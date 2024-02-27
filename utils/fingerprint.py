import hashlib

from pyparsing import CaselessLiteral, Word, alphas, \
    nums, QuotedString, Group, ParserElement, infixNotation, opAssoc, ParseException

from config import logger
from utils.mongo import conn_db

ParserElement.enablePackrat()

# 定义操作符
equals = CaselessLiteral("=")
contains = CaselessLiteral("==")
not_contains = CaselessLiteral("!=")
and_op = CaselessLiteral("&&")
or_op = CaselessLiteral("||")
not_op = CaselessLiteral("!")

# 定义变量和值的语法
variable = Word(alphas + "_")

integer = Word(nums)

escape_char = "\\"
quoted_string = QuotedString('"', escChar=escape_char, unquoteResults=False)

value = quoted_string | integer

# 定义表达式语法
bool_expr = infixNotation(
    Group(variable + equals + value) |
    Group(variable + contains + value) |
    Group(variable + not_contains + value) |
    Group(not_op + variable),
    [
        (not_op, 1, opAssoc.RIGHT),
        (and_op, 2, opAssoc.LEFT),
        (or_op, 2, opAssoc.LEFT),
    ]
)

# 定义操作符
operators = {
    '==': lambda x, y: x == y,
    '!=': lambda x, y: x != y,
    '=': lambda x, y: x in y,
    '!': lambda x: not x,
    '&&': lambda x, y: x and y,
    '||': lambda x, y: x or y
}


# 对双引号包裹的字符串进行 unquote
def unquote_string(s):
    # 去掉引号
    s = s[1:-1]

    # 处理转义字符
    s = s.replace('\\\\', '\\')
    s = s.replace('\\n', '\n')
    s = s.replace('\\t', '\t')
    s = s.replace('\\r', '\r')
    s = s.replace('\\"', '"')

    return s


# 解析表达式
def parse_expression(expression):
    result = bool_expr.parseString(expression, parseAll=True)
    return result.as_list()


#  递归求值
def evaluate_expression(parsed, variables):
    if isinstance(parsed, str):
        if parsed in variables:
            return variables[parsed]
        elif parsed.startswith('"'):
            return unquote_string(parsed)
        else:
            raise ValueError(f"Unknown variable: {parsed}")

    elif len(parsed) == 1:
        return evaluate_expression(parsed[0], variables)
    elif len(parsed) == 2:
        return operators[parsed[0]](evaluate_expression(parsed[1], variables))
    elif len(parsed) == 3:
        return operators[parsed[1]](evaluate_expression(parsed[2], variables),
                                    evaluate_expression(parsed[0], variables))


def evaluate(expression, variables):
    parsed = parse_expression(expression)
    return evaluate_expression(parsed, variables)


def _check_expression(expression):
    variables = {
        'body': "",
        'header': "",
        'title': "",
        'icon_hash': ""
    }
    try:
        return evaluate(expression, variables)
    except ParseException as e:
        raise ValueError(f"Invalid expression: {expression}  exception: {e}")
    except Exception as e:
        raise ValueError(f"Error evaluating expression: {expression} exception: {e}")


def check_expression(expression):
    try:
        _check_expression(expression)
        return True
    except ValueError as e:
        logger.error(e)
        return False


def check_expression_with_error(expression):
    try:
        _check_expression(expression)
        return True, None,
    except ValueError as e:
        return False, e


# 缓存，避免重复解析
parsed_cache = {}


class FingerPrint:
    def __init__(self, app_name: str, human_rule: str):
        self.app_name = app_name
        self.human_rule = human_rule
        self.parsed = None

    def identify(self, variables: dict) -> bool:
        if self.parsed is None:
            self.build_parsed()

        return evaluate_expression(self.parsed, variables)

    def build_parsed(self):
        rule_hash = hashlib.md5(self.human_rule.encode()).hexdigest()
        if rule_hash in parsed_cache:
            self.parsed = parsed_cache[rule_hash]
        else:
            self.parsed = parse_expression(self.human_rule)
            parsed_cache[rule_hash] = self.parsed


def finger_identify(content: bytes, header: str, title: str, favicon_hash: str):
    try:
        content = content.decode("utf-8")
    except UnicodeDecodeError:
        content = content.decode("gbk", "ignore")

    variables = {
        "body": content,
        "header": header,
        "title": title,
        "icon_hash": favicon_hash
    }

    return finger_db_identify(variables)


# 用于缓存指纹数据，避免每次请求都从MongoDB中获取数据
class FingerPrintCache:
    def __init__(self):
        self.cache = None

    def is_cache_valid(self):
        return self.cache is not None

    def get_data(self):
        if self.is_cache_valid():
            return self.cache

        # 如果缓存无效，则重新从MongoDB中获取数据
        self.cache = self.fetch_data_from_mongodb()
        return self.cache

    def fetch_data_from_mongodb(self) -> [FingerPrint]:
        items = list(conn_db('fingerprint').find())
        finger_list = []
        for rule in items:
            finger = FingerPrint(rule['name'], rule['rule'])
            finger_list.append(finger)

        return finger_list

    def update_cache(self):
        # 手动更新缓存
        self.cache = self.fetch_data_from_mongodb()


finger_db_cache = FingerPrintCache()


def finger_db_identify(variables: dict) -> [str]:
    finger_list = finger_db_cache.get_data()
    finger_name_list = []

    for finger in finger_list:
        try:
            if finger.identify(variables):
                finger_name_list.append(finger.app_name)
        except Exception as e:
            logger.warning("error on identify {} {}".format(finger.app_name, e))

    return finger_name_list


def have_human_rule_from_db(rule: str) -> bool:
    query = {
        "human_rule": rule,
    }

    if conn_db('fingerprint').find_one(query):
        return True
    else:
        return False

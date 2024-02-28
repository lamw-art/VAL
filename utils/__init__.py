import subprocess

from utils.mongo import conn_db
from utils.pagehandle import *
from utils.fingerprint import *
from utils.req import Http_Request
from utils.user import *


def check_code_fingerprint(input_data):
    # 定义支持的字段
    supported_fields = ["body", "title", "header", "icon_hash"]
    # 定义支持的操作符
    supported_operators = ["=", "==", "&&", "||", "!"]

    # 构建正则表达式模式
    pattern = re.compile(rf"\b({'|'.join(supported_fields)})\b\s*({', '.join(supported_operators)})\s*\"([^\"]*)\"")

    # 检查输入是否符合规则
    matches = re.findall(pattern, input_data)
    if matches:
        return True
    else:
        return False


def match_subdomains(domain, html, fuzzy=True):
    """
    Use regexp to match subdomains

    :param  str domain: main domain
    :param  str html: response html text
    :param  bool fuzzy: fuzzy match subdomain or not (default True)
    :return set/list: result set or list
    """
    if fuzzy:
        regexp = r'(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.){0,}' \
                 + domain.replace('.', r'\.')
        result = re.findall(regexp, html, re.I)
        if not result:
            return set()
        deal = map(lambda s: s.lower(), result)
        return set(deal)
    else:
        regexp = r'(?:\>|\"|\'|\=|\,)(?:http\:\/\/|https\:\/\/)?' \
                 r'(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.){0,}' \
                 + domain.replace('.', r'\.')
        result = re.findall(regexp, html, re.I)
    if not result:
        return set()
    regexp = r'(?:http://|https://)'
    deal = map(lambda s: re.sub(regexp, '', s[1:].lower()), result)
    return set(deal)


def call_massdns(massdns_path, dict_path, ns_path, output_path, log_path,
                 query_type='A', process_num=1,
                 quiet_mode=True):
    logger.log('INFOR', 'Start running massdns')
    quiet = ''
    if quiet_mode:
        quiet = '--quiet'
    status_format = 'ansi'  # 爆破时状态输出格式（默认asni，可选json）
    concurrent_num = 2000  # 并发查询数量(默认2000，最大推荐10000)
    socket_num = 1  # 爆破时每个进程下的socket数量
    resolve_num = 15  # 解析失败时尝试换名称服务器重查次数
    cmd = f'{massdns_path} {quiet} --status-format {status_format} ' \
          f'--processes {process_num} --socket-count {socket_num} ' \
          f'--hashmap-size {concurrent_num} --resolvers {ns_path} ' \
          f'--resolve-count {resolve_num} --type {query_type} ' \
          f'--flush --output J --outfile {output_path} ' \
          f'--root --error-log {log_path} {dict_path} --filter OK ' \
          f'--sndbuf 0 --rcvbuf 0'
    logger.log('INFOR', f'Run command {cmd}')
    subprocess.run(args=cmd, shell=True)
    logger.log('INFOR', f'Finished massdns')

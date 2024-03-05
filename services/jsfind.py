import asyncio
import random
import re
from urllib.parse import urljoin

import aiohttp
import yaml

from config import logger, settings
from services.crawler import Crawler
from services.service import Service
from utils import get_main_domain


class JsFind(Service):
    def __init__(self, site, urls):
        Service.__init__(self)
        self.task_name = "JSfind"
        self.urls = set(urls)
        self.site = site

        self.visited_urls = set()  # 存储已访问过的链接
        self.main_domain = get_main_domain(self.site)
        self.task_describe = "进行JS敏感信息探测"
        self.rules_path = settings.data_storage_dir.joinpath("js_rules.yml")
        self.rules = {}
        self.matches_result = []
        self.header = settings.request_default_headers
        if settings.enable_random_ua:
            self.header['User-Agent'] = random.choice(settings.user_agents)
        self.proxy = None
        if settings.proxy_enable:
            self.proxy = settings.aiohttp_proxy

    def load_rules(self):
        with open(self.rules_path, 'r') as file:
            rules_data = yaml.safe_load(file)
            enabled_rules = [rule for rule in rules_data.get("rules", []) if rule.get('enabled')]
            for rule in enabled_rules:
                self.rules[rule.get('id')] = re.compile(rule.get("pattern"))
        # 加载域名规则
        self.rules['domain'] = re.compile(r'(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.){0,}' \
                                          + self.main_domain.replace('.', r'\.'))
        # 加载path探测规则
        self.rules['path'] = re.compile(r'(?:/|\.\./|\./)[^"\'><,;| *()(%%$^/\\\[\]][^"\'><,;|()]{1,}'  # 匹配相对路径
                                        r'|[a-zA-Z0-9_\-/]{1,}/[a-zA-Z0-9_\-/]{1,}\.(?:[a-zA-Z]{1,4}|action)(?:['
                                        r'\?|#][^"|\']{0,}|)'  # 匹配带有文件扩展名的相对路径
                                        r'|[a-zA-Z0-9_\-/]{1,}/[a-zA-Z0-9_\-/]{3,}(?:[\?|#][^"| \']{0,}|)'  # 匹配 REST 
                                        # API 风格的路径
                                        r'|[a-zA-Z0-9_\-]{1,}\.(?:php|asp|aspx|jsp|json|action|html|js|txt|xml)(?:['
                                        r'\?|#][^"| \']{0,}|)\)')  # 匹配特定文件类型的路径

    def match_js_rules(self, content, url):
        new_js_urls = set()
        for rule_id, pattern in self.rules.items():
            matches = pattern.findall(content)
            if matches:
                if rule_id == 'path':
                    matches = [urljoin(self.site, path.strip()) for path in matches]
                    js_paths = [path for path in matches if path.endswith('.js')]
                    new_js_urls.update(js_paths)
                for match in matches:
                    result_item = {
                        'content': match,
                        'match_url': url,
                        'rule': rule_id
                    }
                    self.matches_result.append(result_item)
        return new_js_urls
    @staticmethod
    def is_js_path(path):
        # 判断是否为 JS 文件类型的路径，这里简单示范以.js为例
        return path.endswith('.js')

    async def fetch_site_info(self, session, url):
        try:
            if url in self.visited_urls:
                return None
            async with self.semaphore, session.get(url, headers=self.header, proxy=self.proxy) as response:
                self.visited_urls.add(url)
                if response.status != 200:
                    return None
                text = await response.text()
                new_urls = self.match_js_rules(text, url)
                for js_path in new_urls:
                    asyncio.ensure_future(self.fetch_site_info(session, js_path))
                    logger.log("INFO","开启了新任务")
        except Exception as e:
            logger.log("ERROR", str(e))

    async def fetch_all_sites(self):
        timeout = aiohttp.ClientTimeout(total=3600)
        conn = aiohttp.TCPConnector(ssl=settings.request_ssl_verify)
        async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
            tasks = [self.fetch_site_info(session, url) for url in self.urls]
            await asyncio.gather(*tasks)

    def run(self):
        self.begin()
        self.load_rules()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.fetch_all_sites())
        self.finsh()
        return self.matches_result


if __name__ == "__main__":
    req = Crawler('https://business.tenpay.com','js').run()
    js_urls = [i for i in req.get('js_urls')]
    print(js_urls)
    print(len(js_urls))
    res = JsFind('https://business.tenpay.com', js_urls).run()
    print(res)
    print(len(res))

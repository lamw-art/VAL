import asyncio
import json
import random
import subprocess
import simplejson
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

from services.service import Service
from config import settings, logger
from utils import normal_url


class Crawler(Service):
    def __init__(self, site, mode='normal', cookie=None):
        super().__init__()
        self.service_name = "crawlergo"
        self.site = normal_url(site)
        self.cookie = cookie
        self.mode = mode
        self.task_describe = "动态爬虫任务"
        self.crawler_path = settings.Tools_dir.joinpath('crawlergo')
        self.chrome_path = settings.Tools_dir.joinpath('chrome-linux').joinpath('chrome')
        self.req_list = []
        self.sub_domain_list = []
        self.js_urls = set()
        self.crawler_result = {}
        self.header = settings.request_default_headers
        self.semaphore = asyncio.Semaphore(20)
        if settings.enable_random_ua:
            self.header['User-Agent'] = random.choice(settings.user_agents)
        self.proxy = None
        if settings.proxy_enable:
            self.proxy = settings.aiohttp_proxy
        if self.cookie:
            self.header['Cookie'] = self.cookie

    def run_crawler(self):
        cmd = [self.crawler_path, "-c", self.chrome_path, "-o", "json", self.site, "-t", "20", "--robots-path",
               "--custom-headers", simplejson.dumps(self.header)]
        rsp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = rsp.communicate()
        #  "--[Mission Complete]--"  是任务结束的分隔字符串
        result = json.loads(output.decode().split("--[Mission Complete]--")[1])
        self.req_list = [i.get('url') for i in result["req_list"]]
        self.sub_domain_list = result["sub_domain_list"]
        return self.req_list

    async def get_js(self, session, url):
        try:
            async with self.semaphore, session.get(url, headers=self.header, proxy=self.proxy) as response:
                if response.status != 200:
                    return None
                raw_text = await response.text()
                content = BeautifulSoup(raw_text, "html.parser")
                # 查找所有的 script 标签
                script_tags = content.find_all('script')
                # 查找所有的 link 标签中 rel 属性为 modulepreload 的情况
                modulepreload_links = content.find_all('link')
                # 提取 JavaScript 文件链接
                for script_tag in script_tags + modulepreload_links:
                    js_url = script_tag.get('src') or script_tag.get('data-src') or script_tag.get('href')
                    if js_url:
                        js_full_url = urljoin(self.site, js_url)
                        self.js_urls.add(js_full_url)
        except Exception as e:
            logger.log("ERROR", repr(e))
            logger.log("ERROR", f"URL with error: {url}")
            return None

    async def run_get_js(self):
        timeout = aiohttp.ClientTimeout(total=3600)
        conn = aiohttp.TCPConnector(ssl=settings.request_ssl_verify)
        async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
            tasks_get_js = [self.get_js(session, url) for url in self.req_list]
            await asyncio.gather(*tasks_get_js)

    def run(self):
        self.begin()
        self.run_crawler()
        if self.mode == 'js':
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.run_get_js())
        self.js_urls = list(self.js_urls)
        self.js_urls = [path for path in self.js_urls if path.endswith('.js')]
        self.crawler_result = {

            "js_urls": list(self.js_urls),
            "subdomains": self.sub_domain_list,
            "urls": self.req_list
        }
        self.finsh()
        return self.crawler_result


if __name__ == '__main__':
    res = Crawler('https://business.tenpay.com').run()
    print(res)

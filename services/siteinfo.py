import asyncio
import random
from urllib.parse import urlsplit

import aiohttp

from config import settings, logger
from services.service import Service
from services.subfind import SubFind
from utils import get_title, get_headers, fetch_favicon, FingerPrintCache, finger_identify


class SiteInfo(Service):
    def __init__(self, subdomains):
        Service.__init__(self)
        self.service_name = '站点探测'
        self.task_describe = '对搜集的子域名进行站点探测'
        self.subdomains = subdomains
        self.site_list = []
        self.header = settings.request_default_headers
        if settings.enable_random_ua:
            self.header['user-agent'] = random.choice(settings.user_agents)
        self.proxy = None
        if settings.proxy_enable:
            self.proxy = settings.aiohttp_proxy
        self.semaphore = asyncio.Semaphore(20)

    @staticmethod
    def fetch_fingerprint(item, content):
        favicon_hash = item["favicon"].get("hash", 0)
        result_db = finger_identify(content=content, header=item["headers"],
                                    title=item["title"], favicon_hash=str(favicon_hash))

        finger = []
        for name in result_db:
            finger_item = {
                "name": name,
            }
            finger.append(finger_item)

        if finger:
            item["finger"] = finger

    async def fetch_site_info(self, session, url):
        try:
            async with self.semaphore, session.get(url, headers=self.header, proxy=self.proxy) as response:
                body = await response.read()
                final_url = str(response.url)
                normalized_url = urlsplit(final_url)._replace(query='', fragment='').geturl()
                for site_info in self.site_list:
                    if normalized_url in site_info['url']:
                        return None
                item = {
                    'url': normalized_url,
                    'title': get_title(body),
                    'status_code': response.status,
                    'finger': [],
                    "headers": get_headers(response, body),
                    "favicon": fetch_favicon(normalized_url)
                }
            self.fetch_fingerprint(item, content=body)
            # 保存站点信息
            item.pop("headers")
            item.pop("favicon")
            self.site_list.append(item)
        except Exception as e:
            logger.log("ERROR", str(e))

    async def fetch_all_sites(self):
        timeout = aiohttp.ClientTimeout(total=7200)
        conn = aiohttp.TCPConnector(ssl=settings.request_ssl_verify)
        async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
            tasks = [self.fetch_site_info(session, "http://" + url + "/") for url in self.subdomains]
            await asyncio.gather(*tasks)

    def run(self):
        self.begin()
        # 更新数据库缓存
        finger_db_cache = FingerPrintCache()
        finger_db_cache.update_cache()
        # 执行站点信息探测任务
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.fetch_all_sites())
        self.result_describe = f"发现{len(self.site_list)}个站点"
        self.finsh()
        return self.site_list


if __name__ == "__main__":
    subdomain = SubFind("qq.com").run()
    siteinfo = SiteInfo(subdomain)
    results = siteinfo.run()
    print(results)

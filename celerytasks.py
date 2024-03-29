from datetime import datetime

import pymongo
from bson import ObjectId
from celery import Celery
from pymongo import ASCENDING

from services import SubFind, SiteInfo, PortScan, Nuclei, Crawler, JsFind
from utils import conn_db

broker_connection_retry_on_startup = True

custom_celery = Celery(
    "AST",
    broker="redis://127.0.0.1:6379/",
    backend="redis://127.0.0.1:6379/",
)
custom_celery.conf.beat_schedule = {
    'asset_discovery': {
        'task': 'asset_discover',
        'schedule': '',
    },
}


# 资产发现任务
@custom_celery.task(bind=True)
def asset_discovery(self, asset_name, asset_target):
    asset_collection = conn_db("asset")
    asset_info = asset_collection.find_one({"asset_name": asset_name})
    new_subdomains_count = 0  # 初始化新增子域名计数器
    new_sites_count = 0  # 初始化新增站点计数器
    if asset_info:
        asset_target = asset_info["target"]
        asset_id = asset_info["id"]
    else:
        asset = {
            "asset_name": asset_name,
            "target": asset_target,
            "create_time": datetime.now().isoformat(),
            "update_time": "-"
        }
        asset_id = str(asset_collection.insert_one(asset).inserted_id)
        asset_collection.create_index([("asset_name", ASCENDING)], unique=True)
    for domain in asset_target:
        # 执行子域名搜集任务
        subdomains = SubFind(domain).run()
        # 将结果存储再数据库中
        sub_result = []
        for sub in subdomains:
            sub_dict = {"subdomain": sub, "asset_id": asset_id, "domain": domain}
            # 添加到批量操作列表中
            sub_result.append(pymongo.UpdateOne({"subdomain": sub}, {"$set": sub_dict}, upsert=True))
        subdomains_result = conn_db("subdomains").bulk_write(sub_result)
        new_subdomains_count += subdomains_result.upserted_count  # 更新新增子域名计数
        # 执行站点探测任务
        site_info_list = SiteInfo(subdomains).run()
        site_result = []
        for site in site_info_list:
            site["asset_id"] = asset_id
            site_result.append(pymongo.UpdateOne({"url": site["url"]}, {"$set": site}, upsert=True))
        sites_result = conn_db("site").bulk_write(site_result)
        new_sites_count += sites_result.upserted_count  # 更新新增站点计数
    # 更新资产数据库中的 update_time 和新增记录数
    update_time = datetime.now().isoformat()
    asset_collection.update_one(
        {"_id": ObjectId(asset_id)},
        {"$set": {
            "update_time": update_time,
            "new_subdomains_count": new_subdomains_count,  # 记录新增子域名数量
            "new_sites_count": new_sites_count  # 记录新增站点数量
        }}
    )


# 端口扫描任务
@custom_celery.task(bind=True)
def port_scan(self, site, scan_type, site_id):
    port_collection = conn_db("port")
    port_result = PortScan(site, scan_type).run()
    for port in port_result:
        port["site_id"] = site_id
        existing_record = port_collection.find_one({
            'site_id': site_id,
            'port': port['port']
        })
        if not existing_record:
            port_collection.insert_one(port)


# 漏洞扫描任务
@custom_celery.task(bind=True)
def vul_scan(self, site, level, poc_id, tags, site_id):
    vul_collection = conn_db("vul")
    vul_results = Nuclei(site, level, poc_id, tags).run()
    for vul_result in vul_results:
        vul_result["site_id"] = site_id
        existing_record = vul_collection.find_one({
            'site_id': site_id,
            'templateId': vul_result['templateId']
        })
        if not existing_record:
            vul_collection.insert_one(vul_result)


@custom_celery.task(bind=True)
def crawler(self, site_id, url, cookie=None):
    crawler_collection = conn_db("crawler")
    crawler_results = Crawler(url, "normal", cookie).run().get('urls')
    crawler_results = [{"url": temp_url} for temp_url in crawler_results]
    for crawler_result in crawler_results:
        crawler_result["site_id"] = site_id
        existing_record = crawler_collection.find_one({
            'site_id': site_id,
            'url': crawler_result['url']
        })
        if not existing_record:
            crawler_collection.insert_one(crawler_result)


@custom_celery.task(bind=True)
def jsfind(self, site_id, url, cookie=None):
    jsfind_collection = conn_db("jsfind")
    req = Crawler(url, 'js', cookie).run()
    js_urls = [i for i in req.get('js_urls')]
    jsfind_results = JsFind(url, js_urls).run()
    for jsfind_result in jsfind_results:
        jsfind_result["site_id"] = site_id
        existing_record = jsfind_collection.find_one({
            'site_id': site_id,
            'content': jsfind_result['content']
        })
        if not existing_record:
            jsfind_collection.insert_one(jsfind_result)

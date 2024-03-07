from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

import celerytasks
from celerytasks import custom_celery

task_router = APIRouter(tags=["任务管理"])


class asset_TaskParams(BaseModel):
    asset_name: str
    target: str
    timing: str = "0 0 * * 5"


@task_router.post("/task/create_asset")
def create_asset(params: asset_TaskParams):
    params.target = params.target.split(',')
    custom_celery.conf.beat_schedule["asset_discovery"]["schedule"] = params.timing

    # 新建资产任务
    task_result = celerytasks.asset_discovery.delay(
        params.asset_name, params.target
    )
    # 获取任务状态
    task_status = celerytasks.asset_discovery.AsyncResult(task_result.id).status

    # 判断任务状态并返回相应的信息
    if task_status == 'SUCCESS':
        return {
            "code": 200,
            "message": "task created successfully",
            "task_info": {
                "task_id": str(task_result.id),
                "task_name": params.asset_name,
                "created_at": datetime.now().isoformat(),
                "status": "SUCCESS"
            }
        }
    else:
        return {
            "code": 500,
            "message": "task creation failed",
            "task_info": {
                "task_id": str(task_result.id),
                "task_name": params.asset_name,
                "created_at": datetime.now().isoformat(),
                "status": "FAILURE"
            }
        }


# 端口扫描参数
class Port(BaseModel):
    site_id: str
    site: str
    port: str = None
    customPorts: str = None


@task_router.post("/task/portscan")
def port_scan(params: Port):
    if params.customPorts:
        params.port = params.customPorts
    task_result = celerytasks.port_scan.delay(
        params.site, params.port, params.site_id
    )
    # 获取任务状态
    task_status = celerytasks.port_scan.AsyncResult(task_result.id).status

    # 判断任务状态并返回相应的信息
    if task_status == 'SUCCESS':
        return {"code": 200,
                "message": "success start task!"
                }
    else:
        return {"code": 500,
                "message": "failed to start task!"
                }


class VulParams(BaseModel):
    site_id: str
    site: str
    level: str
    poc_id: str = ''
    tags: str = ''


@task_router.post("/task/vulscan")
def vul_scan(params: VulParams):
    task_result = celerytasks.vul_scan.delay(
        params.site, params.level, params.poc_id, params.tags, params.site_id
    )
    # 获取任务状态
    task_status = celerytasks.vul_scan.AsyncResult(task_result.id).status

    # 判断任务状态并返回相应的信息
    if task_status == 'SUCCESS':
        return {"code": 200,
                "message": "success start task!"
                }
    else:
        return {"code": 500,
                "message": "failed to start task!"
                }


class CrawlerParams(BaseModel):
    site_id: str
    url: str
    cookie: str = None


@task_router.post("/task/crawler")
def crawler_scan(params: CrawlerParams):
    task_result = celerytasks.crawler.delay(
        params.site_id, params.url, params.cookie
    )
    # 获取任务状态
    task_status = celerytasks.vul_scan.AsyncResult(task_result.id).status

    # 判断任务状态并返回相应的信息
    if task_status == 'SUCCESS':
        return {"code": 200,
                "message": "success start task!"
                }
    else:
        return {"code": 500,
                "message": "failed to start task!"
                }


class jsfindParams(BaseModel):
    site_id: str
    url: str
    cookie: str = None


@task_router.post("/task/jsfind")
def crawler_scan(params: jsfindParams):
    task_result = celerytasks.jsfind.delay(
        params.site_id, params.url, params.cookie
    )
    # 获取任务状态
    task_status = celerytasks.vul_scan.AsyncResult(task_result.id).status

    # 判断任务状态并返回相应的信息
    if task_status == 'SUCCESS':
        return {"code": 200,
                "message": "success start task!"
                }
    else:
        return {"code": 500,
                "message": "failed to start task!"
                }

from datetime import datetime

from celery.beat import Service
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from celerytask import celery
import celerytask

task_router = APIRouter(tags=["任务管理"])


class asset_TaskParams(BaseModel):
    asset_name: str
    target: str
    timing: str = "0 0 * * 5"


@task_router.post("/task/create_asset")
def create_asset(params: asset_TaskParams, background_tasks: BackgroundTasks):
    params.target = params.target.split(',')
    celery.conf.beat_schedule["asset_discovery"]["schedule"] = params.timing

    # 新建资产任务
    task_result = celerytask.asset_discovery.delay(
        params.asset_name, params.target
    )
    # 打印任务celery id
    background_tasks.add_task(
        print, f"Task ID for {params.asset_name}: {str(task_result.id)}"
    )
    return {
        "code": 200,
        "message": "task created successfully",
        "task_info": {
            "task_id": str(task_result.id),
            "task_name": params.asset_name,
            "created_at": datetime.now().isoformat(),
            "status": "-"
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
    task_result = celerytask.port_scan.delay(
        params.site, params.port, params.site_id
    )
    return {"code": 200,
            "message": "success start task!"
            }


class VulParams(BaseModel):
    site_id: str
    site: str
    level: str
    poc_id: str = ''
    tags: str = ''


@task_router.post("/task/vulscan")
def vul_scan(params: VulParams):
    task_result = celerytask.vul_scan.delay(
        params.site, params.level, params.poc_id, params.tags, params.site_id
    )
    return {"code": 200,
            "message": "success start task!"
            }

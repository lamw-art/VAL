from fastapi import APIRouter
from api.user import user_router
from api.finger import finger_router
from api.poc import poc_router
from api.asset import asset_router
from api.site import site_router
from api.port import port_router
from api.vul import vul_router
from api.tasks import task_router
from api.memo import memo_router
from api.crawler import crawler_router
from api.jsfind import jsfind_router
custom_api = APIRouter(prefix="/api")
custom_api.include_router(user_router)
custom_api.include_router(finger_router)
custom_api.include_router(poc_router)
custom_api.include_router(asset_router)
custom_api.include_router(site_router)
custom_api.include_router(port_router)
custom_api.include_router(vul_router)
custom_api.include_router(task_router)
custom_api.include_router(memo_router)
custom_api.include_router(crawler_router)
custom_api.include_router(jsfind_router)

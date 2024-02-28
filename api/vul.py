from bson import ObjectId
from fastapi import Depends, HTTPException, APIRouter, Query
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from utils import conn_db
from .user import get_current_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
vul_router = APIRouter(tags=["漏洞信息管理"])


class PortInfo(BaseModel):
    id: str = None
    site_id: str


@vul_router.get("/vul/info")
def get_vul_info(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, le=100),
        site_id: str = Query(None, description="Filter by site"),
        severity: str = Query(None, description="Filter by severity"),
        name: str = Query(None, description="Filter by name"),
        templateId: str = Query(default=None, description="Filter by templateId"),
        current_user: dict = Depends(get_current_user)
):
    query = {}
    # 构建查询条件
    if site_id:
        query['site_id'] = site_id
    if severity:
        query['severity'] = severity
    if templateId:
        query['templateId'] = {'$regex': f'.*{templateId}.*', '$options': 'i'}
    if name:
        query['templateId'] = {'$regex': f'.*{name}.*', '$options': 'i'}
    # 获取集合
    collection = conn_db("vul")

    # 一次性查询获取数据和总数量
    total = collection.count_documents(query)

    # 计算跳过的文档数量
    skip_count = (page - 1) * page_size

    # 分页查询
    result = list(collection.find(query).skip(skip_count).limit(page_size))
    for item in result:
        item['_id'] = str(item['_id'])

    # 返回结果，包括总条数
    return JSONResponse({'code': 200, 'data': result, 'total': total})


class DeletePortRequest(BaseModel):
    id: str


@vul_router.post("/vul/delete")
def delete_finger(delete: DeletePortRequest, current_user: dict = Depends(get_current_user)):
    collection = conn_db("vul")
    obj_id = ObjectId(delete.id)
    result = collection.delete_one({"_id": obj_id})

    if result.deleted_count == 1:
        return {"code": 200, "message": "Deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Item not found")

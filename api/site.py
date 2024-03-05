from bson import ObjectId
from fastapi import Depends, HTTPException, APIRouter, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from utils import conn_db
from .user import get_current_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
site_router = APIRouter(tags=["站点管理"])


# 查询资产对应的站点信息
@site_router.get("/site/info")
def get_site_info(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, le=100),
        asset_id: str = None,
        site_id: str = None,
        url: str = Query(None, description="Filter by url"),
        title: str = Query(None, description="Filter by rule"),
        status_code: str = Query(None, description="Filter by status_code"),
        finger: str = Query(None, description="Filter by status_code"),
        current_user: dict = Depends(get_current_user)
):
    query = {}
    # 构建查询条件
    if site_id:
        query["_id"] = ObjectId(site_id)
    if asset_id:
        query['asset_id'] = asset_id  # 使用 asset_id 直接进行查询
    if url:
        # Use a case-insensitive regex for fuzzy name matching
        query['url'] = {'$regex': f'.*{url}.*', '$options': 'i'}
    if title:
        # Use a case-insensitive regex for fuzzy rule matching
        query['title'] = {'$regex': f'.*{title}.*', '$options': 'i'}
    if status_code:
        query['status_code'] = int(status_code)
    if finger:
        # 使用 $elemMatch 匹配 finger 数组中包含指定 name 的文档
        query['finger.name'] = {'$regex': f'.*{finger}.*', '$options': 'i'}

    # 获取集合
    collection = conn_db("site")

    # 一次性查询获取数据和总数量
    total = collection.count_documents(query)

    # 计算跳过的文档数量
    skip_count = (page - 1) * page_size

    # 分页查询
    result = list(collection.find(query).skip(skip_count).limit(page_size))
    for item in result:
        item['_id'] = str(item['_id'])
        item['finger'] = [i['name'] for i in item['finger']]
    # 返回结果，包括总条数
    return JSONResponse({'code': 200, 'data': result, 'total': total})


# 更新站点的参数

class SiteInfo(BaseModel):
    id: str = None
    url: str
    title: str
    asset_id: str
    status_code: int
    finger: str


@site_router.post("/site/update")
def update_site(site_info: SiteInfo,
                current_user: dict = Depends(get_current_user)
                ):
    collection = conn_db("site")
    finger_list = site_info.finger.split(',')
    # 将列表中的每个元素包装成数据库存储格式的对象
    finger = [{"name": finger} for finger in finger_list]
    try:
        if site_info.id:
            obj_id = ObjectId(site_info.id)
            existing = collection.find_one({'_id': obj_id})
            if existing:
                collection.update_one(
                    {"_id": obj_id},
                    {"$set": {"url": site_info.url,
                              "title": site_info.title,
                              "asset_id": site_info.asset_id,
                              "status_code": site_info.status_code,
                              "finger": finger
                              }
                     }
                )
                return JSONResponse({'code': 200, 'message': 'updated successfully'})
            else:
                raise HTTPException(status_code=404, detail='Fingerprint not found')
        else:
            collection.insert_one({"url": site_info.url,
                                   "title": site_info.title,
                                   "asset_id": site_info.asset_id,
                                   "status_code": site_info.status_code,
                                   "finger": finger
                                   })
            return JSONResponse({'code': 200, 'message': 'Document inserted successfully'})
    except RequestValidationError as e:
        # 输出详细错误信息
        error_messages = []
        for error in e.errors():
            error_messages.append({"loc": error["loc"], "msg": error["msg"], "type": error["type"]})
        return JSONResponse(status_code=422, content={"detail": "Validation Error", "errors": error_messages})


class Delete_Id(BaseModel):
    id: str


@site_router.post("/site/delete")
def delete_site(
        delete_id: Delete_Id,
        current_user: dict = Depends(get_current_user)
):
    collection = conn_db("site")
    obj_id = ObjectId(delete_id.id)
    result = collection.delete_one({"_id": obj_id})
    if result.deleted_count == 1:
        return {"code": 200, "message": "Deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Item not found")


@site_router.get("/site/getsite")
def get_site(
        site_id: str
):
    collection = conn_db("site")
    site_id = ObjectId(site_id)
    result = collection.find_one({"_id": site_id})
    url = result.get("url")
    return {
        "code": 200,
        "site": url
    }

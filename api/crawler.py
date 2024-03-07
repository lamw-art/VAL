from bson import ObjectId
from fastapi import Depends, APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils import conn_db
from .user import get_current_user

crawler_router = APIRouter(tags=["动态爬虫管理"])


@crawler_router.get("/crawler/info")
def get_crawler_info(
        site_id: str = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, le=100),
        url: str = None,
        current_user: dict = Depends(get_current_user)
):
    query = {}
    # 构建查询条件
    if site_id:
        query["site_id"] = site_id
    if url:
        query['url'] = {'$regex': f'.*{url}.*', '$options': 'i'}
    # 获取集合
    collection = conn_db("crawler")

    total = collection.count_documents(query)
    skip_count = (page - 1) * page_size

    # 分页查询
    result = list(collection.find(query).skip(skip_count).limit(page_size))
    for item in result:
        item['_id'] = str(item['_id'])

    # 返回结果，包括总条数
    return JSONResponse({'code': 200, 'data': result, 'total': total})


class DeleteParam(BaseModel):
    id: str


@crawler_router.post("/crawler/delete")
def delete_crawler(delete: DeleteParam, current_user: dict = Depends(get_current_user)):
    collection = conn_db("crawler")
    obj_id = ObjectId(delete.id)
    result = collection.delete_one({"_id": obj_id})
    if result.deleted_count == 1:
        return {"code": 200, "message": "Deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Item not found")

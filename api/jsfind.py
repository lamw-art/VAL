from bson import ObjectId
from fastapi import Depends, APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils import conn_db
from .user import get_current_user

jsfind_router = APIRouter(tags=["js敏感信息"])


@jsfind_router.get("/jsfind/info")
def get_crawler_info(
        site_id: str,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, le=100),
        match_url: str = None,
        content: str = None,
        rule: str = None,
        current_user: dict = Depends(get_current_user)
):
    query = {}
    # 构建查询条件
    if site_id:
        query["site_id"] = site_id
    if rule:
        # 如果 rule 存在且不是 "no-path"，则添加路径规则查询条件
        query['rule'] = {'$regex': f'.*{rule}.*', '$options': 'i'}
    if content:
        query['content'] = {'$regex': f'.*{content}.*', '$options': 'i'}
    if match_url:
        query['match_url'] = {'$regex': f'.*{match_url}.*', '$options': 'i'}
    # 获取集合
    collection = conn_db("jsfind")

    total = collection.count_documents(query)
    skip_count = (page - 1) * page_size

    # 分页查询
    result = list(collection.find(query).skip(skip_count).limit(page_size))
    for item in result:
        item['_id'] = str(item['_id'])

    # 返回结果，包括总条数
    return JSONResponse({'code': 200, 'data': result, 'total': total})


@jsfind_router.get("/jsfind/get_rules")
def get_rules(
        site_id: str,
        current_user: dict = Depends(get_current_user)
):
    collection = conn_db("jsfind")

    rules_from_db = collection.find({"site_id": site_id})

    # 使用集合去重
    unique_rules_set = set(rule["rule"] for rule in rules_from_db)

    # 转换为列表
    unique_rules_list = list(unique_rules_set)

    # 返回去重后的规则列表
    return JSONResponse({'code': 200, 'data': unique_rules_list})


class DeleteParam(BaseModel):
    id: str


@jsfind_router.post("/jsfind/delete")
def delete_finger(delete: DeleteParam, current_user: dict = Depends(get_current_user)):
    collection = conn_db("jsfind")
    obj_id = ObjectId(delete.id)
    result = collection.delete_one({"_id": obj_id})
    if result.deleted_count == 1:
        return {"code": 200, "message": "Deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Item not found")

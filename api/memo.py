from bson import ObjectId
from fastapi import Depends, HTTPException, APIRouter, Query, params
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from utils import conn_db, check_expression_with_error
from .user import get_current_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
memo_router = APIRouter(tags=["备忘录"])


@memo_router.get("/memo/info")
def get_finger_info(site_id: str = params.Query(...)):
    if site_id:
        query = {'site_id': site_id}
        memo_collection = conn_db("memo")
        result = list(memo_collection.find(query))
        for item in result:
            item['_id'] = str(item['_id'])
        return JSONResponse({'code': 200, 'data': result})


class Memo(BaseModel):
    site_id: str
    content: str


@memo_router.post("/memo/submit")
def submit_memo(memo: Memo):
    # 要插入或更新的数据
    submit_data = {
        "site_id": memo.site_id,
        "content": memo.content
    }
    # 定义查询条件，这里以一个字段为例
    filter_criteria = {'site_id': memo.site_id}  # 替换为你的查询条件
    collection = conn_db("memo")
    # 使用 update_one 进行插入或更新操作
    result = collection.update_one(
        filter_criteria,
        {'$set': submit_data},
        upsert=True
    )
    return {'code': 200, 'message': 'success'}

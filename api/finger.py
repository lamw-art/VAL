from bson import ObjectId
from fastapi import Depends, HTTPException, APIRouter, Query
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from utils import conn_db, check_expression_with_error
from .user import get_current_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
finger_router = APIRouter(tags=["web指纹管理"])


class FingerInfo(BaseModel):
    id: str = None
    name: str
    rule: str


@finger_router.get("/finger/info")
def get_finger_info(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, le=100),
        name: str = Query(None, description="Filter by name"),
        rule: str = Query(None, description="Filter by rule"),
        current_user: dict = Depends(get_current_user)
):
    query = {}
    # 构建查询条件
    if name:
        # Use a case-insensitive regex for fuzzy name matching
        query['name'] = {'$regex': f'.*{name}.*', '$options': 'i'}
    if rule:
        # Use a case-insensitive regex for fuzzy rule matching
        query['rule'] = {'$regex': f'.*{rule}.*', '$options': 'i'}

    # 获取集合
    collection = conn_db("fingerprint")

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


@finger_router.post("/finger/update")
def update_finger(finger_info: FingerInfo,
                  current_user: dict = Depends(get_current_user)
                  ):
    collection = conn_db("fingerprint")
    try:
        flag, err = check_expression_with_error(finger_info.rule)
        if not flag:
            raise HTTPException(status_code=400, detail="不合法的指纹规则")
        if finger_info.id:
            obj_id = ObjectId(finger_info.id)
            existing_fingerprint = collection.find_one({'_id': obj_id})
            if existing_fingerprint:
                collection.update_one(
                    {"_id": obj_id},
                    {"$set": {"name": finger_info.name, "rule": finger_info.rule}}
                )
                return JSONResponse({'code': 200, 'message': 'success'})
            else:
                raise HTTPException(status_code=404, detail='指纹未发现')
        else:
            collection.insert_one({"name": finger_info.name, "rule": finger_info.rule})
            return JSONResponse({'code': 200, 'message': 'Document inserted successfully'})
    except Exception as e:
        return JSONResponse({'code': 422, 'message': f'Error processing request: {str(e)}'})


class DeleteFingerRequest(BaseModel):
    id: str


@finger_router.post("/finger/delete")
def delete_finger(delete: DeleteFingerRequest, current_user: dict = Depends(get_current_user)):
    collection = conn_db("fingerprint")
    obj_id = ObjectId(delete.id)
    result = collection.delete_one({"_id": obj_id})

    if result.deleted_count == 1:
        return {"code": 200, "message": "Deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="指纹ID未发现")

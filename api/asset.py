from bson import ObjectId
from fastapi import Depends, HTTPException, APIRouter, Query
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from utils import conn_db
from .user import get_current_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
asset_router = APIRouter(tags=["资产管理"])


@asset_router.get("/asset/info")
def get_asset_info(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, le=100),
        asset_name: str = Query(None, description="Filter by name"),
        target: str = Query(None, description="Filter by target"),
        current_user: dict = Depends(get_current_user)
):
    query = {}
    # 构建查询条件
    if asset_name:
        # Use a case-insensitive regex for fuzzy name matching
        query['asset_name'] = {'$regex': f'.*{asset_name}.*', '$options': 'i'}
    if target:
        # Use a case-insensitive regex for fuzzy rule matching
        query['target'] = {'$regex': f'.*{target}.*', '$options': 'i'}

    # 获取集合
    collection = conn_db("asset")

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


class AssetInfo(BaseModel):
    id: str = None
    target: str


@asset_router.post("/asset/update")
def update_asset(asset_info: AssetInfo,
                 current_user: dict = Depends(get_current_user)):
    asset_info.target = asset_info.target.split(',')
    collection = conn_db("asset")
    try:
        if asset_info.id:
            obj_id = ObjectId(asset_info.id)
            existing_fingerprint = collection.find_one({'_id': obj_id})
            if existing_fingerprint:
                collection.update_one(
                    {"_id": obj_id},
                    {"$set": {"target": asset_info.target}}
                )
                return JSONResponse({'code': 200, 'message': 'updated successfully'})
            else:
                raise HTTPException(status_code=404, detail='asset not found')
        else:
            raise HTTPException(status_code=404, detail='asset_id not found')
    except Exception as e:
        return JSONResponse({'code': 422, 'message': f'Error processing request: {str(e)}'})

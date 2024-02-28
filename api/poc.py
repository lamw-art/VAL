from fastapi import Depends, APIRouter, Query
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from utils import conn_db
from .user import get_current_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
poc_router = APIRouter(tags=["POC管理"])


@poc_router.get("/poc/info")
def get_poc_info(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, le=100),
        poc_id: str = Query(None, description="Filter by id"),
        name: str = Query(None, description="Filter by name"),
        tags: str = Query(None, description="Filter by tags"),
        severity: str = Query(None, description="Filter by security"),
        description: str = Query(None, description="Filter by describe"),
        current_user: dict = Depends(get_current_user)
):
    query = {}
    # 构建查询条件
    if name:
        # Use a case-insensitive regex for fuzzy name matching
        query['name'] = {'$regex': f'.*{name}.*', '$options': 'i'}
    if poc_id:
        # Use a case-insensitive regex for fuzzy rule matching
        query['poc_id'] = {'$regex': f'.*{poc_id}.*', '$options': 'i'}
    if tags:
        query['tags'] = {'$regex': f'.*{tags}.*', '$options': 'i'}
    if severity:
        query['severity'] = {'$regex': f'.*{severity}.*', '$options': 'i'}
    if description:
        query['description'] = {'$regex': f'.*{description}.*', '$options': 'i'}

    # 获取集合
    collection = conn_db("POC")

    # 一次性查询获取数据和总数量
    total = collection.count_documents(query)

    # 计算跳过的文档数量
    skip_count = (page - 1) * page_size

    # 分页查询
    result = list(collection.find(query).skip(skip_count).limit(page_size))
    for item in result:
        item['_id'] = str(item['_id'])

    # 返回结果，包括总条数
    return JSONResponse({'code': 200,
                         'data': result,
                         'total': total
                         })

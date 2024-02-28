from fastapi import APIRouter

from api.user import user_router

custom_api = APIRouter(prefix="/api")
custom_api.include_router(user_router)

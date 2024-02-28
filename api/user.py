from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from utils import user_login, conn_db, user_logout, change_pass

user_router = APIRouter(tags=["用户认证管理"])

# 配置 OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")


# 权限认证
def get_current_user(token: str = Depends(oauth2_scheme)):
    user = conn_db('user').find_one({"token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


class LoginParams(BaseModel):
    username: str
    password: str


# 登录接口
@user_router.post("/user/login")
def login(login_params: LoginParams):
    user_data = user_login(username=login_params.username, password=login_params.password)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"code": 200,
            "message": "success",
            "data": {
                "token": user_data["token"],
            }
            }


@user_router.post("/user/logout")
def loginout(current_user: dict = Depends(get_current_user)):
    user_logout(current_user["token"])

    return {
        "code": 200,
        "message": "success"
    }


@user_router.post("/user/change_password")
def change_password(old_password: str, new_password: str, current_user: dict = Depends(get_current_user)):
    if not change_pass(current_user["token"], old_password, new_password):
        return {"code": 0, "message": "error"}
    return {"code": 200, "message": "success"}

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import custom_api

app = FastAPI()
app.include_router(custom_api)
# 配置允许域名
origins = [
    "http://localhost:9527",
    "http://127.0.0.1:9527"
]
# // 配置允许域名列表、允许方法、请求头、cookie等
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    # 运行fastapi程序
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)

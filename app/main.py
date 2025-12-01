# app/main.py
# FastAPI 애플리케이션 초기화 및 라우터 설정


from fastapi import FastAPI
from .routers import posts
from .routers import auth # [추가]
from .services.dynamo_db import create_user_table_if_not_exists # [추가]


app = FastAPI()

# 게시글 라우터 연결
app.include_router(posts.router, prefix="/api/v1/posts", tags=["posts"])

# [추가] 회원관리 라우터
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Health Community API"}


# [CW 추가]
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Health Community API"}
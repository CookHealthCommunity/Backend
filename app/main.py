# app/main.py
# FastAPI 애플리케이션 초기화 및 라우터 설정


from fastapi import FastAPI
from .routers import posts

app = FastAPI()

# 게시글 라우터 연결
app.include_router(posts.router, prefix="/api/v1/posts", tags=["posts"])

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Health Community API"}
# app/main.py
# FastAPI 애플리케이션 진입점 및 설정

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 라우터 임포트 (게시글, 회원, 댓글)
from .routers import posts, auth, comments
from .services.dynamo_db import create_user_table_if_not_exists

# 서버 수명 주기(Lifespan) 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 서버 시작 시: 유저 테이블이 없으면 생성 (온디맨드 모드)
    create_user_table_if_not_exists()
    yield
    # 2. 서버 종료 시: (필요하면 추가 로직 작성)

# FastAPI 앱 초기화
app = FastAPI(
    title="Health Community API",
    description="AWS 프리티어(DynamoDB, S3) 기반 헬스 커뮤니티 백엔드",
    version="1.0.0",
    lifespan=lifespan
)

# ---------------------------------------------------------
#  CORS 설정 (프론트엔드 연결 필수)
# ---------------------------------------------------------
origins = [
    "http://localhost:3000", # React/Vue 로컬 주소
    "http://127.0.0.1:3000",
    "*" # (테스트용) 모든 주소 허용. 실제 배포 시에는 보안을 위해 특정 도메인만 넣는 게 좋음
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 허용할 출처 목록
    allow_credentials=True,     # 쿠키/인증 정보 포함 허용
    allow_methods=["*"],        # 허용할 HTTP 메서드 (GET, POST 등 전체)
    allow_headers=["*"],        # 허용할 HTTP 헤더 (전체)
)

# ---------------------------------------------------------
# 라우터 연결 (Include Routers)
# ---------------------------------------------------------

# 1. 게시글 API (생성, 조회, 상세조회)
app.include_router(posts.router, prefix="/api/v1/posts", tags=["posts"])

# 2. 회원 관리 API (회원가입, 로그인)
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# 3. 댓글 API (게시글 하위 경로)
app.include_router(comments.router, prefix="/api/v1/posts", tags=["comments"])

# ---------------------------------------------------------
# 기본 엔드포인트
# ---------------------------------------------------------
@app.get("/")
def health_check():
    return {"status": "ok", "service": "Health Community API is running"}
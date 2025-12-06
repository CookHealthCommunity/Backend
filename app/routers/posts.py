# app/routers/posts.py

import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, Query
from pydantic import ValidationError

# 모델 임포트
from ..models.post import PostCreate, PostResponse

# S3 서비스 임포트
from ..services.aws_s3 import upload_file_to_s3, delete_file_from_s3

# DynamoDB 서비스 임포트 (모든 로직 포함)
from ..services.dynamo_db import (
    create_post_item, 
    get_posts, 
    get_post_detail, 
    delete_post_item, 
    delete_comments_by_post_id,
    update_post_item,
    search_posts,
    get_posts_by_user  # 👈 [추가] 내가 쓴 글 조회 함수 임포트
)
from .auth import get_current_user 

router = APIRouter()

# ---------------------------------------------------------
# 1. 게시글 생성 API (POST)
# ---------------------------------------------------------
@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED, summary="새 게시글 생성")
async def create_post(
    files: List[UploadFile] = File(None, description="업로드할 이미지 파일"),
    title: str = Form(...),
    content: str = Form(...),
    post_type: str = Form(...),
    current_user: dict = Depends(get_current_user) 
):
    try:
        post_data = PostCreate(title=title, content=content, post_type=post_type)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"입력 데이터 검증 실패: {e.errors()}")
        
    real_user_id = current_user['email']
    new_post_id = str(uuid.uuid4()) 
    uploaded_urls = []
    
    if files:
        for file in files:
            if file.filename: 
                url = await upload_file_to_s3(file, new_post_id)
                if url: uploaded_urls.append(url)
                else: raise HTTPException(status_code=500, detail="파일 업로드 실패")

    post_item_data = {"title": post_data.title, "content": post_data.content, "post_type": post_data.post_type}
    db_item = create_post_item(post_item_data, uploaded_urls, real_user_id, new_post_id)
    
    if not db_item:
        raise HTTPException(status_code=500, detail="DB 저장 실패")

    return db_item

# ---------------------------------------------------------
# 2. 게시글 검색 API (GET /search)
# ---------------------------------------------------------
@router.get("/search", response_model=List[PostResponse], summary="게시글 검색")
def search_community_posts(
    keyword: str = Query(..., min_length=1, description="검색할 키워드 (제목/내용)")
):
    """
    키워드가 제목이나 내용에 포함된 게시글을 검색합니다.
    """
    return search_posts(keyword)

# ---------------------------------------------------------
# 3. 내가 쓴 글 조회 API (GET /me) 
# ---------------------------------------------------------
@router.get("/me", response_model=List[PostResponse], summary="내가 쓴 글 조회")
def read_my_posts(
    current_user: dict = Depends(get_current_user) # 로그인 필수
):
    """
    현재 로그인한 사용자가 작성한 게시글 목록을 반환합니다.
    """
    return get_posts_by_user(current_user['email'])

# ---------------------------------------------------------
# 4. 게시글 목록 조회 API (GET /)
# ---------------------------------------------------------
@router.get("/", response_model=List[PostResponse], summary="게시글 목록 조회")
def read_posts(post_type: str = Query(..., description="게시판 종류")):
    return get_posts(post_type)

# ---------------------------------------------------------
# 5. 게시글 상세 조회 API (GET /{post_id})
# ---------------------------------------------------------
@router.get("/{post_id}", response_model=PostResponse, summary="게시글 상세 조회")
def read_post_detail(post_id: str):
    post = get_post_detail(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return post

# ---------------------------------------------------------
# 6. 게시글 삭제 API (DELETE)
# ---------------------------------------------------------
@router.delete("/{post_id}", status_code=204, summary="게시글 삭제")
def delete_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    post = get_post_detail(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    if post['user_id'] != current_user['email']:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")
        
    # S3 파일 삭제
    if post.get('file_urls'):
        for url in post['file_urls']:
            delete_file_from_s3(url)
    
    # 댓글 데이터 삭제
    delete_comments_by_post_id(post_id)
            
    # 게시글 데이터 삭제
    if not delete_post_item(post_id, current_user['email']):
        raise HTTPException(status_code=500, detail="삭제 중 오류가 발생했습니다.")
        
    return 

# ---------------------------------------------------------
# 7. 게시글 수정 API (PUT)
# ---------------------------------------------------------
@router.put("/{post_id}", response_model=PostResponse, summary="게시글 수정 (사진 포함)")
async def update_post(
    post_id: str,
    files: List[UploadFile] = File(None, description="새로 업로드할 파일 (기존 파일은 삭제됨)"),
    title: str = Form(...),
    content: str = Form(...),
    post_type: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    # 1. 기존 게시글 확인
    old_post = get_post_detail(post_id)
    if not old_post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    if old_post['user_id'] != current_user['email']:
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")

    # 2. 파일 처리 (새 파일이 있는 경우 교체)
    new_file_urls = None 

    if files:
        # 기존 파일 S3 삭제
        if old_post.get('file_urls'):
            for url in old_post['file_urls']:
                delete_file_from_s3(url)
        
        # 새 파일 S3 업로드
        new_file_urls = []
        for file in files:
            if file.filename:
                url = await upload_file_to_s3(file, post_id)
                if url:
                    new_file_urls.append(url)
    
    # 3. DB 업데이트
    updated_post = update_post_item(
        post_id, 
        current_user['email'], 
        title, 
        content,
        post_type,
        new_file_urls
    )
    
    if not updated_post:
        raise HTTPException(status_code=500, detail="게시글 수정 중 오류 발생")
        
    return updated_post
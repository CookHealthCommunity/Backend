# app/routers/posts.py
# 게시글 관련 라우터 정의

import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends # [CW 추가] Depends 추가
from pydantic import ValidationError

from ..models.post import PostCreate, PostResponse
from ..services.aws_s3 import upload_file_to_s3
from ..services.dynamo_db import create_post_item
from .auth import get_current_user # [CW 추가]
router = APIRouter()

@router.post("/", 
             response_model=PostResponse, 
             status_code=status.HTTP_201_CREATED,
             summary="새 게시글 생성 (파일 업로드 포함)")
async def create_post(
    # 파일과 폼 데이터를 동시에 받기 위해 UploadFile 및 Form 사용
    # files: 리스트로 여러 파일 허용, File(...)은 파일을 필수로 받지 않음을 의미
    files: List[UploadFile] = File(None, description="업로드할 이미지 또는 동영상 파일"),
    # Form(...)은 클라이언트가 폼 데이터로 보낸 필드임을 명시
    title: str = Form(...),
    content: str = Form(...),
    post_type: str = Form(...),
    current_user: dict = Depends(get_current_user)  # CW 추가
):
    
    # 1. Pydantic 모델로 폼 데이터 유효성 검사
    try:
        post_data = PostCreate(title=title, content=content, post_type=post_type)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=f"입력 데이터 검증 실패: {e.errors()}"
        )
        
    # **임시 사용자 ID** (로그인 연동 전까지 사용)
    temp_user_id = current_user.get('nickname', 'Unknown') # CW 추가
    #temp_user_id = "SH_Worker" 
    
    # S3와 DynamoDB에 사용할 고유 게시글 ID를 미리 생성합니다.
    new_post_id = str(uuid.uuid4()) 

    # 2. S3 파일 업로드 및 URL 수집
    uploaded_urls = []
    
    if files:
        for file in files:
            # 파일이 비어있지 않은지 확인
            if file.filename: 
                url = await upload_file_to_s3(file, new_post_id)
                if url:
                    uploaded_urls.append(url)
                else:
                    # 파일 업로드 실패 시 클라이언트에게 에러 반환
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                        detail="파일 업로드에 실패했습니다. AWS S3 설정을 확인하세요."
                    )

    # 3. DynamoDB에 게시글 데이터 저장
    post_item_data = {
        "title": post_data.title,
        "content": post_data.content,
        "post_type": post_data.post_type,
    }
    
    db_item = create_post_item(post_item_data, uploaded_urls, temp_user_id, new_post_id)
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="데이터베이스에 게시글을 저장하는 데 실패했습니다."
        )

    # 4. 성공 응답 반환
    return db_item
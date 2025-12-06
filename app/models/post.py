# app/models/post.py
# 게시글 모델 정의 (Pydantic 사용)

from pydantic import BaseModel, Field
from typing import List, Optional

# 1. 게시글 생성 요청 모델
class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str
    # 게시판 타입: 커뮤니티, 식단, 라이브러리 
    post_type: str = Field(pattern="^(커뮤니티|식단|라이브러리)$") 
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "title": "루틴 챌린지 - 데드리프트 마지막 세트",
                "content": "오늘 루틴 공유합니다. 자세 피드백 부탁드려요!",
                "post_type": "커뮤니티"
            }
        }

# 2. 게시글 응답 모델 
class PostResponse(BaseModel):
    post_id: str
    user_id: str
    title: str
    content: str
    post_type: str
    file_urls: List[str] = []
    created_at: str
    
    
    view_count: int = 0
    feedback_count: int = 0

    class Config:
        from_attributes = True

# 3. 게시글 수정 요청 모델
class PostUpdate(BaseModel):
    title : str = Field(min_length=1, max_length=100)
    content : str
    post_type: str = Field(pattern="^(커뮤니티|식단|라이브러리)$")


# app/models/post.py

from pydantic import BaseModel, Field
from typing import List, Optional

# 게시글 생성을 위한 입력 데이터 모델 (Pydantic)
class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str
    # 게시판 타입: 커뮤니티, 식단, 라이브러리 중 하나를 강제합니다.
    post_type: str = Field(pattern="^(커뮤니티|식단|라이브러리)$") 
    
    # 폼 데이터와 함께 오므로 Config 설정을 추가 (FastAPI 공식 문서 참조)
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "title": "루틴 챌린지 - 데드리프트 마지막 세트",
                "content": "오늘 루틴 공유합니다. 자세 피드백 부탁드려요!",
                "post_type": "커뮤니티"
            }
        }

# 응답용 모델 (DB에 저장된 데이터 형식)
class PostResponse(BaseModel):
    post_id: str
    user_id: str
    title: str
    content: str
    post_type: str
    file_urls: List[str]
    created_at: str
    # ... 필요한 다른 필드 추가
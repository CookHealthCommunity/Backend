# app/models/comment.py
from pydantic import BaseModel, Field
from datetime import datetime

# 1. 댓글 작성 요청 (클라이언트가 보내는 데이터)
class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500, description="댓글 내용")

# 2. 댓글 응답 (클라이언트에게 줄 데이터)
class CommentResponse(BaseModel):
    post_id: str
    comment_id: str
    user_id: str
    nickname: str  # 작성자 닉네임
    content: str
    created_at: str

    class Config:
        from_attributes = True
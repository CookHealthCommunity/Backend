# app/routers/comments.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from ..models.comment import CommentCreate, CommentResponse
from ..services.dynamo_db import create_comment, get_comments , delete_comment 
from .auth import get_current_user

router = APIRouter()

# 1. 댓글 작성 API
@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=201)
def write_comment(
    post_id: str,
    comment: CommentCreate,
    current_user: dict = Depends(get_current_user) # 로그인 필수
):
    # 로그인한 유저 정보 가져오기
    user_id = current_user['email']
    nickname = current_user.get('nickname', '익명')

    new_comment = create_comment(post_id, user_id, nickname, comment.content)
    
    if not new_comment:
        raise HTTPException(status_code=500, detail="댓글 저장 실패")
        
    return new_comment

# 2. 댓글 목록 조회 API
@router.get("/{post_id}/comments", response_model=List[CommentResponse])
def read_comments(post_id: str):
    return get_comments(post_id)

# 3. 댓글 삭제 API
@router.delete("/{post_id}/comments/{comment_id}", status_code=204)
def remove_comment(
    post_id: str,
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    # 로그인한 유저의 ID로 삭제 시도
    result = delete_comment(post_id, comment_id, current_user['email'])
    
    if not result:
        # 실패 시 403(권한 없음) 또는 404(못 찾음)를 줄 수 있으나, 보안상 403/400 등으로 통일하기도 함
        raise HTTPException(
            status_code=400, 
            detail="댓글 삭제 실패: 본인의 댓글이 아니거나 이미 삭제되었습니다."
        )
        
    return # 204 No Content
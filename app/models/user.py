# app/models/user.py
from pydantic import BaseModel, Field
from typing import Optional

# 1. 회원가입 요청
class UserCreate(BaseModel):
    email: str
    pw: str
    nickname: str
    secret_key: Optional[str] = None # 관리자 가입용 시크릿 코드

# 2. 로그인 요청
class UserLogin(BaseModel):
    email: str
    pw: str

# 3. 회원 탈퇴 요청
class UserDelete(BaseModel):
    password: str

# 4. 토큰 응답 (로그인 성공 시)
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    message: str

# 5. 내 정보 응답
class UserResponse(BaseModel):
    email: str
    nickname: str
    role: str
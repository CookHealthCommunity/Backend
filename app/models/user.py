from pydantic import BaseModel
from typing import Optional

# 회원가입
class UserCreate(BaseModel):
    email: str
    pw: str
    nickname: str
    secret_key: Optional[str] = None

# 로그인
class UserLogin(BaseModel):
    email: str
    pw: str

# 회원 탈퇴
class UserDelete(BaseModel):
    password: str

# 토큰 응답
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    message: str

# 내 정보 확인
class UserResponse(BaseModel):
    email: str
    nickname: str
    role: str
# app/routers/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import jwt, JWTError
import re

from ..models import user as user_models
from ..services import dynamo_db
from ..config import SECRET_KEY, ALGORITHM, ADMIN_SECRET_CODE

router = APIRouter()

# 비밀번호 암호화 설정 (Argon2 알고리즘 사용)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
security = HTTPBearer()

# --- 내부 함수 (Helper Functions) ---

def verify_password(plain, hashed):
    """입력된 비밀번호와 DB의 해시된 비밀번호 비교"""
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    """비밀번호 암호화"""
    return pwd_context.hash(password)

def create_access_token(data: dict):
    """JWT 토큰 생성"""
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """현재 로그인한 유저 정보 가져오기 (토큰 검증)"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    
    user = dynamo_db.get_user(email)
    if user is None:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    return user

# --- API 엔드포인트 ---

@router.post("/signup", status_code=201, summary="회원가입")
def signup(user: user_models.UserCreate):
    # 이메일 형식 검증
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", user.email):
        raise HTTPException(status_code=400, detail="올바른 이메일 형식이 아닙니다.")
    
    # 비밀번호 암호화 및 역할(Role) 설정
    hashed_pw = get_password_hash(user.pw)
    role = "admin" if user.secret_key == ADMIN_SECRET_CODE else "user"
    
    # DB 저장 시도
    if not dynamo_db.create_user(user.email, hashed_pw, user.nickname, role):
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    
    return {"message": "회원가입이 완료되었습니다."}

@router.post("/login", response_model=user_models.Token, summary="로그인")
def login(user: user_models.UserLogin):
    db_user = dynamo_db.get_user(user.email)
    if not db_user or not verify_password(user.pw, db_user['password']):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")
    
    # 토큰 발행
    token = create_access_token(data={"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": db_user['role'],
        "message": "로그인 성공"
    }

@router.get("/me", response_model=user_models.UserResponse, summary="내 정보 확인")
def read_me(current_user: dict = Depends(get_current_user)):
    return {
        "email": current_user['email'],
        "nickname": current_user['nickname'],
        "role": current_user['role']
    }

@router.delete("/me", summary="회원 탈퇴")
def delete_me(user: user_models.UserDelete, current_user: dict = Depends(get_current_user)):
    if not verify_password(user.password, current_user['password']):
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")
    
    if dynamo_db.delete_user(current_user['email']):
        return {"message": "회원 탈퇴가 완료되었습니다."}
    else:
        raise HTTPException(status_code=500, detail="탈퇴 처리 중 오류가 발생했습니다.")
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import jwt, JWTError
import re

from ..models import user as user_models
from ..services import dynamo_db
from ..config import SECRET_KEY, ALGORITHM, ADMIN_SECRET_CODE

router = APIRouter()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
security = HTTPBearer()

# --- 내부 함수 ---
def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)
def get_password_hash(password): return pwd_context.hash(password)
def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None: raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = dynamo_db.get_user(email)
    if user is None: raise HTTPException(status_code=401, detail="User not found")
    return user

# --- API ---
@router.post("/signup", status_code=201)
def signup(user: user_models.UserCreate):
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", user.email):
        raise HTTPException(status_code=400, detail="이메일 형식이 아닙니다.")
    
    hashed_pw = get_password_hash(user.pw)
    role = "admin" if user.secret_key == ADMIN_SECRET_CODE else "user"
    
    if not dynamo_db.create_user(user.email, hashed_pw, user.nickname, role):
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    return {"message": "회원가입 성공"}

@router.post("/login", response_model=user_models.Token)
def login(user: user_models.UserLogin):
    db_user = dynamo_db.get_user(user.email)
    if not db_user or not verify_password(user.pw, db_user['password']):
        raise HTTPException(status_code=401, detail="이메일/비밀번호 오류")
    
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "role": db_user['role'], "message": "로그인 성공"}

@router.get("/me", response_model=user_models.UserResponse)
def read_me(current_user: dict = Depends(get_current_user)):
    return {"email": current_user['email'], "nickname": current_user['nickname'], "role": current_user['role']}

@router.delete("/me")
def delete_me(user: user_models.UserDelete, current_user: dict = Depends(get_current_user)):
    if not verify_password(user.password, current_user['password']):
        raise HTTPException(status_code=401, detail="비밀번호 불일치")
    dynamo_db.delete_user(current_user['email'])
    return {"message": "탈퇴되었습니다."}
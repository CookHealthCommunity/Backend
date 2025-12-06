# app/config.py
# AWS 자격 증명(Credential) 및 설정 로드

import os
from dotenv import load_dotenv

# 🛠️ .env 파일 로드 활성화
# 프로젝트 루트에 있는 .env 파일에서 AWS 키와 시크릿 키를 읽어옵니다.
load_dotenv() 

# ---------------------------------------------------------
# AWS 설정 (S3 & DynamoDB)
# ---------------------------------------------------------
# .env 파일에 정의된 값이 있으면 그것을 사용하고, 없으면 기본값(두 번째 인자)을 사용합니다.
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "health-project-ccc") 
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2") 

# DynamoDB 테이블 이름 설정
POSTS_TABLE_NAME = "HealthCommunity_Posts"
COMMENTS_TABLE_NAME = "HealthCommunity_Comments"
USERS_TABLE_NAME = "HealthCommunity_Users"  # [추가] 유저 테이블

# ---------------------------------------------------------
# 인증(Auth) 및 보안 설정 [추가됨]
# ---------------------------------------------------------
# JWT 토큰 생성에 사용할 비밀키 (실제 배포 시에는 .env에 설정 권장)
SECRET_KEY = os.getenv("SECRET_KEY", "my_super_secret_key_for_health_app")

# JWT 알고리즘
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# 관리자(admin) 회원가입을 위한 시크릿 코드 (회원가입 시 이 코드를 입력하면 admin 권한 부여)
ADMIN_SECRET_CODE = "health_master"

# ---------------------------------------------------------
# 디버깅용: 로드된 값 확인 (배포 시 삭제 권장)
# ---------------------------------------------------------
print("--------------- DEBUG ---------------")
print(f"✅ LOADED REGION: {AWS_REGION}")
# 보안상 키의 전체를 출력하지 않고 앞 5자리만 확인합니다.
print(f"✅ LOADED ACCESS KEY (Prefix): {os.getenv('AWS_ACCESS_KEY_ID')[:5] if os.getenv('AWS_ACCESS_KEY_ID') else 'None'}")
print("-------------------------------------")
# app/config.py
# AWS 자격 증명(Credential) 및 설정 로드

import os
from dotenv import load_dotenv

# 🛠️ [수정됨] .env 파일 로드 활성화
# 프로젝트 루트에 있는 .env 파일에서 AWS 키를 읽어옵니다.
load_dotenv() 

# AWS 설정
# .env 파일에 정의된 값이 있으면 그것을 사용하고, 없으면 기본값(두 번째 인자)을 사용합니다.
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "health-project-ccc") 
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2") 
POSTS_TABLE_NAME = "HealthCommunity_Posts"
COMMENTS_TABLE_NAME = "HealthCommunity_Comments"

# 디버깅용: 로드된 값 출력 (실제 서비스에서는 민감 정보이므로 출력하지 않도록 주의)
print("--------------- DEBUG ---------------")
print(f"LOADED REGION: {AWS_REGION}")
print(f"LOADED KEY (앞 5자리): {os.getenv('AWS_ACCESS_KEY_ID')[:5] if os.getenv('AWS_ACCESS_KEY_ID') else 'None'}")
print("-------------------------------------")
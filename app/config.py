# app/config.py
# AWS 자격 증명(Credential) 및 설정 로드

import os
from dotenv import load_dotenv

# .env 파일이 있다면 로드 (개발 환경용)
# load_dotenv() 

# AWS 설정
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "health-project-ccc") 
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2") 
POSTS_TABLE_NAME = "HealthCommunity_Posts"
COMMENTS_TABLE_NAME = "HealthCommunity_Comments"
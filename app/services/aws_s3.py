# app/services/aws_s3.py
# AWS S3 관련 서비스 함수들
import os
import uuid
import boto3
from fastapi import UploadFile
from botocore.exceptions import ClientError
from ..config import AWS_REGION, S3_BUCKET_NAME

secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
print(f"DEBUG: Secret Key 길이: {len(secret_key)}") # 👈 이게 40이어야 합니다.
print(f"DEBUG: Secret Key 첫글자: {secret_key[0] if secret_key else 'None'}")
print(f"DEBUG: Secret Key 마지막글자: {secret_key[-1] if secret_key else 'None'}")

s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=secret_key
)


if AWS_REGION:
    SAFE_REGION = AWS_REGION.strip()
else:
    SAFE_REGION = "ap-northeast-2" # 기본값

# S3 클라이언트 초기화 (정제된 SAFE_REGION 사용)
s3_client = boto3.client('s3', region_name=SAFE_REGION)

async def upload_file_to_s3(file: UploadFile, post_id: str) -> str | None:
    """
    FastAPI UploadFile 객체를 받아 S3에 업로드하고 Public URL을 반환합니다.
    """
    try:
        # 파일 확장자 추출 및 고유 파일명 생성
        # 파일명에 점(.)이 없거나 확장자가 없는 경우를 대비해 안전하게 처리
        filename_parts = file.filename.split('.')
        extension = filename_parts[-1] if len(filename_parts) > 1 else 'dat'
        
        unique_filename = f"{uuid.uuid4()}.{extension}"
        file_key = f"posts/{post_id}/{unique_filename}"
        
        # 파일 내용을 비동기적으로 읽어옴
        file_content = await file.read()
        
        # S3에 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            Body=file_content,
            ContentType=file.content_type
            # 🚨 ACL='public-read' 옵션 제거됨 (버킷 소유자 강제 설정 충돌 방지)
            # 파일 공개 권한은 이미 설정한 '버킷 정책'이 처리합니다.
        )
        
        # S3 파일 URL 생성 및 반환 (SAFE_REGION 사용)
        file_url = f"https://{S3_BUCKET_NAME}.s3.{SAFE_REGION}.amazonaws.com/{file_key}"
        return file_url
        
    except ClientError as e:
        # 상세 에러 코드 로깅 (디버깅용)
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', 'Unknown')
        print(f"❌ S3 Upload Client Error: {error_code} - {error_message}")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred during S3 upload: {e}")
        return None
    


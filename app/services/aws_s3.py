# app/services/aws_s3.py
# AWS S3 관련 서비스 함수들 (업로드, 삭제)


import uuid
import boto3
from fastapi import UploadFile
from botocore.exceptions import ClientError
from ..config import AWS_REGION, S3_BUCKET_NAME

# 🛠️ 환경 변수 공백 제거 (Invalid endpoint 에러 방지용)
if AWS_REGION:
    SAFE_REGION = AWS_REGION.strip()
else:
    SAFE_REGION = "ap-northeast-2"

# S3 클라이언트 초기화
s3_client = boto3.client('s3', region_name=SAFE_REGION)

# ---------------------------------------------------------
# 1. 파일 업로드 함수
# ---------------------------------------------------------
async def upload_file_to_s3(file: UploadFile, post_id: str) -> str | None:
    """
    FastAPI UploadFile 객체를 받아 S3에 업로드하고 Public URL을 반환합니다.
    """
    try:
        # 파일 확장자 추출 및 고유 파일명 생성
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
            # ACL 옵션 제거됨 (버킷 정책 사용)
        )
        
        # S3 파일 URL 생성 및 반환
        file_url = f"https://{S3_BUCKET_NAME}.s3.{SAFE_REGION}.amazonaws.com/{file_key}"
        return file_url
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', 'Unknown')
        print(f"❌ S3 Upload Client Error: {error_code} - {error_message}")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred during S3 upload: {e}")
        return None

# ---------------------------------------------------------
# 2. 파일 삭제 함수 (게시글 삭제 시 사용) 
# ---------------------------------------------------------
def delete_file_from_s3(file_url: str):
    """
    S3 URL을 받아 해당 파일을 버킷에서 삭제합니다.
    """
    if not file_url:
        return

    try:
        # URL에서 도메인을 제외한 file_key(경로)만 추출
        # 예: https://.../posts/uuid/file.jpg -> posts/uuid/file.jpg
        file_key = file_url.split('.amazonaws.com/')[-1]
        
        s3_client.delete_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key
        )
        print(f"🗑️ S3 File Deleted: {file_key}")
        
    except ClientError as e:
        print(f"❌ S3 Delete Error: {e}")
    except Exception as e:
        print(f"❌ S3 Delete Unexpected Error: {e}")
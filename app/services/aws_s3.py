# app/services/aws_s3.py
# AWS S3 관련 서비스 함수들
import uuid
import boto3
from fastapi import UploadFile
from botocore.exceptions import ClientError
from ..config import AWS_REGION, S3_BUCKET_NAME

# S3 클라이언트 초기화
s3_client = boto3.client('s3', region_name=AWS_REGION)

async def upload_file_to_s3(file: UploadFile, post_id: str) -> str | None:
    """
    FastAPI UploadFile 객체를 받아 S3에 업로드하고 Public URL을 반환합니다.
    """
    try:
        # 파일 키 (저장 경로) 생성: post_id/고유파일명.확장자
        # UUID를 사용하여 파일명 충돌 방지
        extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        unique_filename = f"{uuid.uuid4()}.{extension}"
        file_key = f"posts/{post_id}/{unique_filename}"
        
        # 파일 내용을 비동기적으로 읽어옴
        file_content = await file.read()
        
        # S3에 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            Body=file_content,
            ContentType=file.content_type,
            # (프리티어이므로 퍼블릭 접근 권한 설정은 생략하고, CDN(CloudFront)을 나중에 붙이는 것을 추천)
            # 일단은 파일 URL을 직접 사용할 수 있도록 공개 설정 (보안에 주의 필요)
            ACL='public-read' 
        )
        
        # S3 파일 URL 생성 및 반환
        file_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file_key}"
        return file_url
        
    except ClientError as e:
        print(f"S3 Upload Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during S3 upload: {e}")
        return None
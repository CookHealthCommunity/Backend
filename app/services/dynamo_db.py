# app/services/dynamo_db.py

import boto3
import time
import uuid
from datetime import datetime
from botocore.exceptions import ClientError
from ..config import AWS_REGION, POSTS_TABLE_NAME

# DynamoDB 리소스 초기화
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
posts_table = dynamodb.Table(POSTS_TABLE_NAME)

def create_post_item(post_data: dict, file_urls: list, user_id: str) -> dict | None:
    """
    게시글 데이터를 DynamoDB에 저장하고 저장된 항목을 반환합니다.
    """
    try:
        # 새로운 게시글 ID 생성
        new_post_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        item = {
            'post_id': new_post_id,
            'post_type': post_data['post_type'],
            'user_id': user_id,  # 로그인 작업자와 연동 후 실제 ID로 대체
            'title': post_data['title'],
            'content': post_data['content'],
            'file_urls': file_urls,  # S3에서 받은 URL 목록
            'view_count': 0,
            'feedback_count': 0,
            'created_at': timestamp,
            'updated_at': timestamp,
        }
        
        # DynamoDB에 항목 저장
        response = posts_table.put_item(Item=item)
        
        # 성공적으로 저장되면 저장된 아이템 반환
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return item
        
    except ClientError as e:
        print(f"DynamoDB Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in DB: {e}")
        return None
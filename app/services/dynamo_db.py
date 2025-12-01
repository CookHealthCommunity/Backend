# app/services/dynamo_db.py

import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from ..config import AWS_REGION, POSTS_TABLE_NAME, COMMENTS_TABLE_NAME

# DynamoDB 리소스 초기화
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

# 테이블 객체 연결
try:
    posts_table = dynamodb.Table(POSTS_TABLE_NAME)
    comments_table = dynamodb.Table(COMMENTS_TABLE_NAME)
except Exception as e:
    print(f"❌ DynamoDB 테이블 연결 오류: {e}")
    posts_table = None
    comments_table = None

# 👇 [수정됨] 인자에 'post_id' 추가 (총 4개)
def create_post_item(post_data: dict, file_urls: list, user_id: str, post_id: str) -> dict | None:
    """
    게시글 데이터를 DynamoDB의 Posts 테이블에 저장합니다.
    """
    if posts_table is None:
        print("DynamoDB 테이블 연결 실패. 저장할 수 없습니다.")
        return None

    try:
        timestamp = datetime.now().isoformat()
        
        # 🚨 중요: 여기서 uuid를 새로 만들지 않고, 인자로 받은 post_id를 그대로 씁니다.
        # (S3에 저장된 폴더명과 DB의 ID를 일치시키기 위함)
        
        item = {
            'post_id': post_id,      # 라우터에서 넘겨받은 ID 사용
            'post_type': post_data['post_type'],
            'user_id': user_id, 
            'title': post_data['title'],
            'content': post_data['content'],
            'file_urls': file_urls,
            'view_count': 0,
            'feedback_count': 0,
            'created_at': timestamp, # GSI 정렬 키
            'updated_at': timestamp,
        }
        
        # DynamoDB에 항목 저장
        response = posts_table.put_item(Item=item)
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return item
        
    except ClientError as e:
        print(f"DynamoDB PutItem Error: {e}")
        return None
    except Exception as e:
        print(f"DB 저장 중 예상치 못한 오류: {e}")
        return None
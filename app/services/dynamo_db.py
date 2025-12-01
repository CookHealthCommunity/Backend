# app/services/dynamo_db.py

import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from ..config import AWS_REGION, POSTS_TABLE_NAME, COMMENTS_TABLE_NAME, USERS_TABLE_NAME




# DynamoDB 리소스 초기화
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

# 테이블 객체 연결
try:
    posts_table = dynamodb.Table(POSTS_TABLE_NAME)
    comments_table = dynamodb.Table(COMMENTS_TABLE_NAME)
    users_table = dynamodb.Table(USERS_TABLE_NAME) # [CW 추가]
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
    
# [CW 추가]

# 1. 유저 테이블 생성 (서버 시작 시 체크)
def create_user_table_if_not_exists():
    try:
        existing_tables = [t.name for t in dynamodb.tables.all()]
        if USERS_TABLE_NAME not in existing_tables:
            print(f"🔨 유저 테이블({USERS_TABLE_NAME}) 생성 중...")
            dynamodb.create_table(
                TableName=USERS_TABLE_NAME,
                KeySchema=[{'AttributeName': 'email', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'email', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
            )
            print("✅ 유저 테이블 생성 완료")
    except Exception as e:
        print(f"❌ 유저 테이블 생성 실패: {e}")

# 2. 회원가입
def create_user(email, password, nickname, role="user"):
    if not users_table: return False
    try:
        users_table.put_item(
            Item={
                'email': email,
                'password': password,
                'nickname': nickname,
                'role': role,
                'created_at': datetime.now().isoformat()
            },
            ConditionExpression='attribute_not_exists(email)'
        )
        return True
    except ClientError:
        return False

# 3. 유저 조회
def get_user(email):
    if not users_table: return None
    try:
        response = users_table.get_item(Key={'email': email})
        return response.get('Item')
    except ClientError:
        return None

# 4. 회원 탈퇴
def delete_user(email):
    if not users_table: return False
    try:
        users_table.delete_item(Key={'email': email})
        return True
    except ClientError:
        return False
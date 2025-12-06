# app/services/dynamo_db.py

import boto3
from datetime import datetime
from botocore.exceptions import ClientError
# 쿼리 조건(Key) 및 검색 조건(Attr) 임포트
from boto3.dynamodb.conditions import Key, Attr
from ..config import AWS_REGION, POSTS_TABLE_NAME, COMMENTS_TABLE_NAME, USERS_TABLE_NAME

# DynamoDB 리소스 초기화
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

# 테이블 객체 연결
try:
    posts_table = dynamodb.Table(POSTS_TABLE_NAME)
    comments_table = dynamodb.Table(COMMENTS_TABLE_NAME)
    users_table = dynamodb.Table(USERS_TABLE_NAME)
    print(f"✅ DynamoDB 테이블 객체 연결 완료")
except Exception as e:
    print(f"❌ DynamoDB 테이블 연결 오류: {e}")
    posts_table = None
    comments_table = None
    users_table = None

# ---------------------------------------------------------
# 1. 게시글 관련 로직 (CRUD + Search + MyPage)
# ---------------------------------------------------------

def create_post_item(post_data: dict, file_urls: list, user_id: str, post_id: str) -> dict | None:
    if posts_table is None: return None
    try:
        timestamp = datetime.now().isoformat()
        item = {
            'post_id': post_id,
            'post_type': post_data['post_type'],
            'user_id': user_id, 
            'title': post_data['title'],
            'content': post_data['content'],
            'file_urls': file_urls,
            'view_count': 0,
            'feedback_count': 0,
            'created_at': timestamp,
            'updated_at': timestamp,
        }
        response = posts_table.put_item(Item=item)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return item
    except ClientError as e:
        print(f"DynamoDB PutItem Error: {e}")
        return None
    except Exception as e:
        print(f"DB Error: {e}")
        return None

def get_posts(post_type: str) -> list:
    if posts_table is None: return []
    try:
        response = posts_table.query(
            IndexName='Type-CreatedAt-Index',
            KeyConditionExpression=Key('post_type').eq(post_type),
            ScanIndexForward=False
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"DynamoDB Query Error: {e}")
        return []

def get_post_detail(post_id: str) -> dict | None:
    if posts_table is None: return None
    try:
        response = posts_table.update_item(
            Key={'post_id': post_id},
            UpdateExpression="SET view_count = view_count + :inc",
            ExpressionAttributeValues={':inc': 1},
            ConditionExpression="attribute_exists(post_id)",
            ReturnValues="ALL_NEW"
        )
        return response.get('Attributes')
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return None
        print(f"DynamoDB Get Detail Error: {e}")
        return None

def delete_post_item(post_id: str, user_id: str) -> bool:
    if posts_table is None: return False
    try:
        posts_table.delete_item(
            Key={'post_id': post_id},
            ConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": user_id}
        )
        return True
    except ClientError as e:
        return False

def update_post_item(post_id: str, user_id: str, title: str, content: str, post_type: str, file_urls: list = None) -> dict | None:
    if posts_table is None: return None
    try:
        timestamp = datetime.now().isoformat()
        
        update_expr = "SET title=:t, content=:c, post_type=:p, updated_at=:u"
        expr_values = {
            ':t': title,
            ':c': content,
            ':p': post_type,
            ':u': timestamp,
            ':uid': user_id
        }

        if file_urls is not None:
            update_expr += ", file_urls=:f"
            expr_values[':f'] = file_urls

        response = posts_table.update_item(
            Key={'post_id': post_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ConditionExpression="user_id = :uid",
            ReturnValues="ALL_NEW"
        )
        return response.get('Attributes')
    except ClientError as e:
        print(f"Update Error: {e}")
        return None

def search_posts(keyword: str) -> list:
    """
    제목(title) 또는 내용(content)에 키워드가 포함된 게시글을 검색합니다.
    """
    if posts_table is None: return []
    try:
        # Scan 사용 (데이터 양이 많지 않을 때 적합)
        response = posts_table.scan(
            FilterExpression=Attr('title').contains(keyword) | Attr('content').contains(keyword)
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"DynamoDB Search Error: {e}")
        return []
    except Exception as e:
        print(f"Search Unexpected Error: {e}")
        return []

#  내가 쓴 글 조회 로직 (MyPage)
def get_posts_by_user(user_id: str) -> list:
    """
    특정 유저(user_id)가 작성한 모든 게시글을 조회하고 최신순으로 정렬합니다.
    """
    if posts_table is None: return []
    try:
        # user_id가 일치하는 데이터만 Scan
        response = posts_table.scan(
            FilterExpression=Attr('user_id').eq(user_id)
        )
        items = response.get('Items', [])
        
        # 가져온 데이터를 created_at 기준 내림차순(최신순) 정렬
        items.sort(key=lambda x: x['created_at'], reverse=True)
        return items
        
    except ClientError as e:
        print(f"My Posts Query Error: {e}")
        return []
    except Exception as e:
        print(f"My Posts Unexpected Error: {e}")
        return []

# ---------------------------------------------------------
# 2. 댓글(Feedback) 관련 로직
# ---------------------------------------------------------

def create_comment(post_id: str, user_id: str, nickname: str, content: str) -> dict | None:
    if comments_table is None or posts_table is None: return None
    try:
        timestamp = datetime.now().isoformat()
        comment_id = f"{timestamp}#{user_id[:5]}"
        item = {
            'post_id': post_id,
            'created_at': comment_id,
            'comment_id': comment_id,
            'user_id': user_id,
            'nickname': nickname,
            'content': content
        }
        comments_table.put_item(Item=item)
        posts_table.update_item(
            Key={'post_id': post_id},
            UpdateExpression="SET feedback_count = feedback_count + :inc",
            ExpressionAttributeValues={':inc': 1}
        )
        return item
    except ClientError as e:
        print(f"❌ Comment Create Error: {e}")
        return None

def get_comments(post_id: str) -> list:
    if comments_table is None: return []
    try:
        response = comments_table.query(
            KeyConditionExpression=Key('post_id').eq(post_id),
            ScanIndexForward=True 
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"❌ Comment Query Error: {e}")
        return []

def delete_comment(post_id: str, comment_id: str, user_id: str) -> bool:
    if comments_table is None or posts_table is None: return False
    try:
        comments_table.delete_item(
            Key={'post_id': post_id, 'created_at': comment_id},
            ConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": user_id}
        )
        posts_table.update_item(
            Key={'post_id': post_id},
            UpdateExpression="SET feedback_count = feedback_count - :dec",
            ExpressionAttributeValues={':dec': 1}
        )
        return True
    except ClientError: return False

def delete_comments_by_post_id(post_id: str):
    if comments_table is None: return
    try:
        response = comments_table.query(KeyConditionExpression=Key('post_id').eq(post_id))
        comments = response.get('Items', [])
        if not comments: return
        with comments_table.batch_writer() as batch:
            for comment in comments:
                batch.delete_item(Key={'post_id': post_id, 'created_at': comment['created_at']})
        print(f"🗑️ 댓글 {len(comments)}개 삭제 완료")
    except Exception: pass

# ---------------------------------------------------------
# 3. 회원 관리(Auth) 관련 로직
# ---------------------------------------------------------

def create_user_table_if_not_exists():
    try:
        existing_tables = [t.name for t in dynamodb.tables.all()]
        if USERS_TABLE_NAME not in existing_tables:
            print(f"🔨 유저 테이블({USERS_TABLE_NAME}) 생성 중...")
            dynamodb.create_table(
                TableName=USERS_TABLE_NAME,
                KeySchema=[{'AttributeName': 'email', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'email', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            print("✅ 유저 테이블 생성 완료")
        else:
            print(f"ℹ 유저 테이블({USERS_TABLE_NAME})이 이미 존재합니다.")
    except Exception as e: print(f"❌ 테이블 생성 실패: {e}")

def create_user(email, password, nickname, role="user"):
    if not users_table: return False
    try:
        users_table.put_item(
            Item={'email': email, 'password': password, 'nickname': nickname, 'role': role, 'created_at': datetime.now().isoformat()},
            ConditionExpression='attribute_not_exists(email)'
        )
        return True
    except ClientError: return False

def get_user(email):
    if not users_table: return None
    try:
        response = users_table.get_item(Key={'email': email})
        return response.get('Item')
    except ClientError: return None

def delete_user(email):
    if not users_table: return False
    try:
        users_table.delete_item(Key={'email': email})
        return True
    except ClientError: return False
# 🏋️ Health Community Backend (Mini-Project)

클라우드 컴퓨팅 수업 미니 프로젝트를 위한 **헬스 커뮤니티 백엔드 API**입니다.
**FastAPI**를 기반으로 하며, **AWS 프리티어(DynamoDB, S3)** 환경에서 동작하도록 구축되었습니다.

---

##  기술 스택 (Tech Stack)

* **Language:** Python 3.8+
* **Framework:** FastAPI
* **Database:** AWS DynamoDB (NoSQL)
* **Storage:** AWS S3 (Image/Video Storage)
* **Libs:** Boto3 (AWS SDK), Pydantic, Uvicorn, python-dotenv

---

##  프로젝트 구조 (Project Structure)

```bash
health-community-backend/
├── app/
│   ├── models/          # Pydantic 데이터 모델 (Request/Response 스키마)
│   ├── routers/         # API 엔드포인트 라우터 (게시글, 댓글 등)
│   ├── services/        # AWS S3 및 DynamoDB 연동 비즈니스 로직
│   ├── config.py        # 환경 변수 및 설정 로드 (.env 처리)
│   └── main.py          # FastAPI 앱 진입점 (Entry Point)
├── .env                 # (필수) 로컬 환경 변수 파일 (Git 포함 X, 각자 생성)
├── .gitignore           # Git 제외 파일 목록
├── requirements.txt     # 의존성 패키지 목록
└── README.md            # 프로젝트 설명서
```

---

## 시작가이드

* **1. 가상환경 활성화**
```bash
# 1. 가상 환경 생성
python -m venv .venv

# 2. 가상 환경 활성화
# Mac/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 3. 필수 패키지 설치
pip install -r requirements.txt
# (requirements.txt가 없다면 아래 명령어 실행)
# pip install fastapi "uvicorn[standard]" boto3 python-multipart python-dotenv
```
* **2. 환경 변수 설정(가장 중요 !!!!)**

```
# .env 파일 내용

# --- AWS 자격 증명 (관리자에게 받은 본인 키 입력) ---
AWS_ACCESS_KEY_ID=여기에_본인_엑세스키_입력
AWS_SECRET_ACCESS_KEY=여기에_본인_시크릿키_입력
AWS_REGION=ap-northeast-2

# --- AWS 리소스 이름 (수정 금지) ---
S3_BUCKET_NAME=health-project-ccc
POSTS_TABLE_NAME=HealthCommunity_Posts
COMMENTS_TABLE_NAME=HealthCommunity_Comments
```

* **3. 서버실행**
```
uvicorn app.main:app --reload
```

---

# api 사용법

* 서버 실행 후 브라우저에서 아래 주소 접속 및 api 문서 테스트
   * API 문서 주소: http://127.0.0.1:8000/docs

* 주요 API: 게시글 생성 (POST /api/v1/posts/)
```
files: 이미지 파일 업로드 (여러 개 가능)

title: 게시글 제목

content: 게시글 내용

post_type: 게시판 종류 (필수: 커뮤니티, 식단, 라이브러리 중 택 1)
```

---

# AWS 리소스 정보

* 프로젝트 리전 :**ap-northeast-2 (서울 리전)**

* 1. DynamoDB Tables
   * HealthCommunity_Posts: 게시글 데이터
     - PK : ```post_id```
     - GSI : ```type-CreatedAt-Index``` (게시판별 목록 조회용)

   * HealthCommunity_Comments: 댓글 데이터

* 2. S3 Bucket
   * health-project-ccc: 이미지 저장소
   * 설정: 버킷 소유자 강제 설정됨 (ACL 미사용), 버킷 정책으로 권한 관리

---

# ⚠️ 트러블슈팅 (FAQ) 
**Q1. SignatureDoesNotMatch 또는 Invalid endpoint 에러가 발생함**

* 원인: .env 파일의 키 값 뒤에 공백이나 줄바꿈이 포함되었거나, 터미널에 이전 환경 변수가 남아있을 가능성    

* 해결:

   1. .env 파일의 값 뒤에 공백이 없는지 확인하세요.

   2. 특수문자가 포함된 시크릿 키는 따옴표 없이 입력하거나, 문제가 계속되면 정확히 복사했는지 확인하세요.

   3. 터미널을 완전히 닫았다가 새로 열어서 uvicorn을 실행하세요. (기존 export 값 초기화)

  
**Q2. 500 Internal Server Error**

* 원인: AWS 자격 증명을 찾지 못했거나, S3 권한이 없는 경우입니다.

* 해결: 본인의 IAM 사용자가 S3 버킷 정책에 추가되어 있는지 관리자에게 확인하세요.
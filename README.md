# Agent of Flutter

ADK(Agent Development Kit) 기반 다중 에이전트 시스템을 활용한 Flutter 애플리케이션 자동 생성 프로젝트입니다.

## 환경 설정

이 프로젝트는 다음 환경 변수를 사용합니다. `.env` 파일을 생성하고 아래 설정을 추가하세요:

```
# ADK 설정
ADK_API_KEY=your_adk_api_key
DEFAULT_MODEL=gemini-1.5-flash

# API 서버 설정
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# 데이터베이스 설정
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flutter_agent

# Redis 설정
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Flutter 프로젝트 설정
FLUTTER_OUTPUT_DIR=./output/flutter_apps
AGENT_ARTIFACTS_DIR=./output/agent_artifacts
FLUTTER_ARCHIVES_DIR=./output/flutter_apps/archives

# 로깅 설정
LOG_LEVEL=INFO
```

## 개요

이 프로젝트는 Google Agent Development Kit(ADK)를 활용하여 정교한 다중 에이전트 시스템을 구축하고, 이를 통해 Flutter 기반 모바일 애플리케이션(Android 및 iOS 지원)을 자동 생성합니다. 각 에이전트는 단일 코드 파일을 생성하도록 책임을 할당받으며, 이러한 에이전트들은 기능별 그룹(웹뷰, API, 모델, 컨트롤러, TDD, 보안)으로 조직화됩니다.

## 주요 기능

- "하나의 에이전트, 하나의 파일" 원칙으로 모듈화된 구조
- ADK의 FunctionTool과 ArtifactService를 활용한 코드 생성 및 파일 관리
- FastAPI를 통한 외부 API 호출 처리
- PostgreSQL, Redis, Nginx 기술 스택 지원
- TDD 및 보안 자동화 기능

## 시스템 구성

프로젝트는 다음과 같은 에이전트 그룹으로 구성되어 있습니다:

1. **모델 그룹**: 데이터 모델 클래스 파일 생성
2. **API 그룹**: API 엔드포인트 및 라우트 파일 생성
3. **컨트롤러 그룹**: 비즈니스 로직 컨트롤러 파일 생성
4. **웹뷰 그룹**: UI 위젯 및 페이지 파일 생성
5. **TDD 그룹**: 자동화된 테스트 케이스 파일 생성
6. **보안 그룹**: 코드 정적 분석 및 보안 취약점 검사

각 그룹 내 에이전트들은 "하나의 에이전트, 하나의 파일" 원칙에 따라 단일 파일 생성을 담당합니다.

### 출력 디렉토리 구조

프로젝트 실행 결과물은 다음과 같은 디렉토리 구조로 관리됩니다:

```
output/
│
├── flutter_apps/         # 생성된 Flutter 앱 파일
│   ├── <app_name>/       # 개별 앱 디렉토리 (앱 이름별)
│   └── archives/         # ZIP 형태로 아카이빙된 앱 파일
│
└── agent_artifacts/      # 에이전트 작업 중간 결과물
    ├── sessions/         # 에이전트 세션 정보
    └── job_states/       # 작업 상태 정보
```

## 시작하기

### 요구사항

- Python 3.10 이상
- Google ADK
- Flutter SDK
- Docker (선택사항)

### 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/agentofflutter.git
cd agentofflutter

# 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 실행

API 서버 시작:

```bash
python main.py --server
```

기본적으로 서버는 http://0.0.0.0:8000 에서 접근 가능합니다.

### API 사용

아래는 새 Flutter 앱 생성 API 호출 예시입니다:

```bash
curl -X POST http://localhost:8000/generate_app \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "my_flutter_app",
    "description": "A sample Flutter application",
    "models": [
      {
        "name": "User",
        "fields": [
          {"name": "id", "type": "String"},
          {"name": "name", "type": "String"},
          {"name": "email", "type": "String"},
          {"name": "createdAt", "type": "DateTime"}
        ]
      }
    ],
    "pages": ["HomePage", "LoginPage", "ProfilePage"]
  }'
```

## API 엔드포인트 참조

### 루트 엔드포인트

API 정보와 사용 가능한 모든 엔드포인트를 조회합니다.

**요청**:
```bash
curl -X GET http://localhost:8000/
```

**응답**:
```json
{
  "name": "Agent of Flutter API",
  "version": "1.0.0",
  "description": "ADK 기반 Flutter 앱 생성 API",
  "endpoints": [
    {
      "path": "/generate_app",
      "method": "POST",
      "description": "Flutter 앱 생성 요청"
    },
    {
      "path": "/job/{job_id}",
      "method": "GET",
      "description": "특정 작업 상태 조회"
    },
    {
      "path": "/jobs",
      "method": "GET",
      "description": "모든 작업 상태 조회"
    },
    {
      "path": "/download/{job_id}/{artifact_name}",
      "method": "GET",
      "description": "특정 아티팩트 다운로드"
    },
    {
      "path": "/download_zip/{job_id}",
      "method": "GET",
      "description": "모든 아티팩트를 ZIP으로 다운로드"
    },
    {
      "path": "/status",
      "method": "GET",
      "description": "서버 상태 조회"
    }
  ]
}
```

### Flutter 앱 생성

새로운 Flutter 앱 생성 요청을 처리합니다.

**요청**:
```bash
curl -X POST http://localhost:8000/generate_app \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "shopping_app",
    "description": "쇼핑몰 모바일 애플리케이션",
    "models": [
      {
        "name": "Product",
        "fields": [
          {"name": "id", "type": "String"},
          {"name": "name", "type": "String"},
          {"name": "price", "type": "double"},
          {"name": "description", "type": "String"},
          {"name": "imageUrl", "type": "String"},
          {"name": "category", "type": "String"},
          {"name": "createdAt", "type": "DateTime"}
        ]
      },
      {
        "name": "Cart",
        "fields": [
          {"name": "id", "type": "String"},
          {"name": "userId", "type": "String"},
          {"name": "products", "type": "List<CartItem>"},
          {"name": "totalPrice", "type": "double"},
          {"name": "updatedAt", "type": "DateTime"}
        ]
      },
      {
        "name": "CartItem",
        "fields": [
          {"name": "productId", "type": "String"},
          {"name": "quantity", "type": "int"},
          {"name": "price", "type": "double"}
        ]
      }
    ],
    "pages": ["HomePage", "ProductDetailPage", "CartPage", "ProfilePage", "CategoryPage"],
    "features": ["다크 모드", "상품 검색", "카테고리 필터링", "장바구니 기능"]
  }'
```

**응답**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0,
  "message": "작업 초기화 중...",
  "artifacts": []
}
```

### 작업 상태 조회

특정 작업의 현재 상태를 조회합니다.

**요청**:
```bash
curl -X GET http://localhost:8000/job/550e8400-e29b-41d4-a716-446655440000
```

**응답**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "message": "앱 생성 완료",
  "artifacts": [
    "models/product.dart",
    "models/cart.dart",
    "models/cart_item.dart",
    "pages/home_page.dart",
    "pages/product_detail_page.dart",
    "pages/cart_page.dart",
    "pages/profile_page.dart",
    "pages/category_page.dart",
    "main.dart"
  ]
}
```

### 모든 작업 상태 조회

모든 작업의 상태를 조회합니다.

**요청**:
```bash
curl -X GET http://localhost:8000/jobs
```

**응답**:
```json
{
  "550e8400-e29b-41d4-a716-446655440000": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "progress": 100,
    "message": "앱 생성 완료",
    "artifacts": [
      "models/product.dart",
      "models/cart.dart",
      "models/cart_item.dart",
      "pages/home_page.dart",
      "pages/product_detail_page.dart",
      "pages/cart_page.dart",
      "pages/profile_page.dart",
      "pages/category_page.dart",
      "main.dart"
    ]
  },
  "550e8400-e29b-41d4-a716-446655440001": {
    "job_id": "550e8400-e29b-41d4-a716-446655440001",
    "status": "running",
    "progress": 65,
    "message": "위젯 파일 생성 중...",
    "artifacts": []
  }
}
```

### 아티팩트 다운로드

특정 작업에서 생성된 아티팩트 파일을 다운로드합니다.

**요청**:
```bash
curl -X GET http://localhost:8000/download/550e8400-e29b-41d4-a716-446655440000/models/product.dart -o product.dart
```

**응답**: 파일 내용이 직접 반환됩니다.

### ZIP 파일 다운로드

특정 작업에서 생성된 모든 아티팩트를 ZIP 파일로 다운로드합니다.

**요청**:
```bash
curl -X GET http://localhost:8000/download_zip/550e8400-e29b-41d4-a716-446655440000 -o shopping_app.zip
```

**응답**: ZIP 파일이 직접 반환됩니다.

### 서버 상태 조회

서버의 현재 상태를 조회합니다.

**요청**:
```bash
curl -X GET http://localhost:8000/status
```

**응답**:
```json
{
  "status": "running",
  "version": "1.0.0",
  "active_jobs": 1,
  "completed_jobs": 1,
  "failed_jobs": 0,
  "uptime": "1:23:45.678901"
}
```

## 프로젝트 구조

```
agentofflutter/
├── src/
│   ├── agents/             # 모든 에이전트 코드
│   │   ├── api_group/      # API 파일 생성 에이전트
│   │   ├── model_group/    # 모델 파일 생성 에이전트
│   │   ├── controller_group/ # 컨트롤러 파일 생성 에이전트
│   │   ├── webview_group/  # UI 위젯 파일 생성 에이전트
│   │   ├── tdd_group/      # 테스트 파일 생성 에이전트
│   │   └── security_group/ # 보안 검사 에이전트
│   ├── api/                # FastAPI 서버 구현
│   ├── tools/              # 에이전트 도구(FunctionTool) 구현
│   ├── templates/          # Jinja2 템플릿 파일
│   ├── utils/              # 유틸리티 함수
│   └── config/             # 설정 파일
├── tests/                  # 테스트 코드
├── main.py                 # 메인 실행 스크립트
└── requirements.txt        # 의존성 패키지 목록
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
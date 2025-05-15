# Agent of Flutter

ADK(Agent Development Kit) 기반 다중 에이전트 시스템을 활용한 Flutter 애플리케이션 자동 생성 프로젝트입니다.

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
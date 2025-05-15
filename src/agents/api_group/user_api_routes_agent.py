"""
UserAPIRoutesAgent: 사용자 API 라우트 파일을 생성하는 에이전트.

이 에이전트는 사용자 CRUD 작업을 위한 FastAPI 라우트 파일을 생성합니다.
"""
from google.adk.agents import LlmAgent

from src.config.settings import get_agent_config
from src.tools.code_generation import (
    generate_python_file_tool,
    direct_code_generation_tool
)


# 사용자 API 라우트 에이전트 정의
user_api_routes_agent = LlmAgent(
    name="UserAPIRoutesAgent",
    description="사용자 API 라우트 파일을 생성하는 에이전트",
    instruction="""
    당신은 사용자 관련 API 엔드포인트를 생성하는 FastAPI 전문가입니다.

    사용자 관리를 위한 CRUD(Create, Read, Update, Delete) 작업을 처리하는
    FastAPI 라우트 파일을 생성해야 합니다.

    이 파일은 다음 기능을 포함해야 합니다:

    1. 사용자 생성 엔드포인트 (/users/, POST)
    2. 전체 사용자 목록 조회 엔드포인트 (/users/, GET)
    3. 특정 사용자 조회 엔드포인트 (/users/{user_id}, GET)
    4. 사용자 정보 수정 엔드포인트 (/users/{user_id}, PUT)
    5. 사용자 삭제 엔드포인트 (/users/{user_id}, DELETE)

    모든 엔드포인트는 적절한 Pydantic 모델을 요청/응답 스키마로 사용해야 합니다.
    PostgreSQL 데이터베이스를 사용하며, SQLAlchemy ORM을 통해 데이터에 접근해야 합니다.

    코드는 가독성이 좋고 모범적인 FastAPI 패턴을 따라야 합니다.
    """,
    model=get_agent_config("model_agent")["model"],
    tools=[generate_python_file_tool, direct_code_generation_tool],
)


def create_default_user_api_routes(tool_context) -> None:
    """
    기본 사용자 API 라우트를 생성합니다.

    Args:
        tool_context: 도구 컨텍스트

    Returns:
        없음
    """
    # 기본 사용자 API 라우트 템플릿 컨텍스트
    user_api_context = {
        "router_name": "users",
        "endpoints": [
            {
                "path": "/users/",
                "method": "POST",
                "summary": "Create new user",
                "response_model": "User"
            },
            {
                "path": "/users/",
                "method": "GET",
                "summary": "Get all users",
                "response_model": "List[User]"
            },
            {
                "path": "/users/{user_id}",
                "method": "GET",
                "summary": "Get user by ID",
                "response_model": "User"
            },
            {
                "path": "/users/{user_id}",
                "method": "PUT",
                "summary": "Update user",
                "response_model": "User"
            },
            {
                "path": "/users/{user_id}",
                "method": "DELETE",
                "summary": "Delete user",
                "response_model": "Dict"
            }
        ],
        "dependencies": [
            "fastapi",
            "sqlalchemy",
            "pydantic"
        ]
    }

    # 파일 생성 (템플릿 기반)
    generate_python_file_tool(
        template_name="fastapi_routes.py.j2",
        output_filename="app/api/routes/user_routes.py",
        context=user_api_context,
        tool_context=tool_context
    )
"""
UserControllerAgent: 사용자 컨트롤러 파일을 생성하는 에이전트.

이 에이전트는 Flutter 애플리케이션에서 사용자 정보를 관리하는 컨트롤러 파일을 생성합니다.
"""
from google.adk.agents import LlmAgent

from src.config.settings import get_agent_config
from src.tools.code_generation import (
    generate_dart_file_tool,
    direct_code_generation_tool
)


# 사용자 컨트롤러 에이전트 정의
user_controller_agent = LlmAgent(
    name="UserControllerAgent",
    description="사용자 컨트롤러 파일을 생성하는 에이전트",
    instruction="""
    당신은 Flutter 애플리케이션을 위한 사용자 컨트롤러를 생성하는 전문가입니다.

    Flutter 애플리케이션에서 사용자 정보를 관리하는 컨트롤러 클래스 파일을 생성해야 합니다.
    이 컨트롤러는 다음 기능을 포함해야 합니다:

    1. User 모델 클래스를 사용한 상태 관리
    2. 사용자 정보 로드, 업데이트, 저장 메서드
    3. 인증 상태 관리 (로그인/로그아웃)
    4. Provider나 다른 상태 관리 라이브러리와 통합
    5. API 호출과 결과 처리

    컨트롤러는 UI와 데이터 레이어 사이의 중간 역할을 하며,
    앱 내에서 사용자 관련 비즈니스 로직을 처리합니다.

    이전에 생성된 User 모델과 API 엔드포인트 정보를 활용하여
    일관된 코드를 작성해야 합니다.
    """,
    model=get_agent_config("model_agent")["model"],
    tools=[generate_dart_file_tool, direct_code_generation_tool],
)


def create_default_user_controller(tool_context) -> None:
    """
    기본 사용자 컨트롤러를 생성합니다.

    Args:
        tool_context: 도구 컨텍스트

    Returns:
        없음
    """
    # 기본 사용자 컨트롤러 템플릿 컨텍스트
    user_controller_context = {
        "controller_name": "UserController",
        "uses_model": True,
        "model_name": "User",
        "state_management": "provider",
        "features": [
            "login",
            "logout",
            "getUserInfo",
            "updateUserInfo"
        ],
        "dependencies": [
            "flutter",
            "models/user_model.dart",
            "package:provider/provider.dart",
            "package:http/http.dart"
        ]
    }

    # 파일 생성 (템플릿 기반)
    generate_dart_file_tool(
        template_name="controller.dart.j2",
        output_filename="lib/controllers/user_controller.dart",
        context=user_controller_context,
        tool_context=tool_context
    )

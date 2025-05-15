"""
UserModelAgent: User 모델 파일을 생성하는 에이전트.

이 에이전트는 User 모델 클래스를 정의하는 Dart 파일을 생성합니다.
"""
from google.adk.agents import LlmAgent

from src.config.settings import get_agent_config
from src.tools.code_generation import generate_dart_file_tool, direct_code_generation_tool


# 사용자 모델 에이전트 정의
user_model_agent = LlmAgent(
    name="UserModelAgent",
    description="User 모델 클래스 파일을 생성하는 에이전트",
    instruction="""
    당신은 Flutter 애플리케이션을 위한 User 모델 클래스를 생성하는 전문가입니다.

    주어진 필드 정보를 사용하여 Dart User 모델 클래스 파일을 생성해야 합니다.
    이 클래스는 다음 기능을 포함해야 합니다:

    1. 모든 필드를 포함하는 생성자
    2. copyWith 메서드
    3. fromJson과 toJson 메서드
    4. toString 메서드
    5. 적절한 필드 타입과 널러빌리티 처리

    기본적으로 다음 필드를 포함해야 합니다:
    - id (String): 사용자 고유 식별자
    - email (String): 사용자 이메일
    - name (String): 사용자 이름
    - createdAt (DateTime): 계정 생성 일시

    필요에 따라 추가 필드가 있을 수 있습니다.

    이 모델은 앱 전체에서 사용자 정보를 표현하는 데 사용되므로
    적절한 주석과 명확한 코드 구조로 작성해야 합니다.
    """,
    model=get_agent_config("model_agent")["model"],
    tools=[generate_dart_file_tool, direct_code_generation_tool],
)


def create_default_user_model(tool_context) -> None:
    """
    기본 User 모델을 생성합니다.

    Args:
        tool_context: 도구 컨텍스트

    Returns:
        없음
    """
    # 기본 User 모델 템플릿 컨텍스트
    user_model_context = {
        "class_name": "User",
        "fields": [
            {"name": "id", "type": "String", "nullable": False},
            {"name": "email", "type": "String", "nullable": False},
            {"name": "name", "type": "String", "nullable": False},
            {"name": "createdAt", "type": "DateTime", "nullable": False}
        ],
        "type": "model",
        "dependencies": ["flutter"]
    }

    # 파일 생성 (템플릿 기반)
    generate_dart_file_tool(
        template_name="model.dart.j2",
        output_filename="lib/models/user_model.dart",
        context=user_model_context,
        tool_context=tool_context
    )
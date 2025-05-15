"""
HomePageViewAgent: 홈 페이지 위젯 파일을 생성하는 에이전트.

이 에이전트는 애플리케이션의 홈 페이지 위젯을 정의하는 Dart 파일을 생성합니다.
"""
from google.adk.agents import LlmAgent

from src.config.settings import get_agent_config
from src.tools.code_generation import (
    generate_dart_file_tool,
    direct_code_generation_tool
)


# 홈 페이지 뷰 에이전트 정의
home_page_view_agent = LlmAgent(
    name="HomePageViewAgent",
    description="홈 페이지 위젯 파일을 생성하는 에이전트",
    instruction="""
    당신은 Flutter 애플리케이션을 위한 홈 페이지 위젯을 생성하는 전문가입니다.

    애플리케이션의 홈 페이지 화면을 정의하는 Dart 파일을 생성해야 합니다.
    이 위젯은 다음 기능을 포함해야 합니다:

    1. StatefulWidget 또는 StatelessWidget 클래스 구현
    2. 적절한 레이아웃 구성 (Column, Row, ListView 등 활용)
    3. 사용자 정보 표시 (User 모델 클래스 사용)
    4. 앱 내 메인 기능으로 이동할 수 있는 네비게이션
    5. 앱에 필요한 UI 요소들 (버튼, 카드 등)

    홈 페이지는 사용자가 앱에서 가장 먼저 보는 화면이므로
    직관적이고 깔끔한 UI를 갖추어야 합니다.

    이전에 생성된 User 모델을 적절히 참조하고 활용하세요.
    세션 상태에 저장된 generated_models 목록을 확인하여
    기존에 생성된 모델 정보를 파악할 수 있습니다.
    """,
    model=get_agent_config("webview_agent")["model"],
    tools=[generate_dart_file_tool, direct_code_generation_tool],
)


def create_default_home_page(tool_context) -> None:
    """
    기본 홈 페이지 위젯을 생성합니다.

    Args:
        tool_context: 도구 컨텍스트

    Returns:
        없음
    """
    # 기본 홈 페이지 템플릿 컨텍스트
    home_page_context = {
        "widget_name": "HomePage",
        "widget_type": "StatefulWidget",
        "uses_model": True,
        "model_name": "User",
        "dependencies": [
            "flutter",
            "models/user_model.dart",
            "package:provider/provider.dart"
        ]
    }

    # 파일 생성 (템플릿 기반)
    generate_dart_file_tool(
        template_name="page_view.dart.j2",
        output_filename="lib/pages/home_page.dart",
        context=home_page_context,
        tool_context=tool_context
    )
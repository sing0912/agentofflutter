"""
ModelTestCaseAgent: 모델 클래스 테스트 파일을 생성하는 에이전트.

이 에이전트는 모델 클래스에 대한 단위 테스트 케이스 파일을 생성합니다.
"""
from google.adk.agents import LlmAgent

from src.config.settings import get_agent_config
from src.tools.code_generation import (
    generate_dart_file_tool,
    direct_code_generation_tool
)


# 모델 테스트 케이스 에이전트 정의
model_test_case_agent = LlmAgent(
    name="ModelTestCaseAgent",
    description="모델 클래스 테스트 파일을 생성하는 에이전트",
    instruction="""
    당신은 Flutter 앱의 모델 클래스를 위한 테스트 케이스를 작성하는 전문가입니다.

    모델 클래스에 대한 단위 테스트 파일을 생성해야 합니다.
    테스트 케이스는 다음을 확인해야 합니다:

    1. 생성자가 올바르게 작동하는지
    2. fromJson 메서드가 정확히 역직렬화하는지
    3. toJson 메서드가 정확히 직렬화하는지
    4. copyWith 메서드가 올바르게 필드 값을 업데이트하는지
    5. equality(==) 연산자가 올바르게 동작하는지

    각 테스트는 명확하고 구체적인 입력값과 예상 결과값을 포함해야 합니다.
    Flutter 표준 테스트 라이브러리(flutter_test)를 사용해야 하며,
    테스트 그룹을 활용하여 논리적으로 테스트를 구성해야 합니다.

    이전에 생성된 모델 클래스의 모든 필드와 메서드를 테스트해야 합니다.
    세션 상태에 저장된 generated_models 목록을 확인하여
    기존에 생성된 모델 정보를 파악할 수 있습니다.
    """,
    model=get_agent_config("tdd_agent")["model"],
    tools=[generate_dart_file_tool, direct_code_generation_tool],
)


def create_model_test_case(model_info, tool_context) -> None:
    """
    지정된 모델에 대한 테스트 케이스를 생성합니다.

    Args:
        model_info: 모델 정보 딕셔너리
        tool_context: 도구 컨텍스트

    Returns:
        없음
    """
    # 테스트 케이스 템플릿 컨텍스트
    test_context = {
        "test_name": f"{model_info['name']}Test",
        "model_name": model_info["name"],
        "model_file": model_info["file"],
        "fields": model_info["fields"],
        "dependencies": [
            "flutter_test",
            model_info["file"]
        ]
    }

    # 파일 생성 (템플릿 기반)
    output_filename = f"test/{
        model_info['file'].replace(
            'lib/',
            '').replace(
            '.dart',
            '')}_test.dart"

    generate_dart_file_tool(
        template_name="model_test.dart.j2",
        output_filename=output_filename,
        context=test_context,
        tool_context=tool_context
    )


def generate_model_tests(tool_context) -> None:
    """
    생성된 모든 모델에 대한 테스트 케이스를 생성합니다.

    Args:
        tool_context: 도구 컨텍스트

    Returns:
        없음
    """
    # 세션 상태에서 생성된 모델 정보 가져오기
    generated_models = tool_context.state.get("generated_models", [])

    if not generated_models:
        return

    # 각 모델에 대해 테스트 케이스 생성
    for model_info in generated_models:
        create_model_test_case(model_info, tool_context)

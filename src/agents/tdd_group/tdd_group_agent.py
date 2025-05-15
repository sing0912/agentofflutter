"""
TDDGroupAgent: 테스트 케이스 생성을 조정하는 그룹 에이전트.

이 에이전트는 여러 테스트 케이스 생성 에이전트의 실행을 조정합니다.
"""
from google.adk.agents import SequentialAgent

from src.agents.tdd_group.model_test_case_agent import model_test_case_agent
from src.utils.logger import logger


# TDD 그룹 에이전트 정의
tdd_group_agent = SequentialAgent(
    name="TDDGroupAgent",
    description="테스트 케이스 생성 작업을 순차적으로 수행하는 에이전트 그룹",
    sub_agents=[
        model_test_case_agent,
        # widget_test_case_agent와 같은 다른 테스트 케이스 에이전트를 추가
    ]
)


def register_tdd_agents(app_spec):
    """
    앱 명세에 따라 필요한 TDD 에이전트를 등록합니다.

    Args:
        app_spec: 애플리케이션 명세

    Returns:
        업데이트된 TDD 그룹 에이전트
    """
    try:
        # 기본 TDD 에이전트 목록 (항상 포함)
        agents = [model_test_case_agent]

        # 앱 명세에 따라 추가 TDD 에이전트 등록
        if "tests" in app_spec:
            # 여기서 앱 명세에 따라 추가적인 테스트 에이전트를 동적으로 추가할 수 있음
            # 예: WidgetTestCase, ControllerTestCase 등
            pass

        # 업데이트된 에이전트 목록으로 SequentialAgent 생성
        updated_tdd_group_agent = SequentialAgent(
            name="TDDGroupAgent",
            description="테스트 케이스 생성 작업을 순차적으로 수행하는 에이전트 그룹",
            sub_agents=agents
        )

        return updated_tdd_group_agent

    except Exception as e:
        logger.error(f"TDD 에이전트 등록 중 오류 발생: {str(e)}")
        return tdd_group_agent  # 오류 발생 시 기본 에이전트 반환

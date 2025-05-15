"""
ControllerGroupAgent: 컨트롤러 파일 생성을 조정하는 그룹 에이전트.

이 에이전트는 여러 컨트롤러 파일 생성 에이전트의 실행을 조정합니다.
"""
from google.adk import Agent

from src.agents.controller_group.user_controller_agent import (
    user_controller_agent
)
from src.utils.logger import logger


# 컨트롤러 그룹 에이전트 정의
controller_group_agent = Agent(
    name="ControllerGroupAgent",
    description="컨트롤러 파일 생성 작업을 병렬로 수행하는 에이전트 그룹",
    sub_agents=[
        user_controller_agent,
        # product_controller_agent와 같은 다른 컨트롤러 에이전트를 추가
    ]
)


def register_controller_agents(app_spec):
    """
    앱 명세에 따라 필요한 컨트롤러 에이전트를 등록합니다.

    Args:
        app_spec: 애플리케이션 명세

    Returns:
        업데이트된 컨트롤러 그룹 에이전트
    """
    try:
        # 기본 컨트롤러 에이전트 목록 (항상 포함)
        agents = [user_controller_agent]

        # 앱 명세에 따라 추가 컨트롤러 에이전트 등록
        if "controllers" in app_spec:
            # 여기서 앱 명세에 따라 추가적인 컨트롤러 에이전트를 동적으로 추가할 수 있음
            # 예: ProductController, OrderController 등
            pass

        # 업데이트된 에이전트 목록으로 Agent 생성
        updated_controller_group_agent = Agent(
            name="ControllerGroupAgent",
            description="컨트롤러 파일 생성 작업을 병렬로 수행하는 에이전트 그룹",
            sub_agents=agents
        )

        return updated_controller_group_agent

    except Exception as e:
        logger.error(f"컨트롤러 에이전트 등록 중 오류 발생: {str(e)}")
        return controller_group_agent  # 오류 발생 시 기본 에이전트 반환

"""
APIGroupAgent: API 파일 생성을 조정하는 그룹 에이전트.

이 에이전트는 여러 API 파일 생성 에이전트의 실행을 조정합니다.
"""
from google.adk.agents import ParallelAgent

from src.agents.api_group.user_api_routes_agent import user_api_routes_agent
from src.utils.logger import logger


# API 그룹 에이전트 정의
api_group_agent = ParallelAgent(
    name="APIGroupAgent",
    description="API 파일 생성 작업을 병렬로 수행하는 에이전트 그룹",
    sub_agents=[
        user_api_routes_agent,
        # product_api_routes_agent와 같은 다른 API 에이전트를 추가
    ]
)


def register_api_agents(app_spec):
    """
    앱 명세에 따라 필요한 API 에이전트를 등록합니다.

    Args:
        app_spec: 애플리케이션 명세

    Returns:
        업데이트된 API 그룹 에이전트
    """
    try:
        # 기본 API 에이전트 목록 (항상 포함)
        agents = [user_api_routes_agent]

        # 앱 명세에 따라 추가 API 에이전트 등록
        if "api_endpoints" in app_spec:
            # 여기서 앱 명세에 따라 추가적인 API 에이전트를 동적으로 추가할 수 있음
            # 예: ProductAPI, OrderAPI 등
            pass

        # 업데이트된 에이전트 목록으로 ParallelAgent 생성
        updated_api_group_agent = ParallelAgent(
            name="APIGroupAgent",
            description="API 파일 생성 작업을 병렬로 수행하는 에이전트 그룹",
            sub_agents=agents
        )

        return updated_api_group_agent

    except Exception as e:
        logger.error(f"API 에이전트 등록 중 오류 발생: {str(e)}")
        return api_group_agent  # 오류 발생 시 기본 에이전트 반환
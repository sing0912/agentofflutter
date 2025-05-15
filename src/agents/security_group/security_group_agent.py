"""
SecurityGroupAgent: 보안 검사를 조정하는 그룹 에이전트.

이 에이전트는 여러 보안 검사 에이전트의 실행을 조정합니다.
"""
from google.adk import Agent

from src.agents.security_group.dart_static_analysis_agent import dart_static_analysis_agent
from src.utils.logger import logger


# 보안 그룹 에이전트 정의
security_group_agent = Agent(
    name="SecurityGroupAgent",
    description="보안 검사 작업을 순차적으로 수행하는 에이전트 그룹",
    sub_agents=[
        dart_static_analysis_agent,
        # python_static_analysis_agent와 같은 다른 보안 에이전트를 추가
    ]
)


def register_security_agents(app_spec):
    """
    앱 명세에 따라 필요한 보안 에이전트를 등록합니다.

    Args:
        app_spec: 애플리케이션 명세

    Returns:
        업데이트된 보안 그룹 에이전트
    """
    try:
        # 기본 보안 에이전트 목록 (항상 포함)
        agents = [dart_static_analysis_agent]

        # 앱 명세에 따라 추가 보안 에이전트 등록
        if "security_checks" in app_spec:
            # 여기서 앱 명세에 따라 추가적인 보안 에이전트를 동적으로 추가할 수 있음
            # 예: PythonStaticAnalysis, SecurityVulnerabilityScan 등
            pass

        # 업데이트된 에이전트 목록으로 Agent 생성
        updated_security_group_agent = Agent(
            name="SecurityGroupAgent",
            description="보안 검사 작업을 순차적으로 수행하는 에이전트 그룹",
            sub_agents=agents
        )

        return updated_security_group_agent

    except Exception as e:
        logger.error(f"보안 에이전트 등록 중 오류 발생: {str(e)}")
        return security_group_agent  # 오류 발생 시 기본 에이전트 반환
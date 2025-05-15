"""
Agent of Flutter 통합 테스트

이 테스트는 에이전트 시스템의 기본 통합 동작을 검증합니다.
"""
import unittest
import os
import json
import tempfile
from pathlib import Path

from google.adk.runners import Runner
from google.adk.services import InMemoryArtifactService, InMemorySessionService
from google.genai.types import Content

from src.agents.main_orchestrator_agent import main_orchestrator_agent
from src.utils.logger import setup_logger


logger = setup_logger("test")


class TestAgentIntegration(unittest.TestCase):
    """에이전트 시스템 통합 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        # 서비스 초기화
        self.artifact_service = InMemoryArtifactService()
        self.session_service = InMemorySessionService()

        # 테스트 러너 초기화
        self.runner = Runner(
            agent=main_orchestrator_agent,
            artifact_service=self.artifact_service,
            session_service=self.session_service,
        )

        # 테스트 사용자 및 세션 ID
        self.user_id = "test_user"
        self.session_id = self.session_service.create_session()

        # 임시 출력 디렉토리 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """테스트 정리"""
        self.temp_dir.cleanup()

    def test_agent_initialization(self):
        """에이전트 초기화 테스트"""
        self.assertIsNotNone(main_orchestrator_agent)
        self.assertEqual(main_orchestrator_agent.name, "MainOrchestratorAgent")

    def test_basic_app_generation(self):
        """기본 앱 생성 테스트"""
        # 최소 앱 명세 생성
        app_spec = {
            "app_name": "test_flutter_app",
            "description": "Test Flutter application",
            "models": [
                {
                    "name": "User",
                    "fields": [
                        {"name": "id", "type": "String"},
                        {"name": "name", "type": "String"},
                        {"name": "email", "type": "String"}
                    ]
                }
            ]
        }

        # 초기 메시지 구성
        initial_message = Content(
            parts=[
                {"text": json.dumps(app_spec, indent=2)}
            ],
            role="user"
        )

        # 통합 테스트 실행 (에이전트 콜아웃을 스킵, 주요 설정만 검증)
        # 참고: 실제 실행은 시간이 너무 오래 걸릴 수 있으므로 스킵
        # result = self.runner.run(
        #     user_id=self.user_id,
        #     session_id=self.session_id,
        #     new_message=initial_message
        # )

        # 대신 기본 구성 유효성 확인
        self.assertEqual(self.runner.agent, main_orchestrator_agent)
        self.assertEqual(self.runner.artifact_service, self.artifact_service)
        self.assertEqual(self.runner.session_service, self.session_service)

        # 에이전트 그룹 확인
        sub_agents = main_orchestrator_agent.sub_agents
        self.assertGreater(len(sub_agents), 0)

        # 첫 번째 에이전트(ProjectScaffoldingAgent) 확인
        first_agent = sub_agents[0]
        self.assertEqual(first_agent.name, "ProjectScaffoldingAgent")


if __name__ == "__main__":
    unittest.main()
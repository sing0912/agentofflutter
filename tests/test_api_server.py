"""
API 서버 테스트 스크립트

이 스크립트는 Agent of Flutter API 서버의 기본 기능을 테스트합니다.
"""
import unittest
import httpx
import asyncio
import os

# API 엔드포인트 설정
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")
BASE_URL = f"http://{API_HOST}:{API_PORT}"


class TestAPIServer(unittest.TestCase):
    """API 서버 기능 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        # 샘플 앱 명세
        self.sample_app_spec = {
            "app_name": "test_flutter_app",
            "description": "Test Flutter application",
            "models": [
                {
                    "name": "User",
                    "fields": [
                        {"name": "id", "type": "String", "nullable": False},
                        {"name": "name", "type": "String", "nullable": False},
                        {"name": "email", "type": "String", "nullable": False},
                        {
                            "name": "createdAt",
                            "type": "DateTime",
                            "nullable": False
                        }
                    ]
                }
            ],
            "pages": ["HomePage", "LoginPage", "ProfilePage"]
        }

    async def asyncTearDown(self):
        """테스트 정리"""
        await self.client.aclose()

    def tearDown(self):
        """동기적 정리 작업"""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asyncTearDown())

    async def test_root_endpoint(self):
        """루트 엔드포인트 테스트"""
        response = await self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Agent of Flutter API")
        self.assertIn("endpoints", data)

    async def test_status_endpoint(self):
        """상태 엔드포인트 테스트"""
        response = await self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "running")
        self.assertIn("active_jobs", data)
        self.assertIn("completed_jobs", data)
        self.assertIn("failed_jobs", data)

    async def test_generate_app_endpoint(self):
        """앱 생성 엔드포인트 테스트"""
        response = await self.client.post(
            "/generate_app",
            json=self.sample_app_spec
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("job_id", data)
        self.assertEqual(data["status"], "pending")

        # 생성된 작업 ID 저장
        job_id = data["job_id"]

        # 작업 상태 확인 (최대 5초 대기)
        max_attempts = 5
        for i in range(max_attempts):
            await asyncio.sleep(1)
            response = await self.client.get(f"/job/{job_id}")
            self.assertEqual(response.status_code, 200)
            job_data = response.json()
            if job_data["status"] != "pending":
                break

        # 모든 작업 조회
        response = await self.client.get("/jobs")
        self.assertEqual(response.status_code, 200)
        jobs_data = response.json()
        self.assertIn(job_id, jobs_data)


def run_tests():
    """테스트 실행"""
    unittest.main()


if __name__ == "__main__":
    run_tests()
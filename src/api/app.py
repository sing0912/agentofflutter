"""
FastAPI 서버 구현.

이 모듈은 Flutter 앱 생성을 위한 FastAPI 서버를 구현합니다.
"""
import io
import uuid
import json
import zipfile
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content

from src.config.settings import API_HOST, API_PORT, API_DEBUG
from src.agents.main_orchestrator_agent import (
    main_orchestrator_agent, register_agents
)
from src.utils.logger import setup_logger


# API 로거 설정
api_logger = setup_logger("api")

# FastAPI 앱 생성
app = FastAPI(
    title="Agent of Flutter API",
    description="ADK 기반 Flutter 앱 생성 API",
    version="1.0.0",
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ADK 서비스 및 실행기 초기화
artifact_service = InMemoryArtifactService()
session_service = InMemorySessionService()

# 메인 오케스트레이터 에이전트를 사용한 ADK 실행기 생성
runner = Runner(
    app_name="AgentOfFlutter",
    agent=main_orchestrator_agent,
    artifact_service=artifact_service,
    session_service=session_service,
)

# 진행 중인 작업 상태 저장
active_jobs: Dict[str, Dict[str, Any]] = {}


# 앱 명세 모델
class AppSpec(BaseModel):
    app_name: str = Field(..., description="애플리케이션 이름")
    description: Optional[str] = Field(None, description="애플리케이션 설명")
    models: Optional[list] = Field(None, description="앱에서 사용할 모델 목록")
    pages: Optional[list] = Field(None, description="앱에서 사용할 페이지 목록")
    controllers: Optional[list] = Field(
        None, description="앱에서 사용할 컨트롤러 목록"
    )
    api_endpoints: Optional[list] = Field(
        None, description="앱에서 사용할 API 엔드포인트 목록"
    )
    tests: Optional[list] = Field(None, description="앱에서 수행할 테스트 목록")
    security_checks: Optional[list] = Field(
        None, description="앱에서 수행할 보안 검사 목록"
    )


# 작업 상태 모델
class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None
    artifacts: Optional[list] = None


# 서버 상태 모델
class ServerStatus(BaseModel):
    status: str = "running"
    version: str = "1.0.0"
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    uptime: str


async def handle_app_generation(job_id: str, app_spec: dict):
    """
    앱 생성 작업을 비동기로 처리합니다.

    Args:
        job_id: 작업 ID
        app_spec: 앱 명세 딕셔너리
    """
    try:
        # 작업 상태 업데이트
        active_jobs[job_id]["status"] = "running"
        active_jobs[job_id]["progress"] = 10
        active_jobs[job_id]["message"] = "Runner 초기화 중..."

        api_logger.info(f"작업 시작: {job_id}")

        # 앱 명세에 따라 에이전트 등록
        updated_agent = register_agents(app_spec)

        # 업데이트된 에이전트로 런너 재설정
        updated_runner = Runner(
            app_name="AgentOfFlutter",
            agent=updated_agent,
            artifact_service=artifact_service,
            session_service=session_service,
        )

        # 세션 생성
        user_id = str(uuid.uuid4())
        session_id = session_service.create_session(
            app_name="AgentOfFlutter",
            user_id=user_id
        )

        # 세션 ID 저장
        active_jobs[job_id]["session_id"] = session_id

        # 초기 메시지 구성
        initial_message = Content(
            parts=[
                {"text": json.dumps(app_spec, indent=2)}
            ],
            role="user"
        )

        active_jobs[job_id]["progress"] = 20
        active_jobs[job_id]["message"] = "앱 생성 시작..."

        # 에이전트 실행
        api_logger.info(f"세션 ID: {session_id}, 사용자 ID: {user_id}")
        run_generator = updated_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=initial_message
        )
        
        # 제너레이터 소비
        async for _ in run_generator:
            pass

        # 결과 처리
        active_jobs[job_id]["progress"] = 90
        active_jobs[job_id]["message"] = "결과 처리 중..."

        # 아티팩트 목록 가져오기
        artifacts = artifact_service.list_artifacts(session_id)

        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["progress"] = 100
        active_jobs[job_id]["message"] = "앱 생성 완료"
        active_jobs[job_id]["artifacts"] = [
            str(artifact) for artifact in artifacts
        ]
        active_jobs[job_id]["completed_at"] = datetime.now().isoformat()

        api_logger.info(f"작업 완료: {job_id}")

    except Exception as e:
        # 오류 발생 시 작업 상태 업데이트
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["message"] = f"오류 발생: {str(e)}"
        active_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        api_logger.error(f"작업 실패: {job_id}, 오류: {str(e)}")


@app.post("/generate_app", response_model=JobStatus)
async def generate_app(app_spec: AppSpec, background_tasks: BackgroundTasks):
    """
    새로운 Flutter 앱 생성 작업을 시작합니다.

    Args:
        app_spec: 앱 명세 데이터
        background_tasks: 백그라운드 작업 객체

    Returns:
        작업 ID와 초기 상태를 포함하는 JobStatus 객체
    """
    try:
        # 작업 ID 생성
        job_id = str(uuid.uuid4())

        # 초기 작업 상태 설정
        active_jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0,
            "message": "작업 초기화 중...",
            "artifacts": [],
            "created_at": datetime.now().isoformat()
        }

        # 백그라운드 작업으로 처리
        background_tasks.add_task(
            handle_app_generation,
            job_id,
            app_spec.dict()
        )

        return JobStatus(**active_jobs[job_id])
    except Exception as e:
        api_logger.error(f"앱 생성 요청 처리 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"앱 생성 요청 처리 중 오류 발생: {str(e)}"
        )


@app.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    특정 작업의 상태를 조회합니다.

    Args:
        job_id: 작업 ID

    Returns:
        작업 상태를 포함하는 JobStatus 객체
    """
    if job_id not in active_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"작업 ID {job_id}를 찾을 수 없습니다."
        )

    return JobStatus(**active_jobs[job_id])


@app.get("/jobs", response_model=Dict[str, JobStatus])
async def get_all_jobs():
    """
    모든 작업의 상태를 조회합니다.

    Returns:
        모든 작업의 상태를 포함하는 딕셔너리
    """
    return {
        job_id: JobStatus(**job_info)
        for job_id, job_info in active_jobs.items()
    }


@app.get("/download/{job_id}/{artifact_name}")
async def download_artifact(job_id: str, artifact_name: str):
    """
    생성된 아티팩트를 다운로드합니다.

    Args:
        job_id: 작업 ID
        artifact_name: 아티팩트 이름

    Returns:
        아티팩트 파일 스트림
    """
    if job_id not in active_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"작업 ID {job_id}를 찾을 수 없습니다."
        )

    job_info = active_jobs[job_id]

    if job_info["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"작업이 아직 완료되지 않았습니다. 현재 상태: {job_info['status']}"
        )

    session_id = job_info.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=500,
            detail="세션 ID를 찾을 수 없습니다."
        )

    # 아티팩트 존재 여부 확인
    artifacts = artifact_service.list_artifacts(session_id)
    if artifact_name not in [str(artifact) for artifact in artifacts]:
        raise HTTPException(
            status_code=404,
            detail=f"아티팩트 {artifact_name}을 찾을 수 없습니다."
        )

    try:
        # 아티팩트 로드
        artifact = artifact_service.load_artifact(session_id, artifact_name)
        if artifact is None:
            raise HTTPException(
                status_code=404,
                detail=f"아티팩트 {artifact_name}을 로드할 수 없습니다."
            )

        # 파일 타입 결정
        content_type = "application/octet-stream"
        if artifact_name.endswith(".dart"):
            content_type = "text/x-dart"
        elif artifact_name.endswith(".py"):
            content_type = "text/x-python"
        elif artifact_name.endswith(".json"):
            content_type = "application/json"
        elif artifact_name.endswith(".yaml") or artifact_name.endswith(".yml"):
            content_type = "text/yaml"
        elif artifact_name.endswith(".md"):
            content_type = "text/markdown"

        # 파일 스트림 반환
        content_disposition = f"attachment; filename={artifact_name}"
        return StreamingResponse(
            io.BytesIO(artifact.data),
            media_type=content_type,
            headers={"Content-Disposition": content_disposition}
        )

    except Exception as e:
        api_logger.error(f"아티팩트 다운로드 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"아티팩트 다운로드 중 오류 발생: {str(e)}"
        )


@app.get("/download_zip/{job_id}")
async def download_zip(job_id: str):
    """
    모든 아티팩트를 zip 파일로 다운로드합니다.

    Args:
        job_id: 작업 ID

    Returns:
        zip 파일 스트림
    """
    if job_id not in active_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"작업 ID {job_id}를 찾을 수 없습니다."
        )

    job_info = active_jobs[job_id]

    if job_info["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"작업이 아직 완료되지 않았습니다. 현재 상태: {job_info['status']}"
        )

    session_id = job_info.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=500,
            detail="세션 ID를 찾을 수 없습니다."
        )

    try:
        # 아티팩트 목록 가져오기
        artifacts = artifact_service.list_artifacts(session_id)

        # 앱 이름 가져오기
        app_spec = job_info.get("app_spec", {})
        app_name = app_spec.get("app_name", "flutter_app")

        # zip 파일 생성
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, "w", zipfile.ZIP_DEFLATED
        ) as zip_file:
            for artifact_name in artifacts:
                artifact = artifact_service.load_artifact(
                    session_id, str(artifact_name)
                )
                if artifact:
                    zip_file.writestr(str(artifact_name), artifact.data)

        # 파일 포인터를 시작으로 되돌림
        zip_buffer.seek(0)

        # zip 파일 반환
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={app_name}.zip"
            }
        )

    except Exception as e:
        api_logger.error(f"ZIP 파일 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ZIP 파일 생성 중 오류 발생: {str(e)}"
        )


@app.get("/status", response_model=ServerStatus)
async def get_server_status():
    """
    서버 상태를 조회합니다.

    Returns:
        서버 상태 정보
    """
    # 작업 통계 계산
    pending_count = sum(
        1 for job in active_jobs.values() if job["status"] == "pending"
    )
    running_count = sum(
        1 for job in active_jobs.values() if job["status"] == "running"
    )
    completed_count = sum(
        1 for job in active_jobs.values() if job["status"] == "completed"
    )
    failed_count = sum(
        1 for job in active_jobs.values() if job["status"] == "failed"
    )

    # 서버 시작 시간 (단순화를 위해 현재 세션 시작 시간으로 대체)
    server_start_time = datetime.now()
    uptime = datetime.now() - server_start_time

    return ServerStatus(
        active_jobs=pending_count + running_count,
        completed_jobs=completed_count,
        failed_jobs=failed_count,
        uptime=str(uptime)
    )


@app.get("/")
async def root():
    """
    루트 엔드포인트 - API 정보를 반환합니다.
    """
    return {
        "name": "Agent of Flutter API",
        "version": "1.0.0",
        "description": "ADK 기반 Flutter 앱 생성 API",
        "endpoints": [
            {
                "path": "/generate_app",
                "method": "POST",
                "description": "Flutter 앱 생성 요청"
            },
            {
                "path": "/job/{job_id}",
                "method": "GET",
                "description": "특정 작업 상태 조회"
            },
            {
                "path": "/jobs",
                "method": "GET",
                "description": "모든 작업 상태 조회"
            },
            {
                "path": "/download/{job_id}/{artifact_name}",
                "method": "GET",
                "description": "특정 아티팩트 다운로드"
            },
            {
                "path": "/download_zip/{job_id}",
                "method": "GET",
                "description": "모든 아티팩트를 ZIP으로 다운로드"
            },
            {
                "path": "/status",
                "method": "GET",
                "description": "서버 상태 조회"
            }
        ]
    }


def start_server():
    """
    FastAPI 서버를 시작합니다.
    """
    import uvicorn

    api_logger.info(f"서버 시작: http://{API_HOST}:{API_PORT}")
    uvicorn.run(
        "src.api.app:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_DEBUG
    )


if __name__ == "__main__":
    start_server()

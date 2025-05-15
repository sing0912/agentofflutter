"""
FastAPI 서버 구현.

이 모듈은 Flutter 앱 생성을 위한 FastAPI 서버를 구현합니다.
"""
import asyncio
import json
import time
import uuid
import io
import os
import zipfile
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from google.adk import Runner
from src.utils.logger import setup_logger

from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService

from src.config.settings import (
    API_HOST, API_PORT, API_DEBUG, FLUTTER_OUTPUT_DIR
)
from src.agents.main_orchestrator_agent import (
    main_orchestrator_agent, register_agents
)

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

# 사용자 ID에서 세션 객체로의 매핑을 저장 (Session 객체는 해시 불가능)
session_id_maps: Dict[str, Any] = {}
session_runners: Dict[str, Any] = {}  # 사용자 ID별 러너 객체 저장


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


# 파일 시스템에 아티팩트를 저장하는 함수 추가
async def save_artifacts_to_filesystem(job_id: str, artifacts: Dict[str, Any]):
    """
    메모리에 저장된 아티팩트를 파일 시스템에 저장합니다.
    
    Args:
        job_id: 작업 ID
        artifacts: 아티팩트 딕셔너리
    """
    try:
        # 작업별 디렉토리 생성
        job_output_dir = os.path.join(FLUTTER_OUTPUT_DIR, job_id)
        os.makedirs(job_output_dir, exist_ok=True)
        
        # 아티팩트 내용을 파일로 저장
        for artifact_name, artifact_content in artifacts.items():
            # 파일 경로 구성
            file_path = os.path.join(job_output_dir, artifact_name)
            
            # 디렉토리 구조 생성
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 파일 저장
            with open(file_path, 'wb') as f:
                f.write(artifact_content)
            
            api_logger.info(f"아티팩트 저장됨: {file_path}")
        
        # 아티팩트 목록 업데이트
        if job_id in active_jobs:
            active_jobs[job_id]["artifacts"] = list(artifacts.keys())
            api_logger.info(f"작업 {job_id}의 아티팩트 목록이 업데이트되었습니다.")
        
        return True
    except Exception as e:
        api_logger.error(f"아티팩트 저장 중 오류 발생: {str(e)}")
        return False


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
        api_logger.info(f"에이전트 등록 완료: {type(updated_agent).__name__}")

        # 세션 생성
        user_id = str(uuid.uuid4())
        api_logger.info(f"생성된 사용자 ID: {user_id}")

        session_id = session_service.create_session(
            app_name="AgentOfFlutter",
            user_id=user_id
        )
        type_name = type(session_id).__name__
        api_logger.info(f"세션 생성 완료: {type_name}, 값: {session_id}")

        # 세션 ID를 사용자 ID에 매핑
        session_id_str = str(session_id)
        api_logger.info(f"세션 ID 문자열: {session_id_str}")
        session_id_maps[user_id] = session_id
        session_runners[user_id] = runner

        api_logger.info("Runner 초기화 완료: Runner")

        # 메시지 내용 구성 - Content 클래스 우회
        initial_message = (
            f"안녕하세요! Flutter 앱을 생성해 주세요. 다음은 앱 명세입니다: "
            f"{json.dumps(app_spec, ensure_ascii=False)}"
        )
        api_logger.info("초기 메시지 구성 완료: 문자열 사용")

        # 작업 ID와 사용자 ID 연결
        active_jobs[job_id]["user_id"] = user_id
        active_jobs[job_id]["runner"] = runner
        active_jobs[job_id]["session_id"] = session_id_str

        # 세션 ID와 사용자 ID 기록
        api_logger.info(f"세션 ID: {session_id_str}, 사용자 ID: {user_id}")

        # 러너 실행 - 비동기 함수로 실행
        api_logger.info(
            f"run_async 호출 전 - 세션 ID 유형: {type(session_id).__name__}"
        )

        # 비동기 작업으로 실행 (여기서 initial_message 문자열 사용)
        try:
            run_task = asyncio.create_task(
                runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=initial_message  # 문자열 전달
                )
            )
            api_logger.info("앱 생성 작업 시작됨")
            
            # 작업이 완료될 때까지 대기
            await run_task
            
            # 작업이 완료되면 아티팩트 가져오기
            artifacts = {}
            for artifact_id in artifact_service.list_artifacts(session_id):
                artifact_data = artifact_service.get_artifact(
                    session_id, artifact_id
                )
                if artifact_data and artifact_data.data:
                    artifacts[artifact_id] = artifact_data.data
            
            # 비동기 작업 실행 후 아티팩트 저장 로그
            if artifacts:
                await save_artifacts_to_filesystem(job_id, artifacts)
                api_logger.info(
                    f"작업 {job_id}의 아티팩트가 저장되었습니다."
                )
            
        except Exception as e:
            api_logger.error(f"러너 실행 실패: {str(e)}")
            raise

        # 작업 완료 표시
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["progress"] = 100
        active_jobs[job_id]["message"] = "앱 생성 완료"

    except Exception as e:
        api_logger.error(f"작업 실패: {job_id}, 오류: {str(e)}")

        # 작업 실패 표시
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = "failed"
            active_jobs[job_id]["message"] = f"앱 생성 중 오류 발생: {str(e)}"


@app.post("/generate_app")
async def start_flutter_app_creation(request: Request):
    """
    Flutter 앱 생성 작업을 시작합니다.

    Request body는 앱 명세를 포함해야 합니다.
    """
    try:
        app_spec = await request.json()
        
        # 앱 이름 및 버전 정보 생성
        app_name = app_spec.get("app_name", "flutter_app")
        app_version = f"v{int(time.time()) % 10000}"
        folder_name = f"App_{app_name}_{app_version}"
        
        # 고유 작업 ID 생성
        job_id = str(uuid.uuid4())

        # 작업 상태 초기화 - job_id 필드 추가
        active_jobs[job_id] = {
            "job_id": job_id,  # job_id 필드 명시적 추가
            "folder_name": folder_name,  # 폴더명 저장
            "app_spec": app_spec,  # 앱 명세 저장
            "status": "pending",
            "progress": 0,
            "message": "작업 초기화 중...",
            "artifacts": [],
            "start_time": time.time()
        }

        # 백그라운드 작업으로 앱 생성 실행
        asyncio.create_task(start_app_creation(job_id, app_spec))

        return {
            "job_id": job_id,
            "status": active_jobs[job_id]["status"],
            "progress": active_jobs[job_id]["progress"],
            "message": active_jobs[job_id]["message"],
            "artifacts": active_jobs[job_id]["artifacts"],
            "folder_name": folder_name
        }

    except Exception as e:
        api_logger.error(f"앱 생성 요청 처리 중 오류 발생: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"앱 생성 시작 중 오류 발생: {str(e)}"}
        )


async def start_app_creation(job_id: str, app_spec: dict):
    """
    Flutter 앱 생성 프로세스를 시작합니다.

    Args:
        job_id: 작업 ID
        app_spec: 앱 명세 딕셔너리
    """
    try:
        # 앱 명세 저장
        active_jobs[job_id]["app_spec"] = app_spec

        # 디버그: 함수 시작 로그
        api_logger.info(f"앱 생성 시작: job_id={job_id}")
        api_logger.info(f"앱 명세: {json.dumps(app_spec, ensure_ascii=False)}")
        
        # ADK 문제를 우회하기 위해 직접 파일 생성 방식 사용
        api_logger.info("앱 생성 시작: 단순 파일 생성 방식")
        
        # 앱 이름 가져오기
        app_name = app_spec.get("app_name", "flutter_app")
        app_description = app_spec.get("description", "Flutter application")
        api_logger.info(f"앱 정보: 이름={app_name}, 설명={app_description}")

        # 앱 버전 및 폴더명 생성
        app_version = f"v{int(time.time()) % 10000}"  # 현재 시간의 일부를 사용한 버전 정보
        folder_name = f"App_{app_name}_{app_version}"  # 'App_' 접두사 추가
        
        # job_id와 폴더명을 매핑하여 저장
        active_jobs[job_id]["folder_name"] = folder_name
        
        # 작업별 출력 디렉토리 생성
        job_output_dir = os.path.join(FLUTTER_OUTPUT_DIR, folder_name)
        # 디버그: 디렉토리 생성
        api_logger.info(f"작업 디렉토리 경로: {job_output_dir}")
        os.makedirs(job_output_dir, exist_ok=True)
        api_logger.info(f"작업 디렉토리 생성 완료: {os.path.exists(job_output_dir)}")
        
        # 기본 디렉토리 구조 생성
        lib_dir = os.path.join(job_output_dir, "lib")
        models_dir = os.path.join(lib_dir, "models")
        pages_dir = os.path.join(lib_dir, "pages")
        
        # 디버그: 하위 디렉토리 생성
        api_logger.info(f"하위 디렉토리 생성: lib={lib_dir}")
        os.makedirs(lib_dir, exist_ok=True)
        api_logger.info(f"하위 디렉토리 생성: models={models_dir}")
        os.makedirs(models_dir, exist_ok=True)
        api_logger.info(f"하위 디렉토리 생성: pages={pages_dir}")
        os.makedirs(pages_dir, exist_ok=True)
        
        # 디버그: 디렉토리 생성 확인
        api_logger.info(f"lib 디렉토리 존재 여부: {os.path.exists(lib_dir)}")
        api_logger.info(f"models 디렉토리 존재 여부: {os.path.exists(models_dir)}")
        api_logger.info(f"pages 디렉토리 존재 여부: {os.path.exists(pages_dir)}")
        
        # 모델 파일 생성
        models = app_spec.get("models", [])
        model_files = []
        
        api_logger.info(f"모델 개수: {len(models)}")
        
        for model in models:
            model_name = model.get("name", "Unknown")
            model_file_path = os.path.join(
                models_dir, f"{model_name.lower()}.dart"
            )
            api_logger.info(f"모델 파일 생성: {model_file_path}")
            
            fields = model.get("fields", [])
            field_definitions = []
            constructor_params = []
            
            for field in fields:
                field_name = field.get("name", "unknown")
                field_type = field.get("type", "String")
                nullable = field.get("nullable", True)
                
                if nullable:
                    field_type = f"{field_type}?"
                    field_definitions.append(f"  {field_type} {field_name};")
                else:
                    field_definitions.append(
                        f"  final {field_type} {field_name};"
                    )
                
                constructor_params.append(f"    this.{field_name},")
            
            model_content = f"""
class {model_name} {{
{chr(10).join(field_definitions)}

  {model_name}({{
{chr(10).join(constructor_params)}
  }});

  factory {model_name}.fromJson(Map<String, dynamic> json) {{
    return {model_name}(
      // TODO: 구현
    );
  }}

  Map<String, dynamic> toJson() {{
    return {{
      // TODO: 구현
    }};
  }}
}}
"""
            
            # 디버그: 파일 쓰기 시도
            try:
                with open(model_file_path, 'w') as f:
                    f.write(model_content)
                api_logger.info(f"모델 파일 쓰기 성공: {model_file_path}")
            except Exception as e:
                api_logger.error(
                    f"모델 파일 쓰기 실패: {model_file_path}, 오류: {str(e)}"
                )
                raise
            
            model_files.append(f"models/{model_name.lower()}.dart")
        
        # 페이지 파일 생성
        pages = app_spec.get("pages", [])
        page_files = []
        
        api_logger.info(f"페이지 개수: {len(pages)}")
        
        for page_name in pages:
            page_file_path = os.path.join(
                pages_dir, f"{page_name.lower()}.dart"
            )
            api_logger.info(f"페이지 파일 생성: {page_file_path}")
            
            page_content = f"""
import 'package:flutter/material.dart';

class {page_name} extends StatelessWidget {{
  const {page_name}({{Key? key}}) : super(key: key);

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{page_name}'),
      ),
      body: const Center(
        child: Text('This is the {page_name}'),
      ),
    );
  }}
}}
"""
            
            # 디버그: 파일 쓰기 시도
            try:
                with open(page_file_path, 'w') as f:
                    f.write(page_content)
                api_logger.info(f"페이지 파일 쓰기 성공: {page_file_path}")
            except Exception as e:
                api_logger.error(
                    f"페이지 파일 쓰기 실패: {page_file_path}, 오류: {str(e)}"
                )
                raise
            
            page_files.append(f"pages/{page_name.lower()}.dart")
            
        # main.dart 파일 생성
        main_file_path = os.path.join(lib_dir, "main.dart")
        
        # 첫 번째 페이지가 없으면 기본 페이지 사용
        first_page = pages[0] if pages else "HomePage"
        
        main_content = f"""
import 'package:flutter/material.dart';
import 'pages/{first_page.lower()}.dart';

void main() {{
  runApp(const MyApp());
}}

class MyApp extends StatelessWidget {{
  const MyApp({{Key? key}}) : super(key: key);

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{app_name}',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: const {first_page}(),
    );
  }}
}}
"""
        
        with open(main_file_path, 'w') as f:
            f.write(main_content)
        api_logger.info(f"메인 파일 생성 완료: {main_file_path}")
        
        # pubspec.yaml 파일 생성
        pubspec_file_path = os.path.join(job_output_dir, "pubspec.yaml")
        
        pubspec_content = f"""
name: {app_name}
description: {app_description}
version: 1.0.0+1

environment:
  sdk: ">=3.0.0 <4.0.0"

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.2
  provider: ^6.0.5
  http: ^1.1.0
  json_annotation: ^4.8.1
  shared_preferences: ^2.2.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0
  build_runner: ^2.4.6
  json_serializable: ^6.7.1

flutter:
  uses-material-design: true
  assets:
    - assets/images/
"""
        
        with open(pubspec_file_path, 'w') as f:
            f.write(pubspec_content)
        api_logger.info(f"pubspec.yaml 파일 생성 완료: {pubspec_file_path}")
        
        # README.md 파일 생성
        readme_file_path = os.path.join(job_output_dir, "README.md")
        
        readme_content = f"""
# {app_name}

{app_description}

## Getting Started

This is a Flutter application.

### Prerequisites

- Flutter SDK
- Dart

### Running the application

1. Run `flutter pub get` to install dependencies
2. Run `flutter run` to start the application

## Features

- [Add your features here]
"""
        
        with open(readme_file_path, 'w') as f:
            f.write(readme_content)
        api_logger.info(f"README.md 파일 생성 완료: {readme_file_path}")
        
        # 생성된 모든 파일 목록
        artifact_files = [
            "lib/main.dart",
            "pubspec.yaml",
            "README.md"
        ] + [f"lib/{file}" for file in model_files + page_files]
        
        # 작업 상태 업데이트
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["progress"] = 100
        active_jobs[job_id]["message"] = "앱 생성 완료"
        active_jobs[job_id]["artifacts"] = artifact_files
        
        api_logger.info(
            f"앱 생성 완료: {app_name}, "
            f"파일 생성 수: {len(model_files) + len(page_files) + 3}"
        )
        
        # 디버그: 최종 파일 확인
        api_logger.info("생성된 파일 목록:")
        for root, _, files in os.walk(job_output_dir):
            for file in files:
                api_logger.info(f" - {os.path.join(root, file)}")

    except Exception as e:
        api_logger.error(f"작업 실패: {job_id}, 오류: {str(e)}")
        import traceback
        api_logger.error(f"상세 오류: {traceback.format_exc()}")

        # 작업 실패 표시
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = "failed"
            active_jobs[job_id]["message"] = f"앱 생성 중 오류 발생: {str(e)}"


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

    # job_id 값을 포함하여 JobStatus 생성
    job_info = active_jobs[job_id].copy()
    if "job_id" not in job_info:
        job_info["job_id"] = job_id
    return JobStatus(**job_info)


@app.get("/jobs", response_model=Dict[str, JobStatus])
async def get_all_jobs():
    """
    모든 작업의 상태를 조회합니다.

    Returns:
        모든 작업의 상태를 포함하는 딕셔너리
    """
    result = {}
    for job_id, job_info in active_jobs.items():
        # 각 작업 정보에 job_id 명시적 추가
        job_data = job_info.copy()
        if "job_id" not in job_data:
            job_data["job_id"] = job_id
        result[job_id] = JobStatus(**job_data)
    
    return result


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

    try:
        # 저장한 러너 객체 사용
        runner_obj = job_info.get("runner")
        if not runner_obj:
            raise HTTPException(
                status_code=500,
                detail="작업에 러너 객체가 없습니다."
            )

        # 세션 객체 가져오기
        user_id = job_info.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=500,
                detail="작업에 사용자 ID가 없습니다."
            )

        # 세션 맵에서 세션 객체 가져오기
        session = session_id_maps.get(user_id)
        if not session:
            # 세션 서비스에서 직접 가져오기 시도
            try:
                session = runner_obj.session_service.get_session(user_id)
                if session:
                    # 세션 맵에 저장
                    session_id_maps[user_id] = session
                    api_logger.info(f"세션 서비스에서 세션 가져옴: {user_id}")
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"사용자 ID {user_id}에 대한 세션을 찾을 수 없습니다."
                    )
            except Exception as e:
                api_logger.error(f"세션 가져오기 실패: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"세션 가져오기 실패: {str(e)}"
                )

        # 아티팩트 존재 여부 확인
        try:
            api_logger.info("아티팩트 목록 요청 - 세션: {0}".format(session))
            # 직접 아티팩트 서비스에 접근해 아티팩트 목록 가져오기
            try:
                artifacts = (
                    runner_obj.artifact_service.list_artifacts(
                        session
                    )
                )
            except AttributeError:
                # ADK 0.5.0 변경사항 - 세션 메서드 사용
                api_logger.info("list_artifacts 메서드 없음, 대체 방법 시도")
                try:
                    # 세션 객체의 get_artifacts 메서드 시도
                    if hasattr(session, 'get_artifacts'):
                        artifacts = session.get_artifacts()
                    else:
                        # runner의 직접 접근 시도
                        artifacts = runner_obj.list_artifacts(
                            session
                        )
                except Exception as inner_e:
                    api_logger.error(
                        f"대체 방법으로 아티팩트 목록 가져오기 실패: {str(inner_e)}"
                    )
                    artifacts = []

            if artifact_name not in [str(artifact) for artifact in artifacts]:
                raise HTTPException(
                    status_code=404,
                    detail=f"아티팩트 {artifact_name}을 찾을 수 없습니다."
                )
        except Exception as e:
            api_logger.warning(f"아티팩트 목록 가져오기 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"아티팩트 목록 가져오기 실패: {str(e)}"
            )

        # 아티팩트 로드
        try:
            artifact = runner_obj.artifact_service.load_artifact(
                session, artifact_name
            )
            if artifact is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"아티팩트 {artifact_name}을 로드할 수 없습니다."
                )
        except Exception as e:
            api_logger.warning(f"아티팩트 로드 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"아티팩트 로드 실패: {str(e)}"
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

    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"아티팩트 다운로드 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"아티팩트 다운로드 중 오류 발생: {str(e)}"
        )


@app.get("/download_zip/{job_id}")
async def download_zip(job_id: str):
    """
    특정 작업에서 생성된 모든 아티팩트를 ZIP 파일로 다운로드합니다.

    Args:
        job_id: 작업 ID

    Returns:
        ZIP 파일 스트림
    """
    if job_id not in active_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"작업 ID {job_id}를 찾을 수 없습니다."
        )

    if active_jobs[job_id]["status"] != "completed":
        return JSONResponse(
            status_code=400,
            content={"error": "작업이 아직 완료되지 않았습니다."}
        )

    try:
        # 작업별 출력 디렉토리 경로 (folder_name 사용)
        folder_name = active_jobs[job_id].get("folder_name", job_id)
        job_output_dir = os.path.join(FLUTTER_OUTPUT_DIR, folder_name)

        # 디렉토리가 존재하는지 확인
        if not os.path.exists(job_output_dir):
            api_logger.error(f"작업 디렉토리가 존재하지 않음: {job_output_dir}")
            return JSONResponse(
                status_code=404,
                content={"error": "생성된 앱 파일을 찾을 수 없습니다."}
            )

        # 앱 이름 가져오기 (있는 경우)
        app_spec = active_jobs[job_id].get("app_spec", {})
        app_name = app_spec.get("app_name", "flutter_app")
        app_version = folder_name.split('_')[-1] if '_' in folder_name else ""

        # 임시 메모리 버퍼에 ZIP 파일 생성
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 재귀적으로 모든 파일 압축
            for root, _, files in os.walk(job_output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # ZIP 내 상대 경로 계산
                    arcname = os.path.relpath(file_path, job_output_dir)
                    zip_file.write(file_path, arcname)

        # 버퍼 위치를 시작으로 재설정
        buffer.seek(0)

        # ZIP 파일 이름 설정 (앱 이름과 버전 사용)
        filename = f"App_{app_name}_{app_version}.zip"

        # 파일 다운로드 응답 반환
        return StreamingResponse(
            buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        api_logger.error(f"ZIP 파일 생성 중 오류 발생: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"ZIP 파일 생성 중 오류 발생: {str(e)}"}
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

    # 출력 디렉토리 생성
    os.makedirs(FLUTTER_OUTPUT_DIR, exist_ok=True)
    api_logger.info(f"출력 디렉토리 확인: {FLUTTER_OUTPUT_DIR}")

    # 서버 시작 메시지
    api_logger.info(f"서버 시작: http://{API_HOST}:{API_PORT}")

    # 서버 시작
    uvicorn.run(
        "src.api.app:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_DEBUG
    )


if __name__ == "__main__":
    start_server()

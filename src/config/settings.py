"""
프로젝트 설정 파일.
"""
import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 기본 디렉토리
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "src" / "templates"
ARTIFACTS_DIR = BASE_DIR / "src" / "artifacts"

# ADK 설정
ADK_API_KEY = os.getenv(
    "ADK_API_KEY", "AIzaSyA8NRAKPcQuVKL936lsoMVdlz2rpQh9Mgo"
)
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")

# API 서버 설정
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8002"))
API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"

# 데이터베이스 설정
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "flutter_agent")
DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Redis 설정
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Flutter 프로젝트 설정
FLUTTER_OUTPUT_DIR = os.getenv(
    "FLUTTER_OUTPUT_DIR", str(BASE_DIR / "output")
)

# 로깅 설정
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def get_agent_config(agent_type: str = "default") -> Dict[str, Any]:
    """특정 에이전트 유형에 대한 설정을 반환합니다."""
    base_config = {
        "model": DEFAULT_MODEL,
        "temperature": 0.2,
    }

    # 에이전트 유형별 특수 설정
    agent_specific_config: Dict[str, Dict[str, Any]] = {
        "model_agent": {
            "temperature": 0.1,
        },
        "webview_agent": {
            "temperature": 0.3,
        },
        "tdd_agent": {
            "temperature": 0.2,
        },
        "security_agent": {
            "temperature": 0.1,
        },
        "default": {
            "temperature": 0.2,
        }
    }

    # 기본 설정에 에이전트별 설정을 병합
    if agent_type in agent_specific_config:
        for key, value in agent_specific_config[agent_type].items():
            base_config[key] = value
    else:
        # agent_type이 없을 경우 기본 설정 사용
        agent_type = "default"
        for key, value in agent_specific_config[agent_type].items():
            base_config[key] = value

    return base_config

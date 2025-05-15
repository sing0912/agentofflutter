"""
ADK 코드 생성 도구.

이 모듈은 코드 생성을 위한 FunctionTool 구현을 포함합니다.
"""
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import jinja2

from google.adk.tools import FunctionTool
from google.genai.types import Part

from src.config.settings import TEMPLATES_DIR
from src.utils.logger import logger


def get_jinja_env(template_dir: Optional[str] = None) -> jinja2.Environment:
    """
    Jinja2 환경 객체를 생성하고 반환합니다.

    Args:
        template_dir: 템플릿 디렉토리 경로 (기본값: TEMPLATES_DIR)

    Returns:
        설정된 Jinja2 환경 객체
    """
    if template_dir is None:
        template_dir = TEMPLATES_DIR

    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def generate_dart_file(
    template_name: str,
    output_filename: str,
    context: Dict[str, Any],
    tool_context: Any
) -> Dict[str, Any]:
    """
    Jinja2 템플릿을 사용하여 Dart 파일을 생성합니다.

    Args:
        template_name: 사용할 템플릿 파일 이름
        output_filename: 생성된 파일의 이름
        context: 템플릿 렌더링을 위한 컨텍스트 변수 딕셔너리
        tool_context: ADK 도구 컨텍스트

    Returns:
        생성 결과를 포함하는 딕셔너리
    """
    try:
        # Jinja2 환경 설정
        env = get_jinja_env(str(Path(TEMPLATES_DIR) / "dart"))

        # 템플릿 로드 및 렌더링
        template = env.get_template(template_name)
        rendered_content = template.render(**context)

        # 아티팩트로 저장
        dart_bytes = rendered_content.encode('utf-8')
        dart_part = Part.from_data(
            data=dart_bytes,
            mime_type="text/x-dart"
        )

        # 아티팩트 저장
        version = tool_context.save_artifact(
            filename=output_filename,
            artifact=dart_part
        )

        # 중요 메타데이터를 세션 상태에 저장
        if "class_name" in context:
            # 에이전트 간 공유할 기본 클래스 정보
            class_meta = {
                "name": context["class_name"],
                "file": output_filename,
                "fields": context.get("fields", []),
                "type": context.get("type", "model")
            }

            # 생성된 모델 목록에 추가
            models_list = tool_context.state.get("generated_models", [])
            models_list.append(class_meta)
            tool_context.state["generated_models"] = models_list

            # 클래스 별로 이름 기반 인덱스 추가
            tool_context.state[f"model_{context['class_name']}"] = class_meta

        return {
            "success": True,
            "filename": output_filename,
            "version": version,
            "message": f"Dart 파일 '{output_filename}'이 성공적으로 생성되었습니다."
        }

    except Exception as e:
        logger.error(f"Dart 파일 생성 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Dart 파일 '{output_filename}' 생성 실패: {str(e)}"
        }


def generate_python_file(
    template_name: str,
    output_filename: str,
    context: Dict[str, Any],
    tool_context: Any
) -> Dict[str, Any]:
    """
    Jinja2 템플릿을 사용하여 Python 파일을 생성합니다.

    Args:
        template_name: 사용할 템플릿 파일 이름
        output_filename: 생성된 파일의 이름
        context: 템플릿 렌더링을 위한 컨텍스트 변수 딕셔너리
        tool_context: ADK 도구 컨텍스트

    Returns:
        생성 결과를 포함하는 딕셔너리
    """
    try:
        # Jinja2 환경 설정
        env = get_jinja_env(str(Path(TEMPLATES_DIR) / "python"))

        # 템플릿 로드 및 렌더링
        template = env.get_template(template_name)
        rendered_content = template.render(**context)

        # 아티팩트로 저장
        python_bytes = rendered_content.encode('utf-8')
        python_part = Part.from_data(
            data=python_bytes,
            mime_type="text/x-python"
        )

        # 아티팩트 저장
        version = tool_context.save_artifact(
            filename=output_filename,
            artifact=python_part
        )

        # API 엔드포인트와 같은 중요 메타데이터를 세션 상태에 저장
        if "endpoints" in context:
            api_endpoints = tool_context.state.get("api_endpoints", [])
            for endpoint in context["endpoints"]:
                api_endpoints.append({
                    "path": endpoint["path"],
                    "method": endpoint["method"],
                    "file": output_filename
                })
            tool_context.state["api_endpoints"] = api_endpoints

        return {
            "success": True,
            "filename": output_filename,
            "version": version,
            "message": f"Python 파일 '{output_filename}'이 성공적으로 생성되었습니다."
        }

    except Exception as e:
        logger.error(f"Python 파일 생성 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Python 파일 '{output_filename}' 생성 실패: {str(e)}"
        }


def direct_code_generation(
    code_content: str,
    output_filename: str,
    mime_type: str,
    tool_context: Any,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    LLM에 의해 직접 생성된 코드를 저장합니다.

    Args:
        code_content: 생성된 코드 문자열
        output_filename: 저장할 파일 이름
        mime_type: 파일의 MIME 타입 (예: "text/x-dart", "text/x-python")
        tool_context: ADK 도구 컨텍스트
        metadata: 세션 상태에 저장할 메타데이터 (선택사항)

    Returns:
        생성 결과를 포함하는 딕셔너리
    """
    try:
        # 코드 내용을 바이트로 인코딩
        code_bytes = code_content.encode('utf-8')
        code_part = Part.from_data(
            data=code_bytes,
            mime_type=mime_type
        )

        # 아티팩트로 저장
        version = tool_context.save_artifact(
            filename=output_filename,
            artifact=code_part
        )

        # 메타데이터가 제공된 경우 세션 상태에 저장
        if metadata:
            file_type = output_filename.split('.')[-1]  # 파일 확장자
            metadata_key = f"generated_{file_type}_files"

            # 기존 메타데이터 목록 불러오기
            existing_metadata = tool_context.state.get(metadata_key, [])

            # 새 메타데이터에 파일명 추가
            metadata["filename"] = output_filename

            # 메타데이터 목록에 추가
            existing_metadata.append(metadata)
            tool_context.state[metadata_key] = existing_metadata

        return {
            "success": True,
            "filename": output_filename,
            "version": version,
            "message": f"파일 '{output_filename}'이 성공적으로 생성되었습니다."
        }

    except Exception as e:
        logger.error(f"파일 생성 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"파일 '{output_filename}' 생성 실패: {str(e)}"
        }


# FunctionTool 정의
generate_dart_file_tool = FunctionTool(generate_dart_file)
generate_python_file_tool = FunctionTool(generate_python_file)
direct_code_generation_tool = FunctionTool(direct_code_generation)
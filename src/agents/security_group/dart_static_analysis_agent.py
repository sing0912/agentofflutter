"""
DartStaticAnalysisAgent: Dart 코드 정적 분석을 수행하는 에이전트.

이 에이전트는 Dart 코드의 정적 분석을 수행하여 잠재적인 문제를 찾아냅니다.
"""
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

from google.adk import Agent
from google.adk.tools import FunctionTool
from google.genai.types import Part

from src.utils.logger import logger


def run_dart_analyze(
    file_content: str,
    filename: str,
    tool_context: Any
) -> Dict[str, Any]:
    """
    Dart 파일의 정적 분석을 수행합니다.

    Args:
        file_content (str): 분석할 Dart 파일의 내용
        filename (str): 분석할 파일의 이름
        tool_context (Any): 도구 컨텍스트

    Returns:
        Dict[str, Any]: 분석 결과를 포함하는 딕셔너리
    """
    try:
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 분석할 Dart 파일 저장
            file_path = Path(temp_dir) / Path(filename).name
            with open(file_path, "w") as f:
                f.write(file_content)

            # analysis_options.yaml 파일 생성 (린트 규칙 정의)
            analysis_options_path = Path(temp_dir) / "analysis_options.yaml"
            with open(analysis_options_path, "w") as f:
                f.write("""
linter:
  rules:
    - avoid_empty_else
    - avoid_relative_lib_imports
    - avoid_returning_null_for_future
    - avoid_types_as_parameter_names
    - control_flow_in_finally
    - empty_statements
    - no_duplicate_case_values
    - no_logic_in_create_state
    - prefer_void_to_null
    - throw_in_finally
    - unnecessary_statements
    - await_only_futures
    - camel_case_types
    - cancel_subscriptions
    - directives_ordering
    - prefer_const_constructors
    - prefer_final_fields
    - prefer_final_locals
                """)

            # dart analyze 명령 실행
            cmd = ["dart", "analyze", str(file_path)]
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            # 분석 결과 파싱
            output = process.stdout
            error_output = process.stderr
            exit_code = process.returncode

            # 결과 구성
            issues = []
            if exit_code != 0:
                # 오류 메시지에서 이슈 추출
                for line in output.splitlines() + error_output.splitlines():
                    if line and not line.startswith("Analyzing"):
                        # 라인 정보, 오류 유형, 메시지 추출 시도
                        parts = line.split(":")
                        if len(parts) >= 3:
                            try:
                                line_num = int(parts[1].strip())
                                error_type = (
                                    "error"
                                    if "error" in parts[2].lower()
                                    else "warning"
                                )
                                message = ":".join(parts[3:]).strip()

                                issues.append({
                                    "line": line_num,
                                    "type": error_type,
                                    "message": message
                                })
                            except (ValueError, IndexError):
                                # 파싱 실패 시 전체 라인을 메시지로 저장
                                issues.append({
                                    "line": 0,
                                    "type": "info",
                                    "message": line.strip()
                                })

            # 분석 결과 보고서 생성
            report_content = {
                "filename": filename,
                "exit_code": exit_code,
                "issues": issues,
                "issues_count": len(issues),
                "success": exit_code == 0
            }

            # 보고서를 JSON 형태로 저장
            report_json = json.dumps(report_content, indent=2)
            report_bytes = report_json.encode("utf-8")
            report_part = Part.from_data(
                data=report_bytes,
                mime_type="application/json"
            )

            tool_context.save_artifact(
                filename=f"analysis_reports/{filename}_analysis.json",
                artifact=report_part
            )

            return report_content

    except Exception as e:
        logger.error(f"Dart 파일 분석 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Dart 파일 분석 실패: {str(e)}"
        }


def analyze_dart_files(tool_context) -> Dict[str, Any]:
    """
    모든 Dart 파일에 대한 정적 분석을 수행합니다.

    Args:
        tool_context: 도구 컨텍스트

    Returns:
        Dict[str, Any]: 전체 분석 결과를 포함하는 딕셔너리
    """
    try:
        # 아티팩트 목록에서 Dart 파일 필터링
        dart_files = [
            f for f in tool_context.list_artifacts()
            if f.endswith(".dart")
        ]

        if not dart_files:
            return {
                "success": True,
                "message": "분석할 Dart 파일이 없습니다.",
                "analyzed_files": 0,
                "total_issues": 0,
                "all_passed": True,
                "results": []
            }

        # 각 파일에 대한 분석 수행
        results = []
        total_issues = 0

        for dart_file in dart_files:
            # 파일 내용 읽기
            file_content = tool_context.read_artifact(dart_file)
            if not file_content:
                continue

            # 파일 분석
            analysis_result = run_dart_analyze(
                file_content=file_content,
                filename=dart_file,
                tool_context=tool_context
            )

            results.append(analysis_result)
            total_issues += analysis_result.get("issues_count", 0)

        # 전체 결과 요약
        all_passed = all(result.get("passed", False) for result in results)

        return {
            "success": True,
            "analyzed_files": len(results),
            "total_issues": total_issues,
            "all_passed": all_passed,
            "results": results,
            "message": f"{len(results)}개 파일 분석 완료, 총 {total_issues}개 이슈 발견"
        }

    except Exception as e:
        logger.error(f"Dart 파일 분석 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Dart 파일 분석 실패: {str(e)}"
        }


# FunctionTool 정의
analyze_dart_files_tool = FunctionTool(analyze_dart_files)

# Dart 정적 분석 에이전트 정의
dart_static_analysis_agent = Agent(
    name="DartStaticAnalysisAgent",
    description="Dart 코드의 정적 분석을 수행하는 에이전트",
    tools=[analyze_dart_files_tool]
)

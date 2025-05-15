"""
DartStaticAnalysisAgent: Dart 코드 정적 분석을 수행하는 에이전트.

이 에이전트는 생성된 Dart 코드에 대한 정적 분석을 수행하여 보안 취약점과 품질 문제를 검출합니다.
"""
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, Any

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
    Dart 코드 정적 분석을 실행합니다.

    Args:
        file_content: 분석할 Dart 파일 내용
        filename: 분석할 파일 이름
        tool_context: ADK 도구 컨텍스트

    Returns:
        분석 결과를 포함하는 딕셔너리
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

            # 아티팩트로 저장
            report_filename = (
                f"security/reports/{Path(filename).stem}_analysis.json"
            )
            version = tool_context.save_artifact(
                filename=report_filename,
                artifact=report_part
            )

            # 세션 상태에 결과 요약 저장
            security_reports = tool_context.state.get("security_reports", [])
            security_reports.append({
                "filename": filename,
                "report_file": report_filename,
                "issues_count": len(issues),
                "success": exit_code == 0
            })
            tool_context.state["security_reports"] = security_reports

            return {
                "success": True,
                "report_filename": report_filename,
                "version": version,
                "issues_count": len(issues),
                "passed": exit_code == 0,
                "message": (
                    f"Dart 정적 분석 완료: {len(issues)}개 이슈 발견"
                    if issues else "Dart 정적 분석 성공: 이슈 없음"
                )
            }

    except Exception as e:
        logger.error(f"Dart 정적 분석 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Dart 정적 분석 실패: {str(e)}"
        }


# FunctionTool 정의
run_dart_analyze_tool = FunctionTool(run_dart_analyze)


# Dart 정적 분석 에이전트 정의
dart_static_analysis_agent = Agent(
    name="DartStaticAnalysisAgent",
    description="생성된 Dart 코드의 정적 분석을 수행하는 에이전트",
    tools=[run_dart_analyze_tool]
)


def analyze_dart_files(tool_context) -> Dict[str, Any]:
    """
    생성된 모든 Dart 파일에 대해 정적 분석을 수행합니다.

    Args:
        tool_context: 도구 컨텍스트

    Returns:
        분석 결과 요약을 포함하는 딕셔너리
    """
    results = []

    try:
        # 세션 상태에서 생성된 Dart 파일 목록 가져오기
        dart_files = []

        # 아티팩트 목록 가져오기
        artifacts = tool_context.list_artifacts()

        # Dart 파일 필터링
        for artifact in artifacts:
            if artifact.endswith(".dart"):
                dart_files.append(artifact)

        if not dart_files:
            logger.warning("분석할 Dart 파일이 없습니다.")
            return {
                "success": True,
                "analyzed_files": 0,
                "message": "분석할 Dart 파일이 없습니다."
            }

        # 각 파일에 대해 정적 분석 실행
        for filename in dart_files:
            # 아티팩트에서 파일 내용 로드
            artifact = tool_context.load_artifact(filename=filename)
            if artifact:
                file_content = artifact.data.decode("utf-8")

                # 정적 분석 실행
                result = run_dart_analyze(
                    file_content=file_content,
                    filename=filename,
                    tool_context=tool_context
                )

                results.append(result)
            else:
                logger.warning(f"파일을 로드할 수 없음: {filename}")

        # 종합 결과 계산
        total_issues = sum(result.get("issues_count", 0) for result in results)
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

"""
AndroidTestAgent: 안드로이드 빌드 파일 테스트 에이전트.

이 에이전트는 안드로이드 빌드 파일을 테스트합니다.
"""
from google.adk import Agent
from google.adk.tools import FunctionTool
from google.genai.types import Part

from src.utils.logger import logger


def test_android_build_files(tool_context) -> dict:
    """
    안드로이드 빌드 파일 테스트를 수행합니다.

    Args:
        tool_context: 도구 컨텍스트

    Returns:
        테스트 결과를 포함하는 딕셔너리
    """
    try:
        app_name = tool_context.state.get("app_name", "flutter_app")
        session_id = tool_context.get_session_id()
        logger.info(f"세션 {session_id}에서 안드로이드 빌드 파일 테스트 시작")

        # 필수 안드로이드 빌드 파일 목록
        required_files = [
            "android/build.gradle",
            "android/settings.gradle",
            "android/app/build.gradle",
            "android/app/src/main/AndroidManifest.xml",
            "android/app/src/main/kotlin/com/example/{app_name_slug}/MainActivity.kt",
            "android/app/src/main/res/values/strings.xml",
            "android/app/src/main/res/drawable/launch_background.xml",
            "android/app/src/main/res/drawable-v21/launch_background.xml",
            "android/gradle/wrapper/gradle-wrapper.properties"
        ]

        # 파일 존재 여부 및 내용 검사 로직
        test_results = {
            "passed": [],
            "failed": []
        }

        app_name_slug = app_name.lower().replace('-', '_').replace(' ', '_')
        
        # 각 파일에 대한 테스트 수행
        for file_path in required_files:
            actual_path = file_path.replace("{app_name_slug}", app_name_slug)
            
            # 아티팩트 서비스에서 파일 존재 여부 확인
            artifact_exists = actual_path in tool_context.list_artifacts()
            
            if artifact_exists:
                test_results["passed"].append(f"{actual_path} 파일이 존재합니다.")
            else:
                test_results["failed"].append(f"{actual_path} 파일이 존재하지 않습니다.")
                logger.warning(f"세션 {session_id}에서 필수 파일이 없습니다: {actual_path}")

        # 테스트 보고서 생성
        total_tests = len(required_files)
        passed_tests = len(test_results["passed"])
        failed_tests = len(test_results["failed"])
        
        test_report = f"""
# 안드로이드 빌드 파일 테스트 보고서

## 요약
- 총 테스트: {total_tests}
- 통과: {passed_tests}
- 실패: {failed_tests}

## 테스트 결과

### 통과한 테스트
{"없음" if not test_results["passed"] else ""}
"""
        for passed in test_results["passed"]:
            test_report += f"- ✅ {passed}\n"

        test_report += """
### 실패한 테스트
"""
        if not test_results["failed"]:
            test_report += "- 모든 테스트 통과\n"
        else:
            for failed in test_results["failed"]:
                test_report += f"- ❌ {failed}\n"

        # 테스트 보고서를 아티팩트로 저장
        report_bytes = test_report.encode("utf-8")
        report_part = Part.from_data(
            data=report_bytes,
            mime_type="text/markdown"
        )

        tool_context.save_artifact(
            filename="test_reports/android_build_test_report.md",
            artifact=report_part
        )

        return {
            "success": True,
            "test_passed": failed_tests == 0,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "report": "test_reports/android_build_test_report.md",
            "message": f"안드로이드 빌드 파일 테스트 완료 (통과: {passed_tests}, 실패: {failed_tests})"
        }

    except Exception as e:
        logger.error(f"안드로이드 빌드 파일 테스트 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"안드로이드 빌드 파일 테스트 실패: {str(e)}"
        }


# FunctionTool 정의
test_android_build_files_tool = FunctionTool(test_android_build_files)

# 안드로이드 테스트 에이전트 정의
android_test_agent = Agent(
    name="AndroidTestAgent",
    description="안드로이드 빌드 파일을 테스트하는 에이전트",
    tools=[test_android_build_files_tool]
) 
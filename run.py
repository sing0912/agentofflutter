import requests
import json
import time
import os

# API 서버의 기본 URL을 설정합니다.
BASE_URL = "http://localhost:8000"


def print_step_header(step_number, title, is_optional=False):
    """각 단계의 헤더를 출력하는 함수입니다."""
    optional_text = "(선택 사항)" if is_optional else ""
    print(f"\n\n--- {step_number}. {title} {optional_text} ---")


def get_api_info():
    """1. API 정보 조회를 수행합니다."""
    print_step_header(1, "API 정보 조회", is_optional=True)
    try:
        response = requests.get(f"{BASE_URL}/")
        response.raise_for_status()  # HTTP 오류 발생 시 예외를 발생시킵니다.
        print("서버 응답:")
        # 응답이 JSON 형식일 수 있으므로, 예쁘게 출력 시도
        try:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(response.text)  # JSON이 아니면 텍스트 그대로 출력
    except requests.exceptions.RequestException as e:
        print(f"오류 발생: {e}")


def get_server_status():
    """2. 서버 상태 조회를 수행합니다."""
    print_step_header(2, "서버 상태 조회", is_optional=True)
    try:
        response = requests.get(f"{BASE_URL}/status")
        response.raise_for_status()
        print("서버 응답:")
        try:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"오류 발생: {e}")


def generate_flutter_app():
    """3. Flutter 앱 생성 요청을 보내고 job_id를 반환합니다."""
    print_step_header(3, "Flutter 앱 생성 요청")
    payload = {
        "app_name": "my_flutter_app",
        "description": "A sample Flutter application",
        "models": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "String"},
                    {"name": "name", "type": "String"},
                    {"name": "email", "type": "String"},
                    {"name": "createdAt", "type": "DateTime"}
                ]
            }
        ],
        "pages": ["HomePage", "LoginPage", "ProfilePage"]
    }
    headers = {"Content-Type": "application/json"}
    job_id = None
    try:
        print("요청 데이터:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        response = requests.post(
            f"{BASE_URL}/generate_app",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        print("\n서버 응답:")
        response_data = response.json()
        print(json.dumps(response_data, indent=2, ensure_ascii=False))

        if "job_id" in response_data:
            job_id = response_data["job_id"]
            print(f"\n>>> 중요: 작업 ID '{job_id}'를 발급받았습니다. <<<")
        else:
            print(
                "\n>>> 경고: 응답에서 'job_id'를 찾을 수 없습니다. "
                "후속 작업에 문제가 발생할 수 있습니다. <<<"
            )
            print("응답 전문을 확인하세요:", response_data)

    except requests.exceptions.RequestException as e:
        print(f"오류 발생: {e}")
    except json.JSONDecodeError:
        # 응답이 JSON이 아닐 경우를 대비
        error_message = "오류: 서버 응답이 유효한 JSON 형식이 아닙니다."
        if 'response' in locals() and hasattr(response, 'text'):
            error_message += f"\n원본 응답: {response.text}"
        print(error_message)

    return job_id


def get_job_status(job_id, step_number=4, poll=False):
    """4. 특정 작업 상태를 조회합니다. poll=True이면 완료될 때까지 반복 확인합니다."""
    if not job_id:
        print("오류: job_id가 제공되지 않아 작업 상태를 조회할 수 없습니다.")
        return None

    header_title = "특정 작업 상태 조회"
    if poll:
        header_title += " (완료될 때까지 반복 확인)"
    print_step_header(step_number, header_title)

    status = None
    try:
        # API 서버의 응답 형식에 따라 'status' 필드명이나 값은 달라질 수 있습니다.
        # 예시: {"status": "processing" | "completed" | "failed",
        #       "details": "..."}
        max_retries = 10  # 최대 10번 시도 (폴링 시)
        retry_interval = 5  # 5초 간격 (폴링 시)

        for attempt in range(max_retries if poll else 1):
            if poll:
                print(
                    f"작업 '{job_id}' 상태 확인 중... "
                    f"(시도 {attempt + 1}/{max_retries})"
                )

            response = requests.get(f"{BASE_URL}/job/{job_id}")
            response.raise_for_status()
            response_data = response.json()
            print(json.dumps(response_data, indent=2, ensure_ascii=False))

            status = response_data.get("status")  # 실제 API 응답의 상태 필드명으로 변경 필요

            if poll:
                if status == "completed":
                    print(f"작업 '{job_id}'가 완료되었습니다.")
                    break
                elif status == "failed":
                    print(f"작업 '{job_id}'가 실패했습니다.")
                    break
                else:
                    if attempt < max_retries - 1:  # 마지막 시도가 아니면 대기
                        print(
                            f"현재 상태: {status}. "
                            f"{retry_interval}초 후 다시 시도합니다."
                        )
                        time.sleep(retry_interval)
                    else:
                        print(
                            "최대 시도 횟수를 초과했습니다. "
                            "작업이 아직 완료되지 않았거나 상태를 알 수 없습니다."
                        )
            else:  # poll=False이면 한 번만 실행하고 종료
                break
        return status  # 마지막으로 확인된 상태 반환

    except requests.exceptions.RequestException as e:
        print(f"오류 발생: {e}")
    except json.JSONDecodeError:
        error_message = "오류: 서버 응답이 유효한 JSON 형식이 아닙니다."
        if 'response' in locals() and hasattr(response, 'text'):
            error_message += f"\n원본 응답: {response.text}"
        print(error_message)
    return status


def get_all_jobs(step_number=5):
    """5. 모든 작업 상태를 조회합니다."""
    print_step_header(step_number, "모든 작업 상태 조회", is_optional=True)
    try:
        response = requests.get(f"{BASE_URL}/jobs")
        response.raise_for_status()
        print("서버 응답:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.RequestException as e:
        print(f"오류 발생: {e}")
    except json.JSONDecodeError:
        error_message = "오류: 서버 응답이 유효한 JSON 형식이 아닙니다."
        if 'response' in locals() and hasattr(response, 'text'):
            error_message += f"\n원본 응답: {response.text}"
        print(error_message)


def download_artifact(job_id, artifact_path="main.dart", step_number=6):
    """6. 특정 아티팩트를 다운로드합니다."""
    if not job_id:
        print("오류: job_id가 제공되지 않아 아티팩트를 다운로드할 수 없습니다.")
        return

    print_step_header(step_number, f"특정 아티팩트 다운로드 (경로: {artifact_path})")
    # artifact_path에 디렉토리 구분자가 포함될 수 있으므로 os.path.basename 사용
    base_artifact_name = os.path.basename(artifact_path)
    output_filename = (
        f"{os.path.splitext(base_artifact_name)[0]}_downloaded"
        f"{os.path.splitext(base_artifact_name)[1]}"
    )
    if not base_artifact_name:  # artifact_path가 비어있거나 '/'로 끝나는 경우
        output_filename = f"{job_id}_artifact_downloaded"

    try:
        print(
            f"아티팩트 '{artifact_path}' 다운로드 시도 중... "
            f"(저장 파일명: {output_filename})"
        )
        # GET 요청 시 URL에 artifact_path가 포함되므로, URL 인코딩이 필요할 수 있습니다.
        # requests는 일반적으로 이를 자동으로 처리하지만, 특수문자가 많은 경우 확인이 필요합니다.
        response = requests.get(
            f"{BASE_URL}/download/{job_id}/{artifact_path}",
            stream=True
        )
        response.raise_for_status()

        with open(output_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"아티팩트 '{artifact_path}'를 '{output_filename}'으로 성공적으로 다운로드했습니다.")
    except requests.exceptions.RequestException as e:
        print(f"오류 발생: {e}")
    except IOError as e:
        print(f"파일 쓰기 오류: {e}")


def download_all_artifacts_zip(
    job_id,
    app_name="my_flutter_app",
    step_number=7
):
    """7. 모든 아티팩트를 ZIP으로 다운로드합니다."""
    if not job_id:
        print("오류: job_id가 제공되지 않아 ZIP 아티팩트를 다운로드할 수 없습니다.")
        return

    print_step_header(step_number, "모든 아티팩트를 ZIP으로 다운로드")
    output_filename = f"{app_name}_downloaded.zip"

    try:
        print(f"ZIP 아티팩트 다운로드 시도 중... (저장 파일명: {output_filename})")
        response = requests.get(
            f"{BASE_URL}/download_zip/{job_id}",
            stream=True
        )
        response.raise_for_status()

        with open(output_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"ZIP 아티팩트를 '{output_filename}'으로 성공적으로 다운로드했습니다.")
    except requests.exceptions.RequestException as e:
        print(f"오류 발생: {e}")
    except IOError as e:
        print(f"파일 쓰기 오류: {e}")


if __name__ == "__main__":
    # --- 1. API 정보 조회 (선택 사항) ---
    if input("1. API 정보 조회를 실행하시겠습니까? (y/N): ").strip().lower() == 'y':
        get_api_info()

    # --- 2. 서버 상태 조회 (선택 사항) ---
    if input("2. 서버 상태 조회를 실행하시겠습니까? (y/N): ").strip().lower() == 'y':
        get_server_status()

    # --- 3. Flutter 앱 생성 요청 ---
    current_job_id = None
    if input("3. Flutter 앱 생성을 요청하시겠습니까? (Y/n): ").strip().lower() != 'n':
        current_job_id = generate_flutter_app()
    else:
        manual_job_id = input(
            "Flutter 앱 생성을 건너뛰었습니다. "
            "사용할 기존 job_id가 있다면 입력하세요 (없으면 Enter): "
        ).strip()
        if manual_job_id:
            current_job_id = manual_job_id

    if current_job_id:
        print(f"\n>>> 현재 사용될 작업 ID: {current_job_id} <<<")
        print(
            "----------------------------------------"
            "----------------------------------------"
        )
        print("이 작업 ID를 사용하여 후속 단계를 진행할 수 있습니다.")

        # --- 4. 특정 작업 상태 조회 ---
        if input(
            f"\n4. 작업 '{current_job_id}' 상태를 조회하시겠습니까? (y/N): "
        ).strip().lower() == 'y':
            poll_status = input(
                "   완료될 때까지 반복 확인하시겠습니까? (y/N): "
            ).strip().lower() == 'y'
            get_job_status(current_job_id, poll=poll_status)

        # --- 5. (선택 사항) 모든 작업 상태 조회 ---
        if input("\n5. 모든 작업 상태를 조회하시겠습니까? (y/N): ").strip().lower() == 'y':
            get_all_jobs()

        # 작업 완료 여부를 가정하고 다운로드 진행 (실제로는 get_job_status의 결과를 확인해야 함)
        # 여기서는 사용자의 선택에 따라 다운로드를 시도하도록 합니다.
        print(f"\n작업 '{current_job_id}'에 대한 다운로드 단계를 진행합니다.")
        print("주의: 이전 단계에서 작업이 'completed' 상태인지 확인하는 것이 좋습니다.")

        # --- 6. (작업 완료 후) 특정 아티팩트 다운로드 ---
        if input(
            f"6. 작업 '{current_job_id}'의 특정 아티팩트를 다운로드하시겠습니까? (y/N): "
        ).strip().lower() == 'y':
            artifact_to_download = input(
                "   다운로드할 아티팩트 경로를 입력하세요 "
                "(예: main.dart, src/generated/user_model.dart 등): "
            ).strip()
            if artifact_to_download:
                download_artifact(
                    current_job_id,
                    artifact_path=artifact_to_download
                )
            else:
                print("   아티팩트 경로가 입력되지 않아 다운로드를 건너뜁니다.")

        # --- 7. (작업 완료 후) 모든 아티팩트를 ZIP으로 다운로드 ---
        if input(
            f"7. 작업 '{current_job_id}'의 모든 아티팩트를 ZIP으로 다운로드하시겠습니까? (y/N): "
        ).strip().lower() == 'y':
            job_response = requests.get(
                f"{BASE_URL}/job/{current_job_id}"
            ).text
            job_data = json.loads(job_response)
            default_app_name = job_data.get("app_name", "my_flutter_app")

            print(
                "   ZIP 파일명에 사용할 앱 이름을 입력하세요 "
                f"(기본값: my_flutter_app, "
                f"현재 job_id의 앱 이름: {default_app_name}): "
            )
            app_name_for_zip = input().strip()
            if not app_name_for_zip:
                app_name_for_zip = default_app_name

            download_all_artifacts_zip(
                current_job_id,
                app_name=app_name_for_zip
            )
    else:
        print("\njob_id가 없어 후속 작업을 진행할 수 없습니다.")

    print("\n--- 모든 안내 끝 ---")

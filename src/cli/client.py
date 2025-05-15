"""
CLI 클라이언트 도구.

이 모듈은 Agent of Flutter API 서버와 통신하기 위한 CLI 도구를 제공합니다.
"""
import os
import sys
import json
import time
import argparse
import httpx

from src.utils.logger import setup_logger

# 로거 설정
cli_logger = setup_logger("cli")

# 기본 API 엔드포인트 설정
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")
BASE_URL = f"http://{API_HOST}:{API_PORT}"

# 시작 시간 기록 (uptime 계산용)
start_time = time.time()


def parse_args():
    """
    명령줄 인자를 파싱합니다.

    Returns:
        파싱된 인자
    """
    parser = argparse.ArgumentParser(
        description="Agent of Flutter API 클라이언트"
    )

    subparsers = parser.add_subparsers(dest="command", help="명령")

    # 'status' 명령
    status_parser = subparsers.add_parser("status", help="서버 상태 확인")

    # 'list' 명령
    list_parser = subparsers.add_parser("list", help="모든 작업 목록 조회")

    # 'create' 명령
    create_parser = subparsers.add_parser("create", help="새로운 Flutter 앱 생성")
    create_parser.add_argument(
        "--spec", "-s", required=True,
        help="앱 명세 JSON 파일 경로"
    )

    # 'show' 명령
    show_parser = subparsers.add_parser("show", help="특정 작업 상태 조회")
    show_parser.add_argument(
        "--job-id", "-j", required=True,
        help="조회할 작업 ID"
    )

    # 'download' 명령
    download_parser = subparsers.add_parser("download", help="생성된 앱 다운로드")
    download_parser.add_argument(
        "--job-id", "-j", required=True,
        help="다운로드할 작업 ID"
    )
    download_parser.add_argument(
        "--output", "-o", default=".",
        help="출력 디렉토리 (기본값: 현재 디렉토리)"
    )

    return parser.parse_args()


async def get_server_status():
    """
    서버 상태를 확인합니다.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        try:
            response = await client.get("/status")
            response.raise_for_status()
            status_data = response.json()

            print(f"서버 상태: {status_data['status']}")
            print(f"활성 작업: {status_data['active_jobs']}")
            print(f"완료된 작업: {status_data['completed_jobs']}")
            print(f"실패한 작업: {status_data['failed_jobs']}")
            print(f"가동 시간: {status_data['uptime']}")

            return True
        except Exception as e:
            cli_logger.error(f"서버 상태 확인 중 오류 발생: {str(e)}")
            print(f"오류: {str(e)}")
            return False


async def list_jobs():
    """
    모든 작업 목록을 조회합니다.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        try:
            response = await client.get("/jobs")
            response.raise_for_status()
            jobs_data = response.json()

            if not jobs_data:
                print("작업이 없습니다.")
                return True

            print(f"총 {len(jobs_data)}개 작업:")
            for job_id, job_info in jobs_data.items():
                status = job_info["status"]
                progress = job_info.get("progress", 0)
                message = job_info.get("message", "")

                # 상태별 색상 코드
                color = ""
                if status == "completed":
                    color = "\033[92m"  # 녹색
                elif status == "failed":
                    color = "\033[91m"  # 빨간색
                elif status == "running":
                    color = "\033[93m"  # 노란색
                reset = "\033[0m"

                print(f"- 작업 ID: {job_id}")
                print(f"  상태: {color}{status}{reset} ({progress}%)")
                print(f"  메시지: {message}")
                print("")

            return True
        except Exception as e:
            cli_logger.error(f"작업 목록 조회 중 오류 발생: {str(e)}")
            print(f"오류: {str(e)}")
            return False


async def show_job(job_id: str):
    """
    특정 작업의 상태를 조회합니다.

    Args:
        job_id: 작업 ID
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        try:
            response = await client.get(f"/job/{job_id}")
            response.raise_for_status()
            job_data = response.json()

            # 상태별 색상 코드
            status = job_data["status"]
            color = ""
            if status == "completed":
                color = "\033[92m"  # 녹색
            elif status == "failed":
                color = "\033[91m"  # 빨간색
            elif status == "running":
                color = "\033[93m"  # 노란색
            reset = "\033[0m"

            print(f"작업 ID: {job_id}")
            print(f"상태: {color}{status}{reset} ({job_data.get('progress', 0)}%)")
            print(f"메시지: {job_data.get('message', '')}")

            if job_data.get("artifacts"):
                print(f"생성된 파일: {len(job_data['artifacts'])}개")
                for i, artifact in enumerate(job_data["artifacts"][:5]):
                    print(f"  - {artifact}")
                if len(job_data["artifacts"]) > 5:
                    print(f"  ... 외 {len(job_data['artifacts'])-5}개")

            return True
        except Exception as e:
            cli_logger.error(f"작업 상태 조회 중 오류 발생: {str(e)}")
            print(f"오류: {str(e)}")
            return False


async def create_app(spec_file: str):
    """
    새로운 Flutter 앱 생성을 요청합니다.

    Args:
        spec_file: 앱 명세 JSON 파일 경로
    """
    try:
        # 앱 명세 파일 로드
        with open(spec_file, "r") as f:
            app_spec = json.load(f)

        print(f"앱 명세 로드 완료: {app_spec.get('app_name', '이름 없음')}")

        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # 앱 생성 요청
            response = await client.post("/generate_app", json=app_spec)
            response.raise_for_status()
            result = response.json()

            job_id = result["job_id"]
            print(f"앱 생성 요청 성공: 작업 ID {job_id}")

            # 작업 상태 실시간 업데이트
            prev_progress = -1
            print("작업 진행 상태:")
            while True:
                try:
                    status_response = await client.get(f"/job/{job_id}")
                    status_response.raise_for_status()
                    job_status = status_response.json()

                    status = job_status["status"]
                    progress = job_status.get("progress", 0)
                    message = job_status.get("message", "")

                    # 진행 상황이 변경된 경우에만 출력
                    if progress != prev_progress:
                        print(f"  - 진행: {progress}% - {message}")
                        prev_progress = progress

                    # 완료 또는 실패 시 종료
                    if status in ["completed", "failed"]:
                        if status == "completed":
                            print("\n✅ 앱 생성 성공!")
                            print(f"생성된 파일: {len(job_status.get('artifacts', []))}개")
                            print(f"다운로드 명령: python -m src.cli.client download --job-id {job_id} --output ./output")
                        else:
                            print("\n❌ 앱 생성 실패!")
                            print(f"오류 메시지: {message}")
                        break

                    # 잠시 대기
                    await httpx.AsyncClient().sleep(1)

                except KeyboardInterrupt:
                    print("\n작업 모니터링 중단됨")
                    break
                except Exception as e:
                    print(f"상태 조회 중 오류 발생: {str(e)}")
                    await httpx.AsyncClient().sleep(2)

            return True

    except FileNotFoundError:
        cli_logger.error(f"앱 명세 파일을 찾을 수 없음: {spec_file}")
        print(f"오류: 앱 명세 파일을 찾을 수 없습니다: {spec_file}")
        return False
    except json.JSONDecodeError:
        cli_logger.error(f"앱 명세 파일 형식 오류: {spec_file}")
        print(f"오류: 앱 명세 파일이 올바른 JSON 형식이 아닙니다: {spec_file}")
        return False
    except Exception as e:
        cli_logger.error(f"앱 생성 요청 중 오류 발생: {str(e)}")
        print(f"오류: {str(e)}")
        return False


async def download_app(job_id: str, output_dir: str):
    """
    생성된 앱을 다운로드합니다.

    Args:
        job_id: 작업 ID
        output_dir: 출력 디렉토리
    """
    try:
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)

        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # 작업 상태 확인
            response = await client.get(f"/job/{job_id}")
            response.raise_for_status()
            job_data = response.json()

            if job_data["status"] != "completed":
                print(f"오류: 작업이 완료되지 않았습니다. 현재 상태: {job_data['status']}")
                return False

            print(f"ZIP 파일 다운로드 중...")

            # ZIP 파일 다운로드
            download_response = await client.get(
                f"/download_zip/{job_id}",
                follow_redirects=True
            )
            download_response.raise_for_status()

            # 앱 이름 가져오기
            app_name = "flutter_app"
            if job_data.get("app_spec") and job_data["app_spec"].get("app_name"):
                app_name = job_data["app_spec"]["app_name"]

            # 파일 저장
            output_path = os.path.join(output_dir, f"{app_name}.zip")
            with open(output_path, "wb") as f:
                f.write(download_response.content)

            print(f"다운로드 완료: {output_path}")

            return True
    except Exception as e:
        cli_logger.error(f"앱 다운로드 중 오류 발생: {str(e)}")
        print(f"오류: {str(e)}")
        return False


def main():
    """
    메인 함수.
    """
    import asyncio

    args = parse_args()

    if args.command == "status":
        asyncio.run(get_server_status())
    elif args.command == "list":
        asyncio.run(list_jobs())
    elif args.command == "show":
        asyncio.run(show_job(args.job_id))
    elif args.command == "create":
        asyncio.run(create_app(args.spec))
    elif args.command == "download":
        asyncio.run(download_app(args.job_id, args.output))
    else:
        print("유효한 명령을 입력하세요. 도움말을 보려면 --help를 사용하세요.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Agent of Flutter - 메인 실행 스크립트

Flutter 애플리케이션 생성 API 서버를 시작하거나 CLI 클라이언트를 실행합니다.
"""
import argparse
import sys
import asyncio
from src.api.app import start_server
from src.utils.logger import setup_logger
from src.cli.client import (
    get_server_status, list_jobs, show_job, create_app, download_app
)

# 메인 로거 설정
logger = setup_logger("main")


def main():
    """
    메인 함수: 명령줄 인자를 파싱하고 적절한 작업을 실행합니다.
    """
    parser = argparse.ArgumentParser(
        description="Agent of Flutter - ADK 기반 Flutter 앱 생성기"
    )

    # 서브명령 그룹 생성
    subparsers = parser.add_subparsers(dest="command", help="명령")

    # 'server' 명령
    subparsers.add_parser(
        "server", help="API 서버 시작"
    )

    # 'status' 명령
    subparsers.add_parser(
        "status", help="서버 상태 확인"
    )

    # 'list' 명령
    subparsers.add_parser(
        "list", help="모든 작업 목록 조회"
    )

    # 'show' 명령
    show_parser = subparsers.add_parser(
        "show", help="특정 작업 상태 조회"
    )
    show_parser.add_argument(
        "--job-id", "-j", required=True,
        help="조회할 작업 ID"
    )

    # 'create' 명령
    create_parser = subparsers.add_parser(
        "create", help="새로운 Flutter 앱 생성"
    )
    create_parser.add_argument(
        "--spec", "-s", required=True,
        help="앱 명세 JSON 파일 경로"
    )

    # 'download' 명령
    download_parser = subparsers.add_parser(
        "download", help="생성된 앱 다운로드"
    )
    download_parser.add_argument(
        "--job-id", "-j", required=True,
        help="다운로드할 작업 ID"
    )
    download_parser.add_argument(
        "--output", "-o", default="./output",
        help="출력 디렉토리 (기본값: ./output)"
    )

    # 이전 형식의 인자도 지원
    parser.add_argument(
        "--server", action="store_true",
        help="API 서버 시작(이전 형식)"
    )

    args = parser.parse_args()

    if args.command == "server" or args.server:
        logger.info("API 서버 모드로 시작합니다.")
        start_server()
    elif args.command == "status":
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
        # 기본적으로 서버 시작
        logger.info("기본 모드로 API 서버를 시작합니다.")
        start_server()

    return 0


if __name__ == "__main__":
    sys.exit(main())

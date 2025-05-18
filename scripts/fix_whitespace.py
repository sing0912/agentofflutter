#!/usr/bin/env python3
"""
프로젝트 내 Python 파일의 Whitespace 이슈를 수정하는 스크립트.

이 스크립트는 다음과 같은 whitespace 이슈를 수정합니다:
1. 줄 끝 공백 제거
2. 파일 끝 공백 줄 제거
3. 탭 문자를 4개의 공백으로 변환
"""
import os
import re
import sys
from pathlib import Path


def fix_whitespace_issues(file_path: str) -> bool:
    """
    주어진 파일의 whitespace 이슈를 수정합니다.

    Args:
        file_path: 수정할 파일 경로

    Returns:
        수정 여부 (True: 수정됨, False: 수정되지 않음)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 원본 내용 백업
    original_content = content

    # 1. 줄 끝 공백 제거
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)

    # 2. 파일 끝 불필요한 빈 줄 제거
    content = re.sub(r'\n+$', '\n', content)

    # 3. 탭 문자를 4개의 공백으로 변환
    content = content.replace('\t', '    ')

    # 변경 사항이 있는 경우에만 파일을 다시 씀
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    return False


def find_python_files(directory: str) -> list:
    """
    주어진 디렉토리 내의 모든 Python 파일을 찾습니다.

    Args:
        directory: 탐색할 디렉토리 경로

    Returns:
        Python 파일 경로 목록
    """
    python_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    return python_files


def main():
    """
    메인 실행 함수.
    """
    # 현재 디렉토리 또는 명령줄 인자로 주어진 디렉토리
    directory = '.' if len(sys.argv) < 2 else sys.argv[1]

    # Python 파일 찾기
    python_files = find_python_files(directory)
    print(f"총 {len(python_files)}개의 Python 파일을 찾았습니다.")

    # 각 파일의 whitespace 이슈 수정
    fixed_files = 0
    for file_path in python_files:
        if fix_whitespace_issues(file_path):
            print(f"수정됨: {file_path}")
            fixed_files += 1

    print(f"총 {fixed_files}개 파일의 whitespace 이슈를 수정했습니다.")


if __name__ == "__main__":
    main()
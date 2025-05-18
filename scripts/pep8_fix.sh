#!/bin/bash

# PEP8 규칙 적용 스크립트
# 작성자: 에이전트 오브 플러터 개발팀
# 설명: 프로젝트 내 모든 Python 파일에 PEP8 규칙을 적용합니다.

echo "============================================"
echo "PEP8 규칙 적용 시작..."
echo "============================================"

# 변수 정의
MAX_LINE_LENGTH=79
COUNT=0

# src 디렉토리 내 모든 Python 파일 리스트 생성
FILES=$(find src -name "*.py")

# 파일별 포맷팅 적용
for file in $FILES; do
    echo "포맷팅 중: $file"
    # 두 번의 --aggressive 옵션으로 더 강력한 포맷팅 적용
    autopep8 --in-place --aggressive --aggressive --max-line-length=$MAX_LINE_LENGTH "$file"
    COUNT=$((COUNT+1))
done

# 메인 파일 포맷팅
echo "포맷팅 중: main.py"
autopep8 --in-place --aggressive --aggressive --max-line-length=$MAX_LINE_LENGTH main.py

# 완료 메시지
echo "============================================"
echo "PEP8 규칙 적용 완료!"
echo "적용된 파일 수: $COUNT + 1(main.py)"
echo "============================================"

#!/bin/bash

# 더 강력한 PEP8 규칙 적용 스크립트
# 작성자: 에이전트 오브 플러터 개발팀
# 설명: 프로젝트 내 모든 Python 파일에 강력한 PEP8 규칙을 적용합니다.

echo "============================================"
echo "강력한 PEP8 규칙 적용 시작..."
echo "============================================"

# 변수 정의
MAX_LINE_LENGTH=79

# 특정 문제 파일들 직접 처리
FILES_WITH_ISSUES=(
    "src/agents/main_orchestrator_agent.py"
)

# 문제 파일들에 더 강력한 포맷팅 적용
for file in "${FILES_WITH_ISSUES[@]}"; do
    echo "강력한 포맷팅 적용 중: $file"
    # 세 번의 --aggressive 옵션과 최대 라인 길이를 더 작게 설정
    autopep8 --in-place --aggressive --aggressive --aggressive --max-line-length=78 "$file"
    # 추가로 긴 import 문을 여러 줄로 분리
    sed -i '' 's/from \(.*\) import \(.*\),\(.*\)/from \1 import \2,\\\n    \3/g' "$file"
done

echo "============================================"
echo "강력한 PEP8 규칙 적용 완료!"
echo "============================================" 
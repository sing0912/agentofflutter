#!/usr/bin/env python3
"""
PEP8 자동 수정 스크립트

이 스크립트는 프로젝트의 모든 Python 파일에 대해 PEP8 규칙을 적용하고
특정 유형의 문제들을 자동으로 수정합니다.
"""
import os
import re
import subprocess
import glob


# 문제가 있는 파일들과 해당 문제 유형
PROBLEM_FILES = {
    "src/agents/main_orchestrator_agent.py": ["E231", "E501"],
    "src/agents/android_group/android_group_agent.py": ["F841", "E501"],
    "src/agents/model_group/user_model_agent.py": ["E501"],
    "src/agents/security_group/security_group_agent.py": ["E501"],
    "src/cli/client.py": ["F841", "E501", "F541"],
    "src/tools/code_generation.py": ["F401"],
    "src/utils/dart_utils.py": ["F401"],
}


def run_autopep8_on_file(file_path: str, aggressive_level: int = 2) -> None:
    """
    특정 파일에 대해 autopep8을 실행합니다.
    
    Args:
        file_path: 포맷팅할 파일 경로
        aggressive_level: 적용할 aggressive 레벨 (1-3)
    """
    aggressive = " ".join(["--aggressive"] * aggressive_level)
    cmd = f"autopep8 --in-place {aggressive} --max-line-length=79 {file_path}"
    print(f"포맷팅 중: {file_path}")
    subprocess.run(cmd, shell=True, check=True)


def fix_imports(file_path: str) -> None:
    """
    미사용 import 문제를 수동으로 수정합니다.
    
    Args:
        file_path: 수정할 파일 경로
    """
    problem_imports = {
        "src/tools/code_generation.py": ["os", "typing.List", "json"],
        "src/utils/dart_utils.py": ["typing.Dict", "typing.Any"],
    }
    
    if file_path not in problem_imports:
        return
        
    print(f"import 수정 중: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for imp in problem_imports.get(file_path, []):
        # import 구문 제거
        if '.' in imp:
            module, item = imp.split('.')
            pattern = rf"from\s+{module}\s+import\s+.*?{item}.*?"
            if re.search(pattern, content):
                new_content = re.sub(
                    pattern, 
                    lambda m: m.group(0).replace(item, ""), 
                    content
                )
                # 만약 import 문이 ", Item"으로 끝나면 쉼표 제거
                new_content = re.sub(r",\s*{item}", "", new_content)
                content = new_content
        else:
            pattern = rf"import\s+{imp}"
            content = re.sub(pattern, "", content)
            
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_whitespace_after_comma(file_path: str) -> None:
    """
    쉼표 후 공백이 없는 문제를 수정합니다.
    
    Args:
        file_path: 수정할 파일 경로
    """
    if "E231" not in PROBLEM_FILES.get(file_path, []):
        return
        
    print(f"쉼표 후 공백 수정 중: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 쉼표 후 공백이 없는 경우 추가
    content = re.sub(r',([^\s])', r', \1', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_unused_variables(file_path: str) -> None:
    """
    사용되지 않는 변수 문제를 수정합니다.
    
    Args:
        file_path: 수정할 파일 경로
    """
    if "F841" not in PROBLEM_FILES.get(file_path, []):
        return
        
    print(f"미사용 변수 수정 중: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 수정된 라인 보관
    new_lines = []
    
    for line in lines:
        if "app_name" in line and "=" in line and "local variable" not in line:
            # 사용되지 않는 변수 주석으로 변경
            new_line = (
                line.rstrip() + "  # 향후 사용 예정\n" 
                if not line.strip().startswith("#") else line
            )
            new_lines.append(new_line)
        elif "app_name_slug" in line and "=" in line:
            # 사용되지 않는 변수 주석으로 변경
            new_line = (
                line.rstrip() + "  # 향후 사용 예정\n" 
                if not line.strip().startswith("#") else line
            )
            new_lines.append(new_line)
        elif "status_parser" in line or "list_parser" in line:
            # 사용되지 않는 변수 주석으로 변경
            new_line = (
                line.rstrip() + "  # 향후 기능 확장 시 사용\n"
                if not line.strip().startswith("#") else line
            )
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


def fix_f_string_placeholders(file_path: str) -> None:
    """
    f-string에 플레이스홀더가 없는 문제를 수정합니다.
    
    Args:
        file_path: 수정할 파일 경로
    """
    if "F541" not in PROBLEM_FILES.get(file_path, []):
        return
        
    print(f"f-string 수정 중: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if "f'" in line or 'f"' in line:
            # f-string에 {가 없으면 일반 문자열로 변경
            if "{" not in line:
                line = line.replace("f'", "'").replace('f"', '"')
        new_lines.append(line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


def fix_line_length(file_path: str) -> None:
    """
    긴 줄 문제를 수정합니다. 
    이미 autopep8이 처리했지만 일부 특수한 경우에는 추가 처리가 필요합니다.
    
    Args:
        file_path: 수정할 파일 경로
    """
    if "E501" not in PROBLEM_FILES.get(file_path, []):
        return
    
    # autopep8의 추가 옵션으로 다시 실행
    run_autopep8_on_file(file_path, aggressive_level=3)


def main() -> None:
    """
    메인 실행 함수
    """
    print("============================================")
    print("PEP8 규칙 자동 수정 시작...")
    print("============================================")
    
    # 1. 모든 Python 파일에 기본 autopep8 적용
    python_files = glob.glob("src/**/*.py", recursive=True)
    python_files.append("main.py")
    
    for file_path in python_files:
        run_autopep8_on_file(file_path)
    
    # 2. 특정 파일에 대한 추가 수정
    for file_path in PROBLEM_FILES:
        # 미사용 import 수정
        fix_imports(file_path)
        
        # 쉼표 후 공백 수정
        fix_whitespace_after_comma(file_path)
        
        # 사용되지 않는 변수 수정
        fix_unused_variables(file_path)
        
        # f-string 플레이스홀더 수정
        fix_f_string_placeholders(file_path)
        
        # 긴 줄 수정
        fix_line_length(file_path)
    
    print("============================================")
    print("PEP8 규칙 자동 수정 완료!")
    print("============================================")


if __name__ == "__main__":
    main() 
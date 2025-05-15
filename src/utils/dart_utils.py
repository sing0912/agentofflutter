"""
Dart 코드 생성 관련 유틸리티 함수들.
"""
import re
from typing import List, Optional


def sanitize_dart_class_name(name: str) -> str:
    """
    문자열을 Dart 클래스 이름 규칙에 맞게 변환합니다.

    Args:
        name: 변환할 이름

    Returns:
        Dart 클래스 이름 규칙에 맞는 문자열
    """
    # 공백과 특수문자를 밑줄로 변환
    result = re.sub(r'[^a-zA-Z0-9]', '_', name)

    # 숫자로 시작하면 앞에 밑줄 추가
    if result and result[0].isdigit():
        result = f"_{result}"

    # 첫 글자를 대문자로 변환
    if result:
        result = result[0].upper() + result[1:]

    # 카멜 케이스로 변환 (밑줄 뒤 문자를 대문자로)
    parts = result.split('_')
    result = parts[0] + ''.join(p.capitalize() for p in parts[1:] if p)

    return result


def sanitize_dart_variable_name(name: str) -> str:
    """
    문자열을 Dart 변수명 규칙에 맞게 변환합니다.

    Args:
        name: 변환할 이름

    Returns:
        Dart 변수명 규칙에 맞는 문자열
    """
    # 공백과 특수문자를 밑줄로 변환
    result = re.sub(r'[^a-zA-Z0-9]', '_', name)

    # 숫자로 시작하면 앞에 밑줄 추가
    if result and result[0].isdigit():
        result = f"_{result}"

    # 첫 글자를 소문자로 변환
    if result:
        result = result[0].lower() + result[1:]

    # 카멜 케이스로 변환 (밑줄 뒤 문자를 대문자로)
    parts = result.split('_')
    result = parts[0] + ''.join(p.capitalize() for p in parts[1:] if p)

    return result


def dart_type_from_python(py_type: str) -> str:
    """
    Python 타입명을 Dart 타입명으로 변환합니다.

    Args:
        py_type: Python 타입명

    Returns:
        Dart 타입명
    """
    type_map = {
        "str": "String",
        "int": "int",
        "float": "double",
        "bool": "bool",
        "list": "List",
        "dict": "Map<String, dynamic>",
        "None": "void",
        "any": "dynamic",
        "datetime": "DateTime",
        "date": "DateTime",
    }

    # 리스트 타입 처리 (예: List[str] -> List<String>)
    list_match = re.match(r'list\[(\w+)\]', py_type.lower())
    if list_match:
        inner_type = list_match.group(1)
        return f"List<{dart_type_from_python(inner_type)}>"

    # 딕셔너리 타입 처리
    dict_match = re.match(r'dict\[(\w+),\s*(\w+)\]', py_type.lower())
    if dict_match:
        key_type = dict_match.group(1)
        value_type = dict_match.group(2)
        return f"Map<{
            dart_type_from_python(key_type)}, {
            dart_type_from_python(value_type)}>"

    return type_map.get(py_type.lower(), "dynamic")


def generate_dart_imports(dependencies: List[str],
                          dart_package_name: Optional[str] = None) -> str:
    """
    Dart import 구문을 생성합니다.

    Args:
        dependencies: 의존성 패키지/파일 목록
        dart_package_name: 현재 Dart 패키지 이름 (선택사항)

    Returns:
        Import 구문 문자열
    """
    imports = []

    # Flutter/Dart 기본 패키지
    std_packages = {
        "flutter": "package:flutter/material.dart",
        "flutter_widgets": "package:flutter/widgets.dart",
        "http": "package:http/http.dart",
        "flutter_test": "package:flutter_test/flutter_test.dart",
        "provider": "package:provider/provider.dart",
        "json_annotation": "package:json_annotation/json_annotation.dart",
    }

    for dep in dependencies:
        if dep in std_packages:
            imports.append(f"import '{std_packages[dep]}';")
        elif dep.startswith("package:"):
            imports.append(f"import '{dep}';")
        elif dep.endswith(".dart"):
            if dart_package_name and not dep.startswith("package:"):
                imports.append(f"import 'package:{dart_package_name}/{dep}';")
            else:
                imports.append(f"import '{dep}';")
        else:
            # 확장자가 없는 내부 파일의 경우
            imports.append(f"import '{dep}.dart';")

    return "\n".join(imports)

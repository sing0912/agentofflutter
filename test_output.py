#!/usr/bin/env python3
"""
출력 디렉토리에 파일을 생성할 수 있는지 확인하는 테스트 스크립트
"""
import os
import uuid
import json

# 출력 디렉토리 설정
OUTPUT_DIR = "./output"

def main():
    """테스트 파일 생성 함수"""
    print(f"출력 디렉토리: {OUTPUT_DIR}")
    
    # 출력 디렉토리가 없으면 생성
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"디렉토리 존재 여부: {os.path.exists(OUTPUT_DIR)}")
    
    # 고유 작업 ID 생성
    job_id = str(uuid.uuid4())
    print(f"작업 ID: {job_id}")
    
    # 작업별 디렉토리 생성
    job_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    print(f"작업 디렉토리: {job_dir}")
    
    # 테스트 파일 생성
    test_file_path = os.path.join(job_dir, "test.txt")
    with open(test_file_path, "w") as f:
        f.write("테스트 파일 내용")
    
    print(f"테스트 파일 생성: {test_file_path}")
    print(f"파일 존재 여부: {os.path.exists(test_file_path)}")
    
    # 테스트 Flutter 파일 생성
    flutter_dir = os.path.join(job_dir, "lib")
    os.makedirs(flutter_dir, exist_ok=True)
    
    main_dart_path = os.path.join(flutter_dir, "main.dart")
    with open(main_dart_path, "w") as f:
        f.write("""
import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Test App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: const MyHomePage(),
    );
  }
}

class MyHomePage extends StatelessWidget {
  const MyHomePage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Test App'),
      ),
      body: const Center(
        child: Text('Hello, World!'),
      ),
    );
  }
}
""")
    
    print(f"Flutter 메인 파일 생성: {main_dart_path}")
    print(f"파일 존재 여부: {os.path.exists(main_dart_path)}")
    
    # 출력 디렉토리 내용 확인
    print("\n출력 디렉토리 내용:")
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for file in files:
            print(f" - {os.path.join(root, file)}")
    
    return 0

if __name__ == "__main__":
    main() 
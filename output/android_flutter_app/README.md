# 안드로이드 플러터 앱

Flutter로 개발된 안드로이드 앱입니다.

## 기능

- 사용자 인증 (로그인/로그아웃)
- 프로필 관리
- 로컬 데이터 저장 (SharedPreferences)

## 기술 스택

- Flutter SDK
- Provider (상태 관리)
- SharedPreferences (로컬 데이터 저장)
- Material Design 3

## 설치 및 실행 방법

1. Flutter SDK 설치
   - [Flutter 공식 사이트](https://flutter.dev/docs/get-started/install)에서 SDK 설치

2. 의존성 패키지 설치
   ```bash
   flutter pub get
   ```

3. 앱 실행
   ```bash
   flutter run
   ```

4. 테스트 계정
   - 이메일: test@example.com
   - 비밀번호: password

## 프로젝트 구조

```
lib/
├── models/          # 데이터 모델
├── controllers/     # 비즈니스 로직 및 상태 관리
├── pages/           # UI 화면
├── utils/           # 유틸리티 함수
└── widgets/         # 재사용 가능한 위젯
```

## 안드로이드 빌드

안드로이드 APK 빌드 방법:

```bash
flutter build apk
```

앱 번들 빌드 방법:

```bash
flutter build appbundle
``` 
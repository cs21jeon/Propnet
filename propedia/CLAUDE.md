# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Propedia (부동산백과) is a Flutter real estate encyclopedia app targeting multiple platforms (Android, iOS, Web, Windows, macOS, Linux).

## Build and Development Commands

```bash
# Get dependencies
flutter pub get

# Run code generators (freezed, json_serializable, retrofit, riverpod, isar)
dart run build_runner build --delete-conflicting-outputs

# Watch mode for code generation during development
dart run build_runner watch --delete-conflicting-outputs

# Run the app
flutter run

# Run on specific device
flutter run -d windows
flutter run -d chrome
flutter run -d android

# Analyze code
flutter analyze

# Run tests
flutter test

# Run a single test file
flutter test test/widget_test.dart
```

## Architecture

The project follows **Clean Architecture** with the following layer structure:

```
lib/
├── main.dart              # Entry point with ProviderScope
├── app.dart               # Root MaterialApp with theme configuration
├── core/                  # Framework-level utilities
│   ├── constants/         # App-wide colors (AppColors), typography (AppTextStyles)
│   ├── network/           # Dio/Retrofit network configuration
│   ├── router/            # go_router configuration
│   └── utils/             # Utility functions
├── data/                  # Data layer
│   ├── datasources/       # Remote (API) and local (Isar) data sources
│   ├── dto/               # Data Transfer Objects for API
│   ├── models/            # Isar database models
│   └── repositories/      # Repository implementations
├── domain/                # Domain layer (business logic)
│   ├── entities/          # Business entities (freezed)
│   ├── repositories/      # Repository interfaces (abstract classes)
│   └── usecases/          # Use case classes
├── presentation/          # UI layer
│   ├── providers/         # Riverpod providers
│   ├── screens/           # Feature screens (auth, home, search, result, favorites, history, profile)
│   └── widgets/           # Reusable widgets (building, common, property)
└── shared/                # Cross-cutting concerns
    ├── extensions/        # Dart extension methods
    └── theme/             # AppTheme (light/dark Material3 themes)
```

## Key Technologies

- **State Management**: Riverpod with code generation (`@riverpod` annotations)
- **Networking**: Dio + Retrofit with generated API clients
- **Local Storage**: Isar database (generated models), SharedPreferences, FlutterSecureStorage
- **Routing**: go_router for declarative navigation
- **Data Classes**: Freezed for immutable models with JSON serialization
- **Maps**: Kakao Map Plugin with Geolocator for location services

## Code Generation

This project heavily relies on code generation. After modifying files with:
- `@freezed` annotations (entities, DTOs)
- `@riverpod` annotations (providers)
- `@RestApi` annotations (Retrofit clients)
- `@Collection` annotations (Isar models)

Run `dart run build_runner build --delete-conflicting-outputs` to regenerate `.g.dart` and `.freezed.dart` files.

## Design System

- Colors defined in `lib/core/constants/app_colors.dart`
- Typography defined in `lib/core/constants/app_text_styles.dart`
- Complete light/dark themes in `lib/shared/theme/app_theme.dart`
- Uses Material 3 design system

## Release Workflow

업데이트/릴리즈 시 다음 단계를 따릅니다:

### 슬래시 명령어
- `/release` - 전체 릴리즈 워크플로우 (테스트 → 빌드 → 커밋)
- `/test` - 코드 분석, 보안 검사 및 API 테스트
- `/build` - APK/AAB 빌드
- `/deploy` - 서버 배포

### 릴리즈 프로세스
1. 코드 수정 완료
2. `/test` 실행 (코드 분석 + 보안 검사 + API 테스트)
3. 오류/취약점 있으면 수정 후 재테스트
4. `docs/progress_development.md` 변경 이력 업데이트
5. `pubspec.yaml` 버전 업데이트
6. `/build` 실행하여 APK/AAB 생성
7. 커밋 및 푸시
8. (필요시) `/deploy`로 서버 배포

### 버전 관리
- 버전 형식: `X.Y.Z+N` (Major.Minor.Patch+BuildNumber)
- 빌드 번호는 Play Store 업로드마다 증가
- 변경 이력: `docs/progress_development.md`

### 빌드 파일 위치
- APK: `build/app/outputs/flutter-apk/app-release.apk`
- AAB: `build/app/outputs/bundle/release/app-release.aab`

## Blog Writing

블로그 글 작성 요청 시 반드시 `blog_sample/my-writing-style.md` 문체 가이드를 참고합니다.
- 문체 가이드 위치: `blog_sample/my-writing-style.md`
- 블로그 콘텐츠 위치: `marketing/blog-content/`
- 발행은 Playwright MCP를 통해 네이버 블로그에 진행
- 카테고리: 게시판(1), 부동산 상식(2), 활용 팁(3), 서비스 가이드(4), 부동산 데이터(5), PropTech 이야기(6)

## Server Information

- **Host**: `root@175.119.224.71`
- **Web App**: `/home/webapp/goldenrabbit`
- **MCP Config**: `.mcp.json`
- **API Base**: `https://goldenrabbit.biz/app/api/`

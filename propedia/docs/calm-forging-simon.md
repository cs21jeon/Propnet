# Propedia (부동산백과) Flutter 앱 마이그레이션 계획

## Context (배경)

현재 GoldenRabbit 부동산 정보 시스템을 **Propedia (부동산백과)** 라는 이름의 Flutter 앱으로 마이그레이션합니다. 기존 시스템은 정적 HTML/CSS/JavaScript 프론트엔드와 Flask 백엔드로 구성되어 있으며, 이를 크로스 플랫폼 모바일 앱으로 전환하여 다음 목표를 달성하고자 합니다:

### 마이그레이션 이유
1. **모바일 네이티브 경험 제공**: Android/iOS 앱스토어 배포를 통한 접근성 향상
2. **크로스 플랫폼 개발**: 단일 코드베이스로 Android, iOS, Web 지원
3. **향상된 사용자 경험**: 네이티브 성능, 오프라인 지원, 푸시 알림 등
4. **유지보수 효율성**: 기존 HTML/JS 파편화된 구조를 Flutter의 위젯 기반 구조로 통합

### 프로젝트 범위
- **타겟 플랫폼**: Android, iOS, Flutter Web (모두)
- **마이그레이션 범위**: 사용자 기능 전체 (어드민 기능은 기존 웹 유지)
- **우선순위**: **건축물 조회 앱** 기능 먼저 개발 (`/app/` 디렉토리 기능)
- **예상 기간**: 12-14주

### 현재 시스템 구조

**프론트엔드 (2개 인터페이스)**:
1. 메인 사이트 (`/index.html` 등): 금토끼부동산 매물 정보 조회
2. 건축물 조회 앱 (`/app/` 디렉토리): 도로명/지번/지도 검색 기능

**백엔드**:
- API Server (8000): 공개 매물 API
- Property Manager (5000): 건축물 검색 API + JWT 인증

---

## 권장 접근 방식

### 아키텍처

**Clean Architecture + MVVM + Riverpod**를 채택합니다:

```
lib/
├── core/                   # 네트워크, 라우팅, 유틸리티
├── data/                   # 모델, Repository 구현, API
├── domain/                 # 비즈니스 로직 (선택적)
├── presentation/           # UI, 화면, 위젯, Provider
└── shared/                 # 테마, 확장 함수
```

**레이어 분리**:
- Presentation (UI) → Provider (상태 관리) → Repository → API
- 각 레이어는 독립적으로 테스트 가능
- 의존성 주입은 Riverpod으로 자동 처리

### 상태 관리: Riverpod 2.0+

- **FutureProvider**: 단순 API 호출 (매물 목록 등)
- **StateNotifier**: 복잡한 상태 (검색, 필터링)
- **StateProvider**: 간단한 UI 상태 (탭 인덱스, 다크모드)
- **StreamProvider**: 실시간 데이터 (검색 기록 감시)

### 네트워크: Dio + Retrofit

- `ApiClient`: Dio 기반 HTTP 클라이언트
- `AuthInterceptor`: JWT 토큰 자동 추가 및 갱신
- 에러 핸들링: 네트워크, 인증, 서버 오류 분리

### 지도 기능: 카카오맵

- Android/iOS: `kakao_map_plugin`
- Web: `HtmlElementView`로 기존 HTML 재사용
- Native App Key는 환경설정 파일에서 확인 가능

### 로컬 데이터베이스: Isar

- 검색 기록, 즐겨찾기 저장
- SQLite보다 빠르고 타입 안전함
- Stream으로 실시간 UI 업데이트

### 보안

- JWT 토큰: `flutter_secure_storage`로 암호화 저장
- API 키: 환경 변수 관리
- HTTPS 통신 기본 설정

---

## 단계별 마이그레이션 계획 (우선순위 반영)

### Phase 1: 프로젝트 초기화 및 인프라 구축 (1주)

**작업 내용**:
1. Flutter 프로젝트 생성: `flutter create propedia`
2. 필수 패키지 설치 (pubspec.yaml)
3. 폴더 구조 생성 (core, data, presentation 등)
4. 테마 설정 (Tailwind CSS → Flutter 변환)
5. ApiClient, AuthInterceptor 구현
6. go_router 라우팅 설정

**검증**: 빈 화면이지만 앱 실행 및 네비게이션 작동 확인

---

### Phase 2: 인증 시스템 구현 (1주)

**작업 내용**:
1. User 모델, Auth DTO 정의
2. AuthRepository + AuthApi 구현
3. JWT 토큰 저장/불러오기 (SecureStorage)
4. AuthProvider (Riverpod)
5. LoginScreen, RegisterScreen UI
6. 자동 로그인 처리

**API 연동**:
- `POST /app/api/auth/register`
- `POST /app/api/auth/login`
- `POST /app/api/auth/refresh`

**검증**: 회원가입 → 로그인 → 앱 재시작 → 자동 로그인

---

### Phase 3: 건축물 검색 기능 (도로명/지번) (2주)

**우선순위 1 - 핵심 기능**

**작업 내용**:
1. Building, Land 모델 정의
2. BuildingRepository + BuildingApi 구현
3. SearchProvider (StateNotifier)
4. SearchMethodScreen (검색 방식 선택)
5. SearchRoadScreen (도로명 검색)
6. SearchJibunScreen (지번 검색 + 법정동 자동완성)
7. ResultScreen (검색 결과 상세 표시)

**API 연동**:
- `POST /app/api/search/road` - 도로명 검색
- `POST /app/api/search/jibun` - 지번 검색
- `GET /app/api/bjdong/search?query=...` - 법정동 자동완성

**주요 기능**:
- 층별 정보 표시
- 토지 특성 정보
- 대지지분 계산 표시
- PDF 다운로드 (선택적)

**검증**: 도로명/지번 검색 → 건축물 정보 표시 → 토지 정보 확인

---

### Phase 4: 지도 검색 기능 (2주)

**우선순위 2**

**작업 내용**:
1. 카카오맵 SDK 설정 (Android/iOS)
2. SearchMapScreen 구현
3. 좌표 클릭 → 지번 변환
4. 필지 경계 표시 (GeoJSON → Polygon)
5. Flutter Web: HtmlElementView로 기존 HTML 재사용

**API 연동**:
- `POST /app/api/map/click-jibun` - 좌표 → 지번 변환
- `GET /app/api/map/parcel-boundary?pnu=...` - 필지 경계

**검증**: 지도 로드 → 클릭 → 지번 표시 → 필지 경계 표시 → 검색

---

### Phase 5: 검색 기록 및 즐겨찾기 (1주)

**작업 내용**:
1. Isar 데이터베이스 초기화
2. SearchHistory, Favorite 스키마 정의
3. DatabaseService 구현
4. HistoryScreen (검색 기록 목록)
5. FavoritesScreen (즐겨찾기 목록)
6. 서버 동기화 (선택적)

**API 연동**:
- `GET /app/api/user/search-history`
- `POST /app/api/user/favorites`
- `DELETE /app/api/user/favorites/{id}`

**검증**: 검색 → 기록 저장 → 기록 목록 표시 → 삭제 → 즐겨찾기 추가

---

### Phase 6: 프로필 및 설정 (1주)

**작업 내용**:
1. ProfileScreen UI
2. 다크모드 토글 (ThemeMode Provider)
3. 사용 통계 표시
4. 로그아웃

**API 연동**:
- `GET /app/api/user/usage-stats`

**검증**: 프로필 확인 → 다크모드 전환 → 사용 통계 표시 → 로그아웃

---

### Phase 7: 매물 정보 조회 (메인 사이트 기능) (2주)

**우선순위 3 - 건축물 앱 완성 후 진행**

**작업 내용**:
1. Property 모델 정의
2. PropertyRepository + PropertyApi 구현
3. HomeScreen (매물 검색 인터페이스)
4. PropertyListView (카테고리별 매물 목록)
5. PropertyCard 위젯
6. PropertyDetailScreen (매물 상세)
7. 조건 검색 (매가, 수익률, 면적 등)

**API 연동**:
- `GET /api/property-list`
- `GET /api/category-properties?view=...`
- `GET /api/property-detail?id=...`
- `POST /property-manager/api/search-map`

**검증**: 매물 목록 로드 → 카테고리 필터 → 상세 보기 → 조건 검색

---

### Phase 8: 매물 지도 표시 (1주)

**작업 내용**:
1. 카카오맵에 매물 마커 표시
2. 마커 클릭 → 매물 상세 모달
3. coordinates.json 캐시 활용

**검증**: 지도에 279개 매물 표시 → 마커 클릭 → 상세 정보

---

### Phase 9: Flutter Web 빌드 및 배포 (1주)

**작업 내용**:
1. 반응형 디자인 검증
2. Web 빌드 최적화 (CanvasKit vs HTML)
3. PWA 설정 (manifest.json)
4. Nginx 설정 (`/flutter-app/` 경로)

**배포**:
```bash
flutter build web --release --web-renderer html
sudo cp -r build/web/* /home/webapp/goldenrabbit/frontend/public/flutter-app/
sudo systemctl reload nginx
```

**검증**: https://goldenrabbit.biz/flutter-app/ 접속 확인

---

### Phase 10: 모바일 앱 빌드 및 배포 (2주)

**Android**:
1. 서명 키 생성
2. Play Console 앱 등록
3. AAB 빌드: `flutter build appbundle --release`
4. 내부 테스트 → 프로덕션 배포

**iOS**:
1. Apple Developer 설정
2. 프로비저닝 프로파일
3. IPA 빌드: `flutter build ipa --release`
4. App Store Connect 업로드

**검증**: 각 플랫폼 스토어에서 다운로드 및 실행 확인

---

### Phase 11: 테스트 및 버그 수정 (2주)

**작업 내용**:
1. 유닛 테스트 (Repository, API)
2. 위젯 테스트 (주요 화면)
3. 통합 테스트 (사용자 시나리오)
4. 버그 수정 및 성능 최적화

**검증**: 모든 테스트 통과

---

## 주요 파일 및 경로

### 새로 생성할 Flutter 프로젝트

**프로젝트 루트**: `/home/webapp/goldenrabbit/propedia/`

**핵심 파일**:
- `lib/main.dart` - 앱 진입점
- `lib/core/network/api_client.dart` - Dio HTTP 클라이언트
- `lib/core/network/auth_interceptor.dart` - JWT 인터셉터
- `lib/data/repositories/building_repository.dart` - 건축물 검색 Repository
- `lib/data/datasources/remote/building_api.dart` - 건축물 검색 API
- `lib/presentation/screens/search/search_jibun_screen.dart` - 지번 검색 화면
- `lib/presentation/screens/search/result_screen.dart` - 검색 결과 화면
- `lib/presentation/providers/search_provider.dart` - 검색 상태 관리
- `pubspec.yaml` - 패키지 의존성

### 참조할 기존 파일

**프론트엔드 (UI/UX 참고)**:
- `/home/webapp/goldenrabbit/frontend/public/app/index.html` - 검색 방식 선택 UI
- `/home/webapp/goldenrabbit/frontend/public/app/search-jibun.html` - 지번 검색 UI
- `/home/webapp/goldenrabbit/frontend/public/app/result.html` - 검색 결과 표시 UI
- `/home/webapp/goldenrabbit/frontend/public/app/js/search.js` - API 호출 패턴
- `/home/webapp/goldenrabbit/frontend/public/app/js/map.js` - 지도 기능

**백엔드 (API 스펙 확인)**:
- `/home/webapp/goldenrabbit/backend/property-manager/routes/app_api.py` - 건축물 검색 API 엔드포인트
- `/home/webapp/goldenrabbit/backend/property-manager/routes/app_auth.py` - JWT 인증 API
- `/home/webapp/goldenrabbit/backend/api/app.py` - 매물 API 엔드포인트

**환경 설정**:
- `/home/webapp/goldenrabbit/backend/.env` - 카카오맵 API 키 확인
- `/home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf` - Nginx 설정 참고

---

## 재사용 가능한 백엔드 API

기존 Flask 백엔드 API를 그대로 사용합니다:

### 건축물 검색 API (Port 5000)

```
POST https://goldenrabbit.biz/app/api/search/road
POST https://goldenrabbit.biz/app/api/search/jibun
POST https://goldenrabbit.biz/app/api/search/bdmgtsn
GET  https://goldenrabbit.biz/app/api/bjdong/search?query=사당동
POST https://goldenrabbit.biz/app/api/map/click-jibun
GET  https://goldenrabbit.biz/app/api/map/parcel-boundary?pnu=1159010700103020000
```

### 인증 API (Port 5000)

```
POST https://goldenrabbit.biz/app/api/auth/register
POST https://goldenrabbit.biz/app/api/auth/login
POST https://goldenrabbit.biz/app/api/auth/refresh
GET  https://goldenrabbit.biz/property-manager/check-auth
```

### 사용자 데이터 API (Port 5000)

```
GET  https://goldenrabbit.biz/app/api/user/search-history
POST https://goldenrabbit.biz/app/api/user/favorites
GET  https://goldenrabbit.biz/app/api/user/usage-stats
```

### 매물 API (Port 8000)

```
GET  https://goldenrabbit.biz/api/property-list
GET  https://goldenrabbit.biz/api/category-properties?view=viwXXX
GET  https://goldenrabbit.biz/api/property-detail?id=recXXX
POST https://goldenrabbit.biz/api/submit-inquiry
POST https://goldenrabbit.biz/property-manager/api/search-map
```

---

## 필수 패키지 (pubspec.yaml)

```yaml
name: propedia
description: Propedia - 부동산백과
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  # 상태 관리
  flutter_riverpod: ^2.4.10
  riverpod_annotation: ^2.3.4

  # 네트워크
  dio: ^5.4.0
  retrofit: ^4.0.3

  # 로컬 저장소
  isar: ^3.1.0+1
  isar_flutter_libs: ^3.1.0+1
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0

  # 라우팅
  go_router: ^13.0.0

  # UI
  cached_network_image: ^3.3.1
  flutter_hooks: ^0.20.5
  hooks_riverpod: ^2.4.10
  shimmer: ^3.0.0

  # 지도
  kakao_map_plugin: ^0.4.2
  geolocator: ^11.0.0

  # JSON
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1

  # 유틸리티
  intl: ^0.19.0
  logger: ^2.0.2+1
  flutter_svg: ^2.0.9
  url_launcher: ^6.2.4

dev_dependencies:
  build_runner: ^2.4.8
  freezed: ^2.4.6
  json_serializable: ^6.7.1
  riverpod_generator: ^2.3.11
  isar_generator: ^3.1.0+1
  retrofit_generator: ^8.0.6
  mocktail: ^1.0.3
```

---

## 검증 방법 (End-to-End)

### 건축물 조회 앱 검증 시나리오

1. **회원가입 및 로그인**
   - 앱 실행 → 회원가입 화면
   - 이메일, 비밀번호 입력 → 회원가입 API 호출
   - 자동 로그인 → 홈 화면 이동
   - 토큰이 SecureStorage에 저장되었는지 확인

2. **지번 검색**
   - "지번주소로 검색" 선택
   - 법정동 입력: "사당동" → 자동완성 목록 표시
   - "사당동" 선택 → bjdong_code 자동 입력
   - 본번: "314", 부번: "21" 입력
   - "검색" 버튼 → API 호출 → 로딩 표시
   - 검색 결과 화면에 건축물 정보 표시
   - 층별 정보, 토지 정보 확인

3. **검색 기록 저장 및 조회**
   - 검색 후 자동으로 Isar DB에 저장
   - 하단 탭 "기록" 선택 → 검색 기록 목록 표시
   - 최신순 정렬 확인
   - 기록 클릭 → 상세 정보 다시 표시

4. **즐겨찾기**
   - 검색 결과에서 "즐겨찾기 추가" 버튼
   - 서버 API 호출 + 로컬 DB 저장
   - "즐겨찾기" 탭 → 목록 표시
   - 삭제 기능 확인

5. **지도 검색**
   - "지도에서 검색" 선택
   - 카카오맵 로드 확인
   - 지도 클릭 → 좌표 → 지번 변환 API 호출
   - 지번 표시 → "이 위치 검색" 버튼
   - 검색 결과 표시

6. **프로필 및 설정**
   - "프로필" 탭 → 사용자 정보 표시
   - 다크모드 토글 → 테마 변경 확인
   - 사용 통계 표시 (검색 횟수 등)
   - "로그아웃" → 토큰 삭제 → 로그인 화면 이동

7. **오프라인 지원**
   - 네트워크 끊기
   - 검색 기록 탭 → 로컬 DB에서 로드 확인
   - 즐겨찾기 탭 → 로컬 데이터 표시

8. **앱 재시작**
   - 앱 종료 후 재실행
   - 토큰 유효하면 자동 로그인 확인
   - 검색 기록 유지 확인

---

## 성공 기준

### 기능 요구사항
- ✅ 회원가입, 로그인, 자동 로그인 작동
- ✅ 도로명/지번/지도 검색 모두 작동
- ✅ 검색 결과에 건축물 정보 정확히 표시
- ✅ 검색 기록 저장 및 목록 표시
- ✅ 즐겨찾기 추가/삭제
- ✅ 지도에 좌표 표시 및 필지 경계 표시
- ✅ 다크모드 지원
- ✅ 오프라인에서 기록 조회 가능

### 성능 요구사항
- ✅ API 응답 시간 2초 이내
- ✅ 지도 로딩 3초 이내
- ✅ 60fps 부드러운 스크롤

### 품질 요구사항
- ✅ 유닛 테스트 커버리지 70% 이상
- ✅ 위젯 테스트 주요 화면 모두 통과
- ✅ 통합 테스트 사용자 시나리오 통과
- ✅ 에러 핸들링 완료 (네트워크, 인증, 서버 오류)

### 배포 요구사항
- ✅ Android APK/AAB 빌드 성공
- ✅ iOS IPA 빌드 성공
- ✅ Flutter Web 빌드 및 Nginx 배포 성공
- ✅ 각 플랫폼에서 정상 실행

---

## 예상 타임라인 (14주)

| Phase | 내용 | 기간 | 누적 |
|-------|------|------|------|
| 1 | 프로젝트 초기화 | 1주 | 1주 |
| 2 | 인증 시스템 | 1주 | 2주 |
| 3 | 건축물 검색 (도로명/지번) | 2주 | 4주 |
| 4 | 지도 검색 | 2주 | 6주 |
| 5 | 검색 기록/즐겨찾기 | 1주 | 7주 |
| 6 | 프로필/설정 | 1주 | 8주 |
| 7 | 매물 정보 조회 | 2주 | 10주 |
| 8 | 매물 지도 표시 | 1주 | 11주 |
| 9 | Flutter Web 배포 | 1주 | 12주 |
| 10 | 모바일 앱 배포 | 2주 | 14주 |

**Phase 11 (테스트/버그 수정)**은 각 Phase 중간에 수행하여 품질 확보

---

## 주의사항

### 카카오맵 Native App Key
- 환경 설정 파일 (`/home/webapp/goldenrabbit/backend/.env`)에서 `VWORLD_APIKEY` 확인
- Native App Key가 별도로 필요한 경우 카카오 개발자 콘솔에서 발급
- Android: `android/app/src/main/AndroidManifest.xml`에 설정
- iOS: `ios/Runner/AppDelegate.swift`에 설정

### 기존 시스템 호환성
- 백엔드 API는 그대로 사용 (변경 없음)
- JWT 토큰 형식 유지
- Airtable 데이터 구조 유지

### 성능 최적화
- 이미지 캐싱 (`cached_network_image`)
- API 응답 캐싱 (Riverpod `keepAlive`)
- 리스트 가상화 (`ListView.builder`)
- 오프라인 지원 (Isar DB 캐시)

### 보안
- JWT 토큰 암호화 저장 (`flutter_secure_storage`)
- HTTPS 통신 강제
- API 키 환경 변수 관리
- 민감 정보 로깅 제거

---

## 개발 환경 설정 (중요!)

### 로컬 PC에서 개발 (권장)

**Flutter 앱 개발은 반드시 로컬 PC에서 진행**해야 합니다. 서버에서 개발하면 다음과 같은 문제가 발생합니다:

❌ **서버 개발의 문제점**:
1. **리소스 부족**: Flutter 빌드는 메모리 4GB+, CPU 멀티코어 필요 → 서버 부하 발생
2. **에뮬레이터 불가**: Android/iOS 에뮬레이터는 GUI 환경 필요 → 서버(CLI)에서 실행 불가
3. **개발 경험 저하**: Hot Reload, 디버깅 등이 원활하지 않음
4. **용량 문제**: Android SDK, iOS SDK 합치면 10GB+ 차지
5. **서버 다운 위험**: 빌드 시 CPU/메모리 사용량 급증

✅ **권장 개발 환경**:

**로컬 PC (Windows/macOS)**에서 개발 → 완성된 빌드만 서버에 배포

```
로컬 PC                                   서버 (goldenrabbit.biz)
├── Flutter 프로젝트 개발                  ├── 백엔드 API (Flask)
├── Android 에뮬레이터 테스트               ├── Nginx 웹서버
├── iOS 시뮬레이터 테스트 (macOS만)         └── Flutter Web 빌드 배포
├── 코드 작성 및 디버깅                          (build/web/ 복사)
└── Git 커밋
```

### 로컬 PC 개발 환경 설정

**1. Flutter SDK 설치 확인**:
```bash
# 로컬 PC에서
flutter --version
flutter doctor
```

**2. 프로젝트 생성 (로컬 PC)**:
```bash
# 로컬 PC의 작업 디렉토리에서
cd ~/projects  # 또는 원하는 경로
flutter create propedia
cd propedia
```

**3. Git 연동 (선택사항)**:
```bash
# 기존 GoldenRabbit 레포지토리에 propedia/ 폴더 추가
git init
git remote add origin <your-repo-url>
```

**4. 로컬에서 개발 및 테스트**:
```bash
# 개발 모드 실행 (Hot Reload 지원)
flutter run

# 또는 Android 에뮬레이터에서
flutter run -d <device-id>

# 또는 Chrome (Web)에서
flutter run -d chrome
```

**5. Flutter Web 빌드 후 서버 배포**:
```bash
# 로컬 PC에서 Web 빌드
flutter build web --release --web-renderer html

# 빌드 결과물을 서버로 복사 (SCP/SFTP)
scp -r build/web/* webapp@goldenrabbit.biz:/home/webapp/goldenrabbit/frontend/public/flutter-app/

# 또는 Git으로 관리한다면
git add build/web/
git commit -m "Build Flutter Web"
git push
# 서버에서 git pull
```

### Android/iOS 앱 빌드

**Android**:
```bash
# 로컬 PC에서 APK 빌드
flutter build apk --release

# AAB (Play Store용)
flutter build appbundle --release

# 빌드 결과물 위치
# build/app/outputs/flutter-apk/app-release.apk
# build/app/outputs/bundle/release/app-release.aab
```

**iOS** (macOS만 가능):
```bash
# macOS에서 IPA 빌드
flutter build ipa --release

# Xcode에서 서명 후 App Store Connect 업로드
```

### 서버 사용 (배포 전용)

서버는 **오직 배포 목적**으로만 사용:

1. **Flutter Web 호스팅**:
   - 로컬에서 빌드한 `build/web/` 폴더를 서버로 복사
   - Nginx가 정적 파일로 서빙

2. **백엔드 API 유지**:
   - 기존 Flask API는 그대로 유지
   - Flutter 앱은 이 API를 호출

3. **지속적 배포** (선택사항):
   - GitHub Actions로 자동 빌드 및 배포 설정 가능

---

---

## 현재 진행 상태 (2026-02-20 업데이트)

### 완료된 Phase

| Phase | 내용 | 상태 | 완료일 |
|-------|------|------|--------|
| 1 | 프로젝트 초기화 | ✅ 완료 | 2026-02-10 |
| 2 | 인증 시스템 | ✅ 완료 | 2026-02-10 |
| 3 | 건축물 검색 (도로명/지번) | ✅ 완료 | 2026-02-10 |
| 4 | 지도 검색 | ✅ 완료 | 2026-02-11 |
| 5 | 검색 기록/즐겨찾기 | ✅ 완료 | 2026-02-12 |
| 6 | 프로필/설정 | ✅ 완료 | 2026-02-13 |
| 7 | 매물 정보 조회 | ✅ 완료 | 2026-02-18 |
| 8 | 매물 지도 표시 | ✅ 완료 | 2026-02-18 |
| 9 | Flutter Web 배포 | ✅ 완료 | 2026-02-20 |
| 10 | 모바일 앱 배포 | 🔄 진행중 | - |

### Phase 10 세부 진행 상황

**Android (Google Play)**:
- [x] 서명 키 생성 (`propedia-release-key.jks`)
- [x] Play Console 앱 등록 (`com.proppedia.app`)
- [x] AAB 빌드 완료 (v1.0.1+2)
- [x] 비공개 테스트 트랙 생성
- [x] 테스터 20명 모집 및 초대
- [ ] 14일 테스트 진행 중 (2026-02-20 ~ 03-06)
- [ ] 프로덕션 출시

**iOS (App Store)**:
- [ ] Apple Developer Program 가입
- [ ] 프로비저닝 프로파일 생성
- [ ] IPA 빌드
- [ ] App Store Connect 업로드
- [ ] 심사 및 출시

### Phase 9 완료 내역 (2026-02-20)

**Flutter Web 배포 완료**:
- 빌드: `flutter build web --release --base-href "/proppedia-app/"`
- 배포 경로: `/home/webapp/goldenrabbit/frontend/public/proppedia-app/`
- URL: https://goldenrabbit.biz/proppedia-app/

**홍보/마케팅 인프라 구축 완료**:
- 앱 소개 랜딩 페이지: https://goldenrabbit.biz/proppedia/
- SEO 설정: robots.txt, sitemap.xml 배포
- nginx 설정 업데이트 (proppedia, proppedia-app 경로)
- 블로그 콘텐츠 초안 작성 (marketing/blog-content/)

### 남은 작업

1. **iOS 앱 출시** (Phase 10)
   - Apple Developer 계정 필요 ($99/년)

2. **추가 기능** (선택)
   - 매물 즐겨찾기 연동
   - 홈 화면 매물 섹션 추가

---

## 다음 단계

1. **로컬 PC에서 프로젝트 생성**:
   ```bash
   # 로컬 PC의 작업 디렉토리에서
   cd ~/projects  # Windows: C:\Users\yourname\projects
   flutter create propedia
   cd propedia
   ```

2. **pubspec.yaml 설정**: 위의 필수 패키지 추가

3. **폴더 구조 생성**: `lib/` 디렉토리 구조화

4. **Phase 1부터 순차적으로 진행** (로컬 PC에서)

5. **각 Phase 완료 후 검증 시나리오 수행** (로컬 에뮬레이터/시뮬레이터)

6. **완성 후 서버 배포**:
   - Flutter Web: `build/web/` → 서버로 복사
   - Android: Play Store 업로드
   - iOS: App Store 업로드

이 계획대로 진행하면 약 14주 내에 완전한 Flutter 앱을 구축할 수 있습니다.


화 |
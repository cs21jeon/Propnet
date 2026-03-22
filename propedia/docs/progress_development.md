업데이트 현황 (2026-02-10)

&nbsp; ## Phase 1:  ✅ 완료

&nbsp; - ✅ Flutter 프로젝트 생성

&nbsp; - ✅ pubspec.yaml 패키지 설정

&nbsp; - ✅ Clean Architecture 폴더 구조 생성

&nbsp; - ✅ 테마 설정 (app\_colors.dart, app\_text\_styles.dart, app\_theme.dart)

&nbsp; - ✅ app.dart, main.dart 구현

&nbsp; - ✅ 앱 실행 테스트 성공 (Chrome)

&nbsp; - ✅ Flutter Web 빌드 성공



&nbsp; ## Phase 2: 인증 시스템 ✅ 완료



&nbsp; ### 구현된 파일 목록:



&nbsp; \*\*모델/DTO (Freezed)\*\*

&nbsp; - lib/domain/entities/user.dart - User 엔티티

&nbsp; - lib/data/dto/auth\_dto.dart - LoginRequest, RegisterRequest, AuthResponse 등



&nbsp; \*\*네트워크 (Dio)\*\*

&nbsp; - lib/core/network/api\_client.dart - Dio HTTP 클라이언트 (baseUrl: https://goldenrabbit.biz)

&nbsp; - lib/core/network/auth\_interceptor.dart - JWT 토큰 자동 추가/갱신 인터셉터

&nbsp; - lib/data/datasources/remote/auth\_api.dart - 인증 API 호출 클래스



&nbsp; \*\*토큰 저장 (SecureStorage)\*\*

&nbsp; - lib/core/storage/token\_storage.dart - 암호화된 토큰 저장/관리



&nbsp; \*\*Repository \& Provider (Riverpod)\*\*

&nbsp; - lib/data/repositories/auth\_repository.dart - 인증 비즈니스 로직

&nbsp; - lib/presentation/providers/auth\_provider.dart - 인증 상태 관리 (AuthNotifier, AuthState)



&nbsp; \*\*라우팅 (go\_router)\*\*

&nbsp; - lib/core/router/app\_router.dart - 인증 상태 기반 라우팅 (/, /login, /register, /home)



&nbsp; \*\*화면 UI\*\*

&nbsp; - lib/presentation/screens/splash/splash\_screen.dart - 스플래시 화면 (자동 로그인 체크)

&nbsp; - lib/presentation/screens/auth/login\_screen.dart - 로그인 화면

&nbsp; - lib/presentation/screens/auth/register\_screen.dart - 회원가입 화면

&nbsp; - lib/presentation/screens/home/home\_screen.dart - 홈 화면 (검색 방식 선택)



&nbsp; ### 연동된 API 엔드포인트:

&nbsp; - POST /app/api/auth/register - 회원가입

&nbsp; - POST /app/api/auth/login - 로그인

&nbsp; - POST /app/api/auth/refresh - 토큰 갱신

&nbsp; - GET /app/api/auth/me - 내 정보 조회

&nbsp; - POST /app/api/auth/logout - 로그아웃



&nbsp; ### 패키지 변경사항:

&nbsp; - Retrofit 제거 → Dio 직접 사용 (패키지 호환성 문제)

&nbsp; - Isar 제거 → Hive 사용 예정 (Phase 5에서 구현)



&nbsp; ### 테스트 결과:

&nbsp; - flutter analyze: No issues found

&nbsp; - flutter test: All tests passed

&nbsp; - flutter build web: 빌드 성공

&nbsp; - flutter run -d chrome: 실행 성공



&nbsp; ---



&nbsp; ## Phase 3: 건축물 검색 기능 ✅ 완료 (2026-02-10)



&nbsp; ### 구현된 파일 목록:



&nbsp; \*\*DTO (Freezed)\*\*

&nbsp; - lib/data/dto/building\_dto.dart - 건축물/토지 관련 모든 DTO

&nbsp;   - RoadSearchRequest, RoadSearchResponse, RoadSearchResultItem

&nbsp;   - JibunSearchRequest, BuildingSearchResponse

&nbsp;   - BdMgtSnSearchRequest

&nbsp;   - CodeInfo, AddressInfo, BuildingInfo, BuildingBasicInfo, FloorInfo

&nbsp;   - LandInfo, BjdongSearchItem, BjdongSearchResponse

&nbsp;   - AreaInfoRequest, AreaInfo, AreaInfoResponse

&nbsp;   - \_intFromDynamic, \_stringFromDynamic 컨버터 함수 (혼합 타입 처리)



&nbsp; \*\*API \& Repository\*\*

&nbsp; - lib/data/datasources/remote/building\_api.dart - 건축물 검색 API 호출

&nbsp; - lib/data/repositories/building\_repository.dart - 건축물 검색 비즈니스 로직



&nbsp; \*\*Provider (Riverpod)\*\*

&nbsp; - lib/presentation/providers/building\_provider.dart

&nbsp;   - RoadSearchNotifier, RoadSearchState - 도로명 검색 상태 관리

&nbsp;   - BuildingSearchNotifier, BuildingSearchState - 지번/건물관리번호 검색 상태 관리

&nbsp;   - AreaInfoNotifier, AreaInfoState - 공동주택 동/호 상세 정보 상태 관리

&nbsp;   - bjdongSearchProvider - 법정동 자동완성



&nbsp; \*\*화면 UI\*\*

&nbsp; - lib/presentation/screens/search/search\_road\_screen.dart - 도로명 검색 화면

&nbsp; - lib/presentation/screens/search/search\_jibun\_screen.dart - 지번 검색 화면

&nbsp;   - Overlay 기반 법정동 자동완성 드롭다운 (CompositedTransformTarget/Follower)

&nbsp;   - 토지구분 선택 (대지/임야)

&nbsp; - lib/presentation/screens/search/result\_screen.dart - 검색 결과 상세 표시

&nbsp;   - 주소 정보 (도로명/지번)

&nbsp;   - 토지 정보 (면적, 지목, 공시지가, 용도지역 등)

&nbsp;   - 건축물 정보 (용도, 구조, 층수, 면적, 건폐율/용적률 등)

&nbsp;   - 층별 정보 테이블

&nbsp;   - 공동주택 동/호 선택 드롭다운 및 상세 정보 조회



&nbsp; \*\*토큰 저장 (플랫폼별 분기)\*\*

&nbsp; - lib/core/storage/token\_storage.dart

&nbsp;   - Web: SharedPreferences 사용 (FlutterSecureStorage 미지원)

&nbsp;   - Mobile: FlutterSecureStorage 사용 (암호화)



&nbsp; \*\*라우팅 업데이트\*\*

&nbsp; - lib/core/router/app\_router.dart - /search/road, /search/jibun, /result 라우트 추가

&nbsp; - lib/presentation/screens/home/home\_screen.dart - 검색 버튼 연결



&nbsp; ### 연동된 API 엔드포인트:

&nbsp; - POST /app/api/search/road - 도로명 검색

&nbsp; - POST /app/api/search/jibun - 지번 검색

&nbsp; - POST /app/api/search/bdmgtsn - 건물관리번호 검색

&nbsp; - GET /app/api/bjdong/search?query=... - 법정동 자동완성

&nbsp; - POST /app/api/area - 공동주택 동/호별 상세 정보



&nbsp; ### 해결된 이슈:

&nbsp; 1. \*\*로그인 JSON 파싱 오류\*\*: 서버 응답 snake\_case와 DTO camelCase 불일치 → @JsonKey 어노테이션 추가

&nbsp; 2. \*\*Web FlutterSecureStorage 오류\*\*: OperationError 발생 → SharedPreferences로 대체 (Web만)

&nbsp; 3. \*\*법정동 드롭다운 클릭 안됨\*\*: GestureDetector가 이벤트 가로챔 → Overlay 방식으로 변경

&nbsp; 4. \*\*공동주택 조회 실패\*\*: total\_parking 등 필드가 int 또는 String("-") 혼합 → fromJson 컨버터 추가

&nbsp; 5. \*\*서버 bjdong/search 500 에러\*\*: systemd 서비스 Python venv 경로 문제 → 서버에서 수정



&nbsp; ### 테스트 결과:

&nbsp; - flutter build web: 빌드 성공

&nbsp; - flutter analyze: 경고만 있음 (에러 없음)

&nbsp; - 단독주택/공동주택 검색 테스트 성공



&nbsp; ---



&nbsp; ## Phase 4: 지도 검색 기능 ✅ 완료 (2026-02-11)



&nbsp; 구현 완료:

&nbsp; - ✅ 카카오맵 SDK 설정 (Android/iOS)

&nbsp; - ✅ SearchMapScreen 구현

&nbsp; - ✅ 좌표 클릭 → 지번 변환

&nbsp; - ✅ 필지 경계 표시 (Polygon)

&nbsp; - ✅ 마커 업데이트 버그 수정

&nbsp; - ✅ GitHub 저장소 연동

&nbsp; - ✅ API 키 환경변수 관리



&nbsp; 연동된 API:

&nbsp; - POST /app/api/map/click-jibun - 좌표 → 지번 변환

&nbsp; - GET /app/api/map/parcel-boundary?pnu=... - 필지 경계



&nbsp; ---



&nbsp; ## Phase 5: 검색 기록 및 즐겨찾기 ✅ 완료 (2026-02-12)



&nbsp; ### 구현된 파일 목록:



&nbsp; **모델 (Hive)**

&nbsp; - `lib/data/models/search_history.dart` - 검색 기록 모델 (@HiveType)

&nbsp; - `lib/data/models/favorite.dart` - 즐겨찾기 모델 (@HiveType)

&nbsp; - `lib/data/models/search_history.g.dart` - Hive TypeAdapter (자동 생성)

&nbsp; - `lib/data/models/favorite.g.dart` - Hive TypeAdapter (자동 생성)



&nbsp; **데이터베이스 서비스**

&nbsp; - `lib/core/database/database_service.dart` - Hive 초기화 및 CRUD 작업



&nbsp; **API**

&nbsp; - `lib/data/datasources/remote/history_api.dart` - 검색 기록 API

&nbsp; - `lib/data/datasources/remote/favorites_api.dart` - 즐겨찾기 API



&nbsp; **Repository**

&nbsp; - `lib/data/repositories/history_repository.dart` - 검색 기록 비즈니스 로직

&nbsp; - `lib/data/repositories/favorites_repository.dart` - 즐겨찾기 비즈니스 로직



&nbsp; **Provider (Riverpod)**

&nbsp; - `lib/presentation/providers/history_provider.dart` - 검색 기록 상태 관리

&nbsp; - `lib/presentation/providers/favorites_provider.dart` - 즐겨찾기 상태 관리



&nbsp; **화면 UI**

&nbsp; - `lib/presentation/screens/history/history_screen.dart` - 검색 기록 목록

&nbsp; - `lib/presentation/screens/favorites/favorites_screen.dart` - 즐겨찾기 목록

&nbsp; - `lib/presentation/screens/search/result_screen.dart` - 검색 기록 저장 및 즐겨찾기 버튼 추가

&nbsp; - `lib/presentation/screens/search/search_map_screen.dart` - searchType: 'map' 전달



&nbsp; **라우터 업데이트**

&nbsp; - `lib/core/router/app_router.dart` - /history, /favorites 라우트 추가



&nbsp; **홈 화면 업데이트**

&nbsp; - `lib/presentation/screens/home/home_screen.dart` - 하단 네비게이션 바 추가



&nbsp; ### 연동된 API 엔드포인트:

&nbsp; - GET /app/api/user/history?limit=100 - 검색 기록 조회 (날짜별 그룹핑)

&nbsp; - DELETE /app/api/user/history/{id} - 검색 기록 삭제

&nbsp; - DELETE /app/api/user/history/all - 검색 기록 전체 삭제

&nbsp; - GET /app/api/user/favorites?limit=100 - 즐겨찾기 조회

&nbsp; - POST /app/api/user/favorites - 즐겨찾기 추가

&nbsp; - DELETE /app/api/user/favorites/{id} - 즐겨찾기 삭제

&nbsp; - PUT /app/api/user/favorites/{id} - 즐겨찾기 메모/별칭 수정



&nbsp; ### 주요 기능:

&nbsp; - 검색 완료 후 자동 검색 기록 저장 (result_screen.dart initState)

&nbsp; - 검색 결과 화면 AppBar에 즐겨찾기 버튼 (★ 토글)

&nbsp; - 검색 타입 표시 (도로명/지번/지도) - searchType 필드 추가

&nbsp; - 검색 기록 날짜별 그룹핑 표시

&nbsp; - 검색 기록 클릭 → 해당 부동산 결과 화면 이동

&nbsp; - 즐겨찾기 별칭/메모 편집

&nbsp; - 하단 네비게이션 바 (홈, 검색기록, 즐겨찾기)

&nbsp; - 로컬(Hive) + 서버 동기화 지원



&nbsp; ### 패키지 추가:

&nbsp; - `hive_generator: ^2.0.1` (dev_dependencies)



&nbsp; ### 테스트 결과:

&nbsp; - flutter analyze: 에러 없음 (경고만)

&nbsp; - flutter build web: 빌드 성공



&nbsp; ### 버그 수정 (2026-02-13):

&nbsp; **검색 기록 저장 타이밍 문제 수정**

&nbsp; - 문제: `_saveSearchHistory()`가 검색 완료 전(loading 상태)에 호출되어 기록이 저장되지 않음

&nbsp; - 해결: `ref.listenManual()`을 사용하여 검색 완료(success) 상태 감지 후 저장

&nbsp; - 수정 파일: `lib/presentation/screens/search/result_screen.dart`



&nbsp; **검색 기록/즐겨찾기 지번 주소 표시**

&nbsp; - `history_screen.dart` - 로컬 기록에서 jibunAddress 우선 표시, 도로명 주소 함께 표시

&nbsp; - `favorites_screen.dart` - 로컬 즐겨찾기로 변경, jibunAddress 우선 표시



&nbsp; **하단 네비게이션 바 호버/터치 효과 추가**

&nbsp; - `home_screen.dart`, `history_screen.dart`, `favorites_screen.dart`

&nbsp; - GestureDetector → Material + InkWell 변경

&nbsp; - hoverColor, splashColor 추가



&nbsp; **데이터 영구 저장 확인**

&nbsp; - Hive 로컬 저장소: 앱 종료 후에도 데이터 유지

&nbsp; - Android: 앱 데이터 폴더에 영구 저장

&nbsp; - Web: IndexedDB에 영구 저장 (시크릿 모드 제외)



&nbsp; ---



&nbsp; ## Phase 6: 프로필 및 설정 ✅ 완료 (2026-02-13)



&nbsp; ### 구현된 파일 목록:



&nbsp; **Provider**

&nbsp; - `lib/presentation/providers/theme_provider.dart` - 다크모드 상태 관리 (ThemeModeNotifier)

&nbsp; - `lib/presentation/providers/user_provider.dart` - 사용 통계 상태 관리 (UsageStatsNotifier)



&nbsp; **DTO**

&nbsp; - `lib/data/dto/user_stats_dto.dart` - UsageStatsResponse, UsageStats, SearchByType



&nbsp; **API & Repository**

&nbsp; - `lib/data/datasources/remote/user_api.dart` - 사용 통계 API 호출

&nbsp; - `lib/data/repositories/user_repository.dart` - 사용 통계 비즈니스 로직



&nbsp; **화면 UI**

&nbsp; - `lib/presentation/screens/profile/profile_screen.dart` - 프로필 화면

&nbsp;   - 사용자 정보 카드

&nbsp;   - 다크모드 토글 (Switch)

&nbsp;   - 사용 통계 표시 (총 검색, 즐겨찾기, 오늘/이번주 검색, 검색타입별 통계)

&nbsp;   - 로그아웃 버튼



&nbsp; **라우터 업데이트**

&nbsp; - `lib/core/router/app_router.dart` - /profile 라우트 추가



&nbsp; **하단 네비게이션 업데이트**

&nbsp; - `lib/presentation/screens/home/home_screen.dart` - 프로필 탭 추가

&nbsp; - `lib/presentation/screens/history/history_screen.dart` - 프로필 탭 추가

&nbsp; - `lib/presentation/screens/favorites/favorites_screen.dart` - 프로필 탭 추가



&nbsp; **앱 테마 연동**

&nbsp; - `lib/app.dart` - ThemeModeProvider 연동



&nbsp; ### 연동된 API 엔드포인트:

&nbsp; - GET /app/api/user/usage-stats - 사용 통계 조회



&nbsp; ### 주요 기능:

&nbsp; - 다크모드/라이트모드 전환 (SharedPreferences로 영구 저장)

&nbsp; - 사용 통계 표시 (총 검색, 즐겨찾기, 오늘/이번주/이번달 검색)

&nbsp; - 검색 타입별 통계 (도로명/지번/지도)

&nbsp; - 마지막 검색 일시, 가입일 표시

&nbsp; - 로그아웃 기능

&nbsp; - 하단 네비게이션 4탭 (홈, 검색기록, 즐겨찾기, 프로필)



&nbsp; ### 버그 수정 (2026-02-13):

&nbsp; **즐겨찾기 상태 표시 오류**
&nbsp; - 문제: 즐겨찾기 별이 항상 노란색으로 표시됨
&nbsp; - 해결: displayAddress 기반 → PNU 기반 비교로 변경
&nbsp; - 수정 파일: `result_screen.dart`

&nbsp; **사용 통계 로드 실패**
&nbsp; - 문제: 서버 API 미구현으로 통계 로드 불가
&nbsp; - 해결: 서버 API 대신 로컬 데이터(historyProvider, favoritesProvider) 기반 통계로 변경
&nbsp; - 수정 파일: `profile_screen.dart`

&nbsp; **다크모드 색상 문제**
&nbsp; - 지번 검색 법정동 드롭다운 글씨 안보임 → Theme.of(context).cardColor 적용
&nbsp; - 층별개요 테이블 글씨 검은색 → isDark 조건 분기
&nbsp; - 공동주택 동/호 선택 드롭다운 → dropdownColor, fillColor 테마 적용
&nbsp; - 토지구분 버튼 배경색 → isDark 조건 분기
&nbsp; - 수정 파일: `search_jibun_screen.dart`, `result_screen.dart`

&nbsp; **다크모드 네비게이션/푸터 배경 흰색**
&nbsp; - 문제: 하단 네비게이션 바와 푸터가 다크모드에서도 흰색 유지
&nbsp; - 해결: `Colors.white` → `Theme.of(context).scaffoldBackgroundColor` 변경
&nbsp; - 수정 파일: `app_footer.dart`, `home_screen.dart`, `history_screen.dart`, `favorites_screen.dart`

&nbsp; **로고 다크모드 투명 문제**
&nbsp; - 문제: 로고의 책 부분이 투명 처리되어 다크모드에서 안보임
&nbsp; - 해결: "fillbook 01" 버전 로고로 교체 (책 부분 흰색 채움, 사이즈 조정)
&nbsp; - 서버 소스: `/home/webapp/goldenrabbit/backend/assets/proppedia/logo_proppedia_*_fillbook_logo only 01.png`
&nbsp; - 교체된 파일: `assets/images/proppedia_logo.png` (179KB), `assets/images/proppedia_logo_landscape.png` (196KB)
&nbsp; - 영향받는 화면: 로그인, 홈 헤더, PDF

&nbsp; ---



&nbsp; ## Phase 7: 매물 정보 연동 ✅ 완료 (2026-02-14 ~ 02-18)


### 구현 방향 변경

**기존 계획**: 외부 링크 방식 (딥링크 문제로 보류)

**변경된 방향**: 앱 내에 매물 기능 직접 구현
- goldenrabbit.biz 웹사이트와 동일한 구조로 Flutter 앱 내 구현
- 서버 API 연동 (매물 목록/상세/검색/지도)


### 구현된 파일 목록:

**DTO (Freezed)**
- `lib/data/dto/property_dto.dart` - 매물 관련 DTO
  - PropertyRecord, PropertyFields, PropertyCategory 등
  - `investment` 필드 추가 (실투자금)
  - `formatPrice()` 함수: 17.8억 형식으로 표시

**API & Repository**
- `lib/data/datasources/remote/property_api.dart` - 매물 API 호출
- `lib/data/repositories/property_repository.dart` - 매물 비즈니스 로직

**Provider (Riverpod)**
- `lib/presentation/providers/property_provider.dart`
  - PropertyListNotifier, PropertyDetailNotifier, PropertySearchNotifier
  - coordinatesProvider, allPropertiesProvider (지도용)
  - selectedCategoryProvider, SearchStatus

**화면 UI**
- `lib/presentation/screens/property/property_list_screen.dart` - 매물 목록
  - 카테고리 탭 (전체/재건축/고수익/저가)
- `lib/presentation/screens/property/property_detail_screen.dart` - 매물 상세
  - 웹사이트와 동일한 구조로 완전 재작성
- `lib/presentation/screens/property/property_map_screen.dart` - 매물 지도
  - CustomOverlay로 가격 마커 표시 (17.8억 형식)
- `lib/presentation/screens/property/property_search_screen.dart` - 매물 검색
  - 입력 → 조건 선택 방식 UI
- `lib/presentation/screens/property/property_search_map_screen.dart` - 검색결과 지도 (신규)

**위젯**
- `lib/presentation/widgets/property/property_card.dart` - 매물 카드
  - category 파라미터 추가 (카테고리별 표시 정보 변경)
- `lib/presentation/widgets/property/property_image.dart` - 매물 이미지 (3단 fallback)
- `lib/presentation/widgets/property/property_info_chips.dart` - 카테고리별 정보 칩 (신규)

**라우터**
- `lib/core/router/app_router.dart` - /property/* 라우트 추가
  - `/property/search-map` 라우트 추가 (검색결과 지도)


### 연동된 API 엔드포인트:

- `GET /api/property-list` - 전체 매물 목록
- `GET /api/category-properties?view=` - 카테고리별 매물
- `GET /api/property-detail?id=` - 매물 상세
- `GET /api/check-image?record_id=` - 이미지 확인
- `GET /api/coordinates` - 좌표 데이터
- `POST /api/search-map` - 조건 검색


### 카테고리별 표시 정보 (웹사이트와 동일):

| 카테고리 | 표시 정보 |
|---------|----------|
| 재건축용 토지 | 대지면적, 용도지역 |
| 고수익률 건물 | 대지면적, 수익률, 사용승인일 |
| 저가단독주택 | 대지면적, 층수, 사용승인일 |


### 매물 상세 화면 구조 (웹사이트와 동일):

1. 이미지
2. 지번/매매가
3. 정보 행 (융자제외실투자금, 수익률, 평단가)
4. 상세정보
5. 금토끼부동산 정보
6. 버튼들 (문의하기, 지도보기+링크복사)


### 주요 수정사항 (2026-02-18):

**1. 매물 지도 마커 표시 완료**
- `Marker`의 `customOverlayContent` → `CustomOverlay` + `addCustomOverlay()` 변경
- 가격 마커 정상 표시 (웹과 동일한 HTML 스타일)
- 마커 클릭 시 하단 시트로 매물 정보 표시

**2. 가격 표시 형식 변경**
- '17억8000만원' → '17.8억' 형식으로 간소화
- 1억 미만: '5000만' 형식
- `formatPrice()` 함수 수정

**3. 매물 검색 UI 개선**
- 레이아웃: 라벨(70px) + 입력(flex 5) + 선택(flex 4)
- 입력 방식: 숫자 입력 시 자동으로 '이하' 선택
- 입력칸 항상 활성화 (전체 선택 시에도 입력 가능)
- 라벨 "토지면적" 4글자 수용

**4. 검색결과 지도 표시 기능 추가**
- "지도보기" 버튼으로 검색 결과를 지도에 표시
- `PropertySearchMapScreen` 신규 생성
- `/property/search-map` 라우트 추가

**5. 기타**
- 카테고리별 정보 칩 위젯 생성 (`PropertyInfoChips`)
- 상세 화면 웹사이트 구조 반영
- 버튼 높이 48px → 52px (글자 잘림 해결)


### 테스트 결과:

- flutter analyze: 에러 없음
- flutter run -d SM-S928N: Android 기기 실행 성공
- ✅ 매물 지도 마커 269개 표시 확인
- ✅ 조건 검색 31개 결과 확인
- ✅ 검색결과 지도 31개 마커 표시 확인
- ✅ 카테고리별 매물 목록 표시 확인
- ✅ 매물 상세 화면 표시 확인


### 완료된 작업:

- [x] 매물 지도 화면 마커 표시 (CustomOverlay)
- [x] 매물 검색 UI 개선 (입력 → 선택 방식)
- [x] 검색결과 지도 표시 기능
- [x] 가격 표시 형식 간소화 (17.8억)

### 남은 작업:

- [ ] 즐겨찾기 기능 연동
- [ ] 홈 화면 매물 섹션 추가



&nbsp; ---



&nbsp; ## 알려진 제한사항 (2026-02-10)



&nbsp; 1. \*\*Hot Reload 제한\*\*: Windows 환경에서 Dart code 수정 시 Hot Reload 불가, 앱 재시작 필요

&nbsp; 2. \*\*analyzer 경고\*\*: json\_annotation, analyzer 버전 경고 (기능에는 영향 없음)

&nbsp; 3. \*\*WASM 빌드 불가\*\*: flutter\_secure\_storage\_web, geolocator\_web이 dart:html 사용 → JS 빌드만 지원



---



\## 업데이트 이력



\### 2026-02-11: Phase 4 지도 검색 기능 완료 및 보안 설정



\#### 1. 지도 검색 기능 (Phase 4) 완료



\*\*구현된 파일\*\*:

\- `lib/data/dto/map\_dto.dart` - 지도 관련 DTO (MapClickJibunRequest, JibunInfo 등)

\- `lib/data/datasources/remote/map\_api.dart` - 지도 API 호출

\- `lib/data/repositories/map\_repository.dart` - 지도 비즈니스 로직

\- `lib/presentation/providers/map\_provider.dart` - 지도 상태 관리

\- `lib/presentation/screens/search/search\_map\_screen.dart` - 지도 검색 화면



\*\*연동된 API\*\*:

\- POST /app/api/map/click-jibun - 좌표 → 지번 변환

\- GET /app/api/map/parcel-boundary - 필지 경계 조회



\*\*주요 기능\*\*:

\- 카카오맵 표시 (kakao\_map\_plugin)

\- 지도 탭 → 마커 표시 → 지번 정보 조회

\- 필지 경계 폴리곤 표시

\- 현재 위치 버튼 (Geolocator)

\- "조회하기" 버튼 → 건물 검색 → 결과 화면 이동



\#### 2. 마커 업데이트 버그 수정



\*\*문제\*\*: 지도에서 위치 클릭 후 다른 위치 클릭 시 마커가 업데이트되지 않음



\*\*해결\*\*: KakaoMap 위젯의 `markers` 파라미터 대신 컨트롤러 메서드 사용

```dart

// 변경 전: \_markers 상태 변수 사용

// 변경 후: 컨트롤러 직접 호출

await \_mapController!.clearMarker();

await \_mapController!.addMarker(markers: \[Marker(...)]);

```



\#### 3. GitHub 저장소 설정



\*\*저장소\*\*: https://github.com/cs21jeon/Proppedia

\- SSH 인증 설정 (ed25519 키)

\- 초기 커밋 및 푸시 완료



\#### 4. 보안 설정 - API 키 환경변수 관리



\*\*문제\*\*: 카카오 API 키가 코드에 하드코딩되어 공개 저장소에 노출



\*\*해결\*\*: 환경변수 파일로 분리



\*\*생성된 파일\*\*:

\- `.env` - 실제 API 키 (git 제외)

\- `.env.example` - 템플릿 (git 포함)

\- `android/local.properties` - Android API 키 (git 제외)

\- `android/local.properties.example` - 템플릿

\- `ios/Flutter/Secrets.xcconfig` - iOS API 키 (git 제외)

\- `ios/Flutter/Secrets.xcconfig.example` - 템플릿



\*\*수정된 파일\*\*:

\- `pubspec.yaml` - flutter\_dotenv 패키지 추가

\- `lib/main.dart` - dotenv.load() 및 환경변수에서 키 로드

\- `android/app/build.gradle.kts` - local.properties에서 키 읽어 manifestPlaceholders 전달

\- `android/app/src/main/AndroidManifest.xml` - ${KAKAO\_NATIVE\_APP\_KEY} 플레이스홀더

\- `ios/Flutter/Debug.xcconfig` - Secrets.xcconfig include

\- `ios/Flutter/Release.xcconfig` - Secrets.xcconfig include

\- `ios/Runner/Info.plist` - $(KAKAO\_NATIVE\_APP\_KEY) 변수

\- `.gitignore` - .env, Secrets.xcconfig 등 제외



\*\*환경변수 구조\*\*:

```

.env (Flutter 런타임)

├── KAKAO\_NATIVE\_APP\_KEY=xxx

└── KAKAO\_JAVASCRIPT\_KEY=xxx



android/local.properties (Android 빌드)

└── KAKAO\_NATIVE\_APP\_KEY=xxx



ios/Flutter/Secrets.xcconfig (iOS 빌드)

└── KAKAO\_NATIVE\_APP\_KEY=xxx

```



---



\### 2026-02-11: 주택공시가격 표시 및 층별개요 복원



\#### 1. 주택공시가격(VWorld API) 연동 완료



\*\*수정된 백엔드 파일\*\*:

\- `/home/webapp/goldenrabbit/backend/property-manager/routes/app\_api.py`

&nbsp; - `search\_by\_jibun()`: 단독주택 공시가격 조회 로직 추가

&nbsp; - `search\_by\_bdmgtsn()`: 단독주택 공시가격 조회 로직 추가



\*\*연동 API\*\*: VWorld `getIndvdHousingPriceAttr`

\- 반환 필드: `house\_price`, `house\_price\_year`, `house\_price\_month`

\- 대상: 일반건축물 또는 건물없는 토지



\#### 2. 웹앱 주택공시가격 표시 수정



\*\*수정된 파일\*\*: `/home/webapp/goldenrabbit/backend/property-manager/static/app.js`

\- `displayGeneralBuilding()`: 건물정보 섹션 내에 주택공시가격 표시

\- 포맷 변경: `xxxx원 (2025년)` → `xxxx원(2025년)` (공백 제거)



\#### 3. 플러터앱 층별개요 복원



\*\*수정된 파일\*\*: `lib/presentation/screens/search/result\_screen.dart`

\- `\_buildFloorInfoCard()` 함수 추가: 층별개요 테이블 표시

\- 컬럼: 층 | 구조 | 용도 | 면적

\- 정렬: 지상층(높은층→낮은층) → 지하층

\- 조건: 일반건축물(`type == 'general'`) \&\& `floorInfo` 존재 시에만 표시



\#### 적용 방법



```bash

\# 웹앱: property-manager 재시작

sudo systemctl restart property-manager



\# 플러터앱: 앱 재빌드

flutter run -d windows

```



---



\### 2026-02-11: 웹앱/Flutter 앱 조회결과 비교 검토 및 표시 일관성 수정



\#### 1. 8개 테스트 케이스 정의



웹앱과 Flutter 앱의 조회화면/PDF 출력 일관성 검증을 위한 테스트 케이스:



| # | 주소 | 케이스 유형 | 검증 포인트 |

|---|------|-----------|------------|

| 1 | 사당동 산 32-77 | 토지만 (임야) | 건물 없을 때 토지정보 상세표시, 산 표시 |

| 2 | 사당동 318-107 | 토지만 (대지) | 건물 없을 때 처리 |

| 3 | 사당동 1044-23 | 일반건축물 | 주용도, 층별정보 표시 |

| 4 | 사당동 314-12 동없음 201호 | 공동주택 | 세대/가구/호, 공시가격 년도 |

| 5 | 사당동 280-1 101동 201호 | 다필지 공동주택 | 필지수 표시 (9필지) |

| 6 | 사당동 1154 101동 201호 | 대규모 아파트 | 해당동 정보, 전유부 정보 |

| 7 | 사당동 147-29 이수자이동 101-1402호 | 복잡한 동/호명 | 특수 동명/호명 처리 |

| 8 | 사당동 86-6 동없음 101호 | 비주거 건물 | 주택 아닌 multi\_unit 처리 |



\#### 2. 웹앱 버그 수정 (SSH로 result.html 수정)



\*\*서버 파일\*\*: `/home/webapp/goldenrabbit/frontend/public/app/result.html`



| 이슈 | 원인 | 수정 내용 |

|------|------|----------|

| `fmly` 변수 미정의 | 변수명 오타 | `fmly` → `family` |

| 세대/가구/호 기본값 | 잘못된 기본값 | `-/-/-` → `0/0/0` |

| 필지수 표시 형식 | 형식 불일치 | `(합계)` → `\[n필지]` |

| 대지면적 필지수 누락 | 건물정보에 필지수 미표시 | 필지수 추가 |



\*\*수정된 코드 위치\*\*:

\- Line 521: 토지정보 섹션 필지수 형식

\- Line 609: 일반건축물 대지면적 필지수 추가

\- Line 733: 공동주택 대지면적 필지수 추가



\#### 3. Flutter 앱 수정



\*\*수정된 파일\*\*: `lib/presentation/screens/search/result\_screen.dart`



| 항목 | 수정 전 | 수정 후 |

|------|--------|--------|

| `\_formatTotalUnits()` | 0을 '-'로 표시 | 0을 그대로 표시 |

| 세대/가구/호 라벨 | "총 세대/가구/호" | "세대/가구/호" |

| 대지면적 | 필지수 미표시 | `\[n필지]` 표시 (2필지 이상) |

| 층수 표시 | 일반건축물만 표시 | 모든 건물 타입에서 표시 |

| 높이 | 미표시 | 높이 표시 추가 |

| 승강기수 | 미표시 | 승강기수 표시 추가 |



\*\*함수 시그니처 변경\*\*:

```dart

// 변경 전

Widget \_buildBuildingInfoCard(BuildContext context, BuildingInfo building)



// 변경 후 (필지수 조회를 위해 LandInfo 추가)

Widget \_buildBuildingInfoCard(BuildContext context, BuildingInfo building, LandInfo? land)

```



\#### 4. 테스트 케이스 검토 가이드 문서 생성



\*\*생성된 파일\*\*: `docs/test-case-review-guide.md`



문서 내용:

\- 8개 테스트 케이스 목록

\- API 데이터 조회 방법 (curl 예시)

\- 검토 대상 파일 위치 (웹앱/Flutter)

\- 검증 항목 체크리스트 (기본정보, 토지정보, 건물정보, 전유부정보)

\- 테스트 실행 절차

\- 주요 코드 위치

\- 발견된 이슈 및 수정 이력



\#### 5. 검증 결과



\*\*웹앱/Flutter 앱 표시 일관성\*\*:

\- ✅ 지번주소 (시도 포함)

\- ✅ 도로명주소 (시도 포함)

\- ✅ 세대/가구/호 라벨 및 값 (0 표시)

\- ✅ 대지면적 + 평 + 필지수

\- ✅ 연면적/건축면적 + 평

\- ✅ 층수 (모든 건물 타입)

\- ✅ 높이

\- ✅ 승강기수

\- ✅ 공시지가/공동주택가격 + 년도



\*\*MCP 연결 활용\*\*:

\- `.mcp.json` 설정으로 SSH 서버 접속

\- 서버: `root@175.119.224.71`

\- 웹앱 파일 직접 편집 가능



---



\### 2026-02-12: UI 브랜딩 및 Footer 적용



\#### 1. 로그인 화면 브랜딩 수정



\*\*수정된 파일\*\*: `lib/presentation/screens/auth/login\_screen.dart`



\*\*변경 내용\*\*:

\- 로고 이미지 적용: `proppedia\_logo.png` (투명 배경)

\- 텍스트 배치: 로고 → "Proppedia" → "부동산백과" → "세상 편한 부동산 조회" (세로 배치)

\- 로고 크기: 140px



\#### 2. 홈 화면 헤더 브랜딩 수정



\*\*수정된 파일\*\*: `lib/presentation/screens/home/home\_screen.dart`



\*\*변경 내용\*\*:

\- AppBar에 로고+텍스트 가로 배치 (goldenrabbit.biz/app 스타일)

\- 구조: `\[로고 이미지] + \[Proppedia / 부동산백과]` (Row + Column)

\- 로고 크기: 56px

\- AppBar toolbarHeight: 72px



\#### 3. Footer 위젯 구현



\*\*생성된 파일\*\*: `lib/presentation/widgets/common/app\_footer.dart`



\*\*위젯 종류\*\*:

\- `AppFooterSimple` - 홈/검색 화면용 (로고만)

\- `AppFooterWithDisclaimer` - 결과 화면용 (안내문구 + 로고)



\*\*Footer 구성\*\*:

```

\[Proppedia 아이콘] Proppedia 제공 | \[금토끼 아이콘] 금토끼부동산 제작

```



\*\*WithDisclaimer 추가 내용\*\*:

```

본 자료는 공공데이터포털 및 VWorld를 기반으로 생성되었습니다.

오류가 있을 수 있으니 정확한 정보는 공적장부를 참고하세요.

```



\#### 4. Footer 적용 화면



| 화면 | 파일 | Footer 타입 |

|------|------|-------------|

| 홈 화면 | `home\_screen.dart` | AppFooterSimple |

| 도로명 검색 | `search\_road\_screen.dart` | AppFooterSimple |

| 지번 검색 | `search\_jibun\_screen.dart` | AppFooterSimple |

| 지도 검색 | `search\_map\_screen.dart` | AppFooterSimple |

| 결과 화면 | `result\_screen.dart` | AppFooterWithDisclaimer |



\#### 5. 로고 이미지 파일



\*\*다운로드된 파일\*\* (`assets/images/`):

\- `proppedia\_logo.png` - 메인 로고 (투명 배경, 로그인/홈 헤더용)

\- `proppedia\_logo\_landscape.png` - 가로형 로고 (미사용)

\- `proppedia\_icon.png` - 아이콘 (Footer용)

\- `goldenrabbit\_icon.png` - 금토끼부동산 아이콘 (Footer용)



\*\*이미지 소스\*\*:

\- 서버 경로: `/home/webapp/goldenrabbit/backend/assets/proppedia/`

\- 투명 배경 버전: `logo\_proppedia\_transparent\_logo only.png`



\#### 6. 기타 수정사항



\- "PropPedia" → "Proppedia" 텍스트 통일

\- SafeArea 적용으로 Footer가 시스템 UI에 가려지지 않도록 처리

\- errorBuilder 추가로 이미지 로드 실패 시 대체 아이콘 표시



---



\### 2026-02-12: UI/UX 개선 및 PDF 기능 고도화



\#### 1. 푸터 이중 표시 문제 해결



\*\*수정된 파일\*\*: `result\_screen.dart`



\*\*문제\*\*: 결과 화면에서 푸터가 이중으로 표시됨

\- 본문 내 `\_buildDisclaimerSection()` + `bottomNavigationBar`에 `AppFooterWithDisclaimer`



\*\*해결\*\*: `bottomNavigationBar` 제거, 본문 내 안내문구 섹션만 유지



\#### 2. 로그인/회원가입 버튼 높이 조정



\*\*수정된 파일\*\*: `login\_screen.dart`, `register\_screen.dart`



\*\*문제\*\*: 안드로이드에서 '로그인' 버튼의 '인'자 하단이 잘림



\*\*해결\*\*: 버튼 높이 50px → 54px (한글 폰트 descender 여유 확보)



\#### 3. 푸터 영역 개선



\*\*수정된 파일\*\*: `app\_footer.dart`, `result\_screen.dart`, `pdf\_generator.dart`



\*\*변경 내용\*\*:

\- SafeArea 적용 (홈바 위로 표시)

\- Flexible/Wrap 적용 (overflow 방지)

\- 이미지 errorBuilder 추가

\- 구분자: `,` → `|` (간격 6px)

\- 로고 크기: 14px → 13px (10% 축소)

\- 금토끼 로고 모서리 라운드 처리 (ClipRRect)

\- 문구 통일: "Proppedia 제공 | 금토끼부동산 제작"

\- 주소: "goldenrabbit.biz" → "https://goldenrabbit.biz"



\#### 4. 지번검색 입력예시 수정



\*\*수정된 파일\*\*: `search\_jibun\_screen.dart`



\*\*변경\*\*: "서울시 서초구 사당동 314-21" → "서울시 동작구 사당동 123-45"



\#### 5. 조회 결과 화면 안내문구 줄바꿈



\*\*수정된 파일\*\*: `result\_screen.dart`



\*\*변경\*\*:

```

본 자료는 공공데이터포털 및

VWorld를 기반으로 생성되었습니다.



오류가 있을 수 있으니

정확한 정보는 공적장부를 참고하세요.

```



\#### 6. 홈 화면 헤더 크기 조정



\*\*수정된 파일\*\*: `home\_screen.dart`



\*\*변경 내용\*\*:

\- AppBar toolbarHeight: 기본 → 72px

\- 로고 높이: 46px → 56px

\- 제목 폰트: 18px → 20px

\- 부제목 폰트: 12px → 13px



\#### 7. 홈 화면 overflow 문제 해결



\*\*수정된 파일\*\*: `home\_screen.dart`



\*\*문제\*\*: 로그인 후 홈 화면에서 "bottom overflowed by 14 pixels" 오류



\*\*해결\*\*: `Padding` → `SingleChildScrollView`로 변경



\#### 8. PDF 파일명 고도화



\*\*수정된 파일\*\*: `pdf\_provider.dart`



\*\*파일명 형식\*\*:

\- 일반건축물: `Proppedia\_사당동123-45\_20260212\_221625.pdf`

\- 공동주택: `Proppedia\_사당동272-26\_101동\_302호\_20260212\_221625.pdf`

\- 동/호 없는 경우: `Proppedia\_사당동272-26\_동없음\_302호\_20260212\_221625.pdf`



\*\*추출 로직\*\*:

1\. PNU 코드에서 번지 추출

2\. recapTitleInfo에서 번지 추출

3\. platPlc에서 정규식으로 동/번지 추출

4\. areaInfo에서 동/호 정보 추출 (공동주택)



\#### 9. PDF 미리보기 파일명 통일



\*\*수정된 파일\*\*: `result\_screen.dart`



\*\*문제\*\*: 미리보기 후 저장 시 "부동산정보.pdf"로 저장됨



\*\*해결\*\*:

\- 하드코딩된 `name: '부동산정보.pdf'` 제거

\- `notifier.previewPdf()` 호출로 동적 파일명 사용



\#### 10. PDF 푸터 간격 조정



\*\*수정된 파일\*\*: `pdf\_generator.dart`



\*\*변경\*\*: "금토끼부동산 제작"과 "https://goldenrabbit.biz" 사이 공백 3칸 추가



\#### 11. PDF 저장 완료 SnackBar 개선



\*\*수정된 파일\*\*: `result\_screen.dart`



\*\*변경\*\*:

\- "확인" 버튼 제거

\- `duration: 3초` 추가 (자동 닫힘)



\#### 12. 스플래시 스크린 이미지 설정



\*\*수정된 파일\*\*:

\- `android/app/src/main/res/drawable/launch\_background.xml`

\- `android/app/src/main/res/drawable-v21/launch\_background.xml`



\*\*추가된 파일\*\*:

\- `android/app/src/main/res/drawable/launch\_image.png`



\*\*이미지 소스\*\*: 서버 `/home/webapp/goldenrabbit/backend/assets/proppedia/logo\_proppedia\_portrait\_transparent\_logo only.png`



---



\### 수정 파일 요약 (2026-02-12)



| 파일 | 주요 변경 |

|------|----------|

| `login\_screen.dart` | 버튼 높이 54px |

| `register\_screen.dart` | 버튼 높이 54px |

| `home\_screen.dart` | 헤더 크기 확대, SingleChildScrollView |

| `result\_screen.dart` | 푸터 이중 제거, 안내문구 줄바꿈, SnackBar 3초 |

| `app\_footer.dart` | SafeArea, 구분자 |, 로고 라운드 |

| `search\_jibun\_screen.dart` | 입력예시 수정 |

| `pdf\_generator.dart` | 푸터 문구/간격/로고 |

| `pdf\_provider.dart` | 파일명 형식 (지번+동호+타임스탬프) |

| `launch\_background.xml` | 스플래시 이미지 활성

---

### 2026-02-13: 검색기록/즐겨찾기 동기화 및 삭제 기능 개선

#### 1. 검색기록 중복 제거 로직 수정

**문제**: 같은 행정구역(displayAddress)만 같아도 기존 기록을 덮어씀

**해결**: PNU(지번코드) + 동명 + 호명 기준으로 변경

**수정 파일**: `lib/core/database/database_service.dart`

```dart
// 변경 전: displayAddress로 비교
// 변경 후: PNU + dongName + hoName으로 비교
```

#### 2. 서버 동기화 기능 추가

앱 시작 시 서버에서 검색기록/즐겨찾기를 불러와 로컬에 동기화

**수정 파일**:
- `lib/data/datasources/remote/history_api.dart` - API 경로 수정 (`/app/api/user/history`)
- `lib/data/repositories/history_repository.dart` - `syncFromServer()` 메서드 추가
- `lib/data/repositories/favorites_repository.dart` - `syncFromServer()` 메서드 추가
- `lib/presentation/providers/history_provider.dart` - 동기화 호출
- `lib/presentation/providers/favorites_provider.dart` - 동기화 호출
- `lib/presentation/screens/history/history_screen.dart` - 화면 진입 시 자동 동기화
- `lib/presentation/screens/favorites/favorites_screen.dart` - 화면 진입 시 자동 동기화

**동기화 로직**:
- PNU별 최신 기록만 가져오기 (중복 제거)
- 로컬에 없는 기록만 추가
- 당겨서 새로고침 시 서버 재동기화

#### 3. 삭제 시 서버 연동

**문제**: 로컬에서 삭제해도 서버에서 다시 동기화되어 복원됨

**해결**: 삭제 시 같은 PNU를 가진 모든 서버 기록도 함께 삭제

**수정 파일**:
- `lib/presentation/providers/history_provider.dart` - `deleteHistory()` 수정
- `lib/presentation/providers/favorites_provider.dart` - `deleteFavorite()` 수정

#### 4. 저장 기간 확인

| 항목 | 로컬(Hive) | 서버(PostgreSQL) |
|------|-----------|-----------------|
| 검색기록 | 최대 100개, 영구 저장 | 무제한, 영구 저장 |
| 즐겨찾기 | 무제한, 영구 저장 | 무제한, 영구 저장 |

#### 수정 파일 요약

| 파일 | 주요 변경 |
|------|----------|
| `database_service.dart` | 중복 제거 로직 PNU 기준으로 변경 |
| `history_api.dart` | API 경로 `/app/api/user/history`로 수정 |
| `history_repository.dart` | `syncFromServer()` 추가, PNU별 최신 기록만 |
| `favorites_repository.dart` | `syncFromServer()` 추가 |
| `history_provider.dart` | 삭제 시 서버 연동, 동기화 메서드 |
| `favorites_provider.dart` | 삭제 시 서버 연동, 동기화 메서드 |
| `history_screen.dart` | 화면 진입 시 서버 동기화 |
| `favorites_screen.dart` | 화면 진입 시 서버 동기화 |

---

### 2026-02-18: 웹/앱 매물 상세 UI 통일 및 카테고리 UI 개선

#### 1. 웹 공유 페이지 (property-detail.html) 리디자인

**서버 파일**: `/home/webapp/goldenrabbit/frontend/public/property-detail.html`

**변경 사항**:
- Tailwind CSS 적용 (goldenrabbit.biz 디자인과 통일)
- 다크모드 지원 (`darkMode: 'class'`)
- API 엔드포인트 변경: `/api/property/by-id` → `/api/property-detail` (Airtable 필드 직접 사용)
- 이미지 메타데이터 기반 로딩 (`image_metadata.json`)
- 고정 헤더 (로고 + 금토끼부동산)
- 좁은 너비 (`max-w-lg`) - 앱과 동일

**표시 정보**:
1. 이미지
2. 지번 주소 + 매매가
3. 정보 행 (융자제외 실투자금, 수익률, 평단가)
4. 상세정보
5. 금토끼부동산 정보
6. 버튼 (문의하기 + 지도보기)
7. 홈페이지 링크

#### 2. 앱 매물 상세 화면 웹과 동일하게 수정

**수정 파일**: `lib/presentation/screens/property/property_detail_screen.dart`

**변경 사항**:
- 버튼 배치: 문의하기/지도보기 나란히 + 링크복사 별도 행 (웹과 동일)
- 문의하기: 확인 다이얼로그 → 바로 전화 (웹과 동일)
- 지도 연결: 카카오맵 → 네이버 지도 (웹과 동일)
- 버튼 높이: 48px → 52px (글자 잘림 해결)
- 링크복사 버튼: 파란색 테두리 스타일

#### 3. 카테고리 UI 개선 (SegmentedButton)

**수정 파일**: `lib/presentation/screens/property/property_list_screen.dart`

**변경 전**: TabBar (스크롤, 좌측 정렬, 긴 레이블)
**변경 후**: SegmentedButton (균등 분할, 둥근 모서리, 골드 강조)

**레이블 변경**:
- '재건축용 토지' → '재건축토지'
- '고수익률 건물' → '고수익건물'
- '저가단독주택' → '단독주택'

**기타 변경**:
- 헤더 제목: '금토끼부동산 추천매물' → '추천매물' (잘림 방지)
- 체크 아이콘 제거 (`showSelectedIcon: false`)
- TabController 제거 → 단순 상태 관리로 변경

#### 4. 서버 백업 데이터 사용 확인

앱이 이미 서버 백업 데이터를 사용 중임 확인:
- `/api/property-list` → `all_properties.json`
- `/api/property-detail` → `all_properties.json`
- `/api/category-properties` → 카테고리별 JSON 파일
- `/airtable_backup/images/` → 백업 이미지

#### 수정 파일 요약

| 파일 | 주요 변경 |
|------|----------|
| `property-detail.html` (서버) | Tailwind CSS, API 변경, 메타데이터 이미지 |
| `property_detail_screen.dart` | 버튼 배치/동작 웹과 통일, 네이버 지도 |
| `property_list_screen.dart` | SegmentedButton, 짧은 레이블, 체크 제거 |

---

### 2026-02-18: 보안 강화 - 회원가입 동의 및 로그인 설정 추가

#### 1. 회원가입 정보제공동의 추가

**생성된 파일**:
- `lib/core/constants/terms.dart` - 이용약관 및 개인정보처리방침 상수

**수정된 파일**:
- `lib/presentation/screens/auth/register_screen.dart`

**추가된 기능**:
- 전체 동의 체크박스
- 서비스 이용약관 동의 (필수) + 약관 보기 버튼
- 개인정보 수집/이용 동의 (필수) + 약관 보기 버튼
- 개인정보 수집 항목 요약 표시
- 동의하지 않으면 회원가입 불가

#### 2. 로그인 화면 체크박스 추가

**생성된 파일**:
- `lib/core/storage/login_preferences.dart` - 로그인 설정 저장 서비스

**수정된 파일**:
- `lib/presentation/screens/auth/login_screen.dart`
- `lib/data/repositories/auth_repository.dart`

**추가된 기능**:
- 이메일 저장 체크박스 (SharedPreferences 저장)
- 자동 로그인 체크박스 (기본값: 활성화)
- 자동 로그인 해제 시 앱 재시작 후 로그인 화면 표시

#### 수정 파일 요약

| 파일 | 주요 변경 |
|------|----------|
| `terms.dart` (신규) | 이용약관, 개인정보처리방침 상수 |
| `login_preferences.dart` (신규) | 이메일 저장, 자동 로그인 설정 관리 |
| `register_screen.dart` | 약관 동의 체크박스 UI 추가 |
| `login_screen.dart` | 이메일 저장/자동 로그인 체크박스 추가 |
| `auth_repository.dart` | 자동 로그인 설정 확인 로직 추가 |

---

### 2026-02-20: 홍보/마케팅 인프라 구축

#### 1. 앱 소개 랜딩 페이지 제작

**생성된 파일**: `marketing/proppedia/index.html`

**URL**: https://goldenrabbit.biz/proppedia/

**페이지 구성**:
- Hero Section: 헤드라인 + Google Play 다운로드 버튼 + 앱 스크린샷 목업
- 주요 기능 Section: 건축물 정보, 토지 정보, 공시가격
- 3가지 검색 방식 Section: 도로명, 지번, 지도
- 스크린샷 갤러리: 8개 앱 스크린샷
- 다운로드 CTA Section
- Footer: 금토끼부동산 정보, 개인정보처리방침 링크

**SEO 최적화**:
- title: "Proppedia 부동산백과 - 건물과 토지에 관한 모든 정보"
- meta description, keywords
- Open Graph 태그 (SNS 공유용)
- Twitter Card 태그
- Schema.org 구조화된 데이터 (MobileApplication)
- 반응형 디자인 (모바일/태블릿/데스크톱)

#### 2. Flutter Web 앱 배포

**URL**: https://goldenrabbit.biz/proppedia-app/

**빌드 명령어**:
```bash
flutter build web --base-href "/proppedia-app/"
```

**배포된 파일**:
- `index.html`, `main.dart.js` (4.3MB)
- `flutter_bootstrap.js`, `flutter.js`
- `assets/`, `canvaskit/`, `icons/`
- `manifest.json`

**수정된 파일**:
- `lib/app.dart` - title: 'Proppedia 부동산백과'
- `web/manifest.json` - name, short_name, description 업데이트
- `web/index.html` - SEO 메타 태그 추가

#### 3. SEO 파일 생성 및 배포

**생성된 파일**:
- `marketing/robots.txt` - 크롤링 규칙
- `marketing/sitemap.xml` - 사이트맵 (6개 URL)

**배포 URL**:
- https://goldenrabbit.biz/robots.txt
- https://goldenrabbit.biz/sitemap.xml

#### 4. nginx 설정 추가

**수정된 파일**: `/home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf`

**추가된 location 블록**:
```nginx
# Proppedia Flutter Web 앱
location /proppedia-app/ {
    alias /home/webapp/goldenrabbit/frontend/public/proppedia-app/;
    try_files $uri $uri/ /proppedia-app/index.html;
}

# Proppedia 랜딩 페이지
location /proppedia/ {
    alias /home/webapp/goldenrabbit/frontend/public/proppedia/;
    try_files $uri $uri/ /proppedia/index.html;
}

# proppedia-app 내 .env 파일 허용 (숨김 파일 예외)
```

#### 5. 블로그 콘텐츠 초안 작성

**생성된 파일**:
- `marketing/blog-content/01-건축물대장-보는-법.md`
- `marketing/blog-content/02-공시지가-조회하기.md`

#### 6. 배포 스크립트 생성

**생성된 파일**:
- `marketing/deploy.ps1` - PowerShell 배포 스크립트
- `marketing/deploy.sh` - Bash 배포 스크립트
- `marketing/DEPLOYMENT.md` - 배포 가이드

#### 마케팅 파일 구조

```
marketing/
├── proppedia/
│   └── index.html          # 앱 소개 랜딩 페이지
├── blog-content/
│   ├── 01-건축물대장-보는-법.md
│   └── 02-공시지가-조회하기.md
├── robots.txt              # 검색 엔진 크롤링 규칙
├── sitemap.xml             # 사이트맵
├── deploy.ps1              # PowerShell 배포 스크립트
├── deploy.sh               # Bash 배포 스크립트
└── DEPLOYMENT.md           # 배포 가이드
```

#### 배포된 URL 현황

| URL | 설명 | 상태 |
|-----|------|------|
| https://goldenrabbit.biz/proppedia/ | 앱 소개 랜딩 페이지 | ✅ |
| https://goldenrabbit.biz/proppedia-app/ | Flutter Web 앱 | ✅ |
| https://goldenrabbit.biz/robots.txt | 크롤링 규칙 | ✅ |
| https://goldenrabbit.biz/sitemap.xml | 사이트맵 | ✅ |

---

### 2026-02-20: 앱 아이콘 및 이름 변경 (v1.0.1)

#### 1. 앱 아이콘 변경

**사용된 패키지**: `flutter_launcher_icons: ^0.14.3`

**원본 이미지**: `assets/images/proppedia_logo.png`

**설정** (`pubspec.yaml`):
```yaml
flutter_launcher_icons:
  android: true
  ios: true
  remove_alpha_ios: true
  background_color_ios: "#FFFFFF"
  web:
    generate: true
    background_color: "#FFFFFF"
  windows:
    generate: true
  macos:
    generate: true
  image_path: "assets/images/proppedia_logo.png"
  adaptive_icon_background: "#FFFFFF"
  adaptive_icon_foreground: "assets/images/proppedia_logo.png"
```

**생성된 아이콘**:
- Android: mipmap 아이콘 + adaptive 아이콘 (drawable-*/ic_launcher_foreground.png)
- iOS: AppIcon.appiconset 전체 아이콘
- Web: favicon.png, Icon-192.png, Icon-512.png
- Windows: app_icon.ico
- macOS: AppIcon.appiconset 전체 아이콘

#### 2. 앱 이름 변경

**변경**: "propedia" / "Proppedia" → "부동산백과"

**수정된 파일**:
- `android/app/src/main/AndroidManifest.xml` - `android:label="부동산백과"`
- `ios/Runner/Info.plist` - `CFBundleDisplayName`, `CFBundleName` = "부동산백과"

#### 3. 버전 업데이트

**변경**: `1.0.0+1` → `1.0.1+2`

**수정된 파일**: `pubspec.yaml`

#### 4. 빌드 및 배포

- APK 빌드: `build/app/outputs/flutter-apk/app-release.apk` (76.3MB)
- AAB 빌드: `build/app/outputs/bundle/release/app-release.aab` (61.1MB)
- Google Play Console 비공개 테스트 업로드 준비 완료

#### 수정 파일 요약

| 파일 | 주요 변경 |
|------|----------|
| `pubspec.yaml` | flutter_launcher_icons 추가, 버전 1.0.1+2 |
| `AndroidManifest.xml` | android:label="부동산백과" |
| `ios/Runner/Info.plist` | CFBundleName, CFBundleDisplayName = "부동산백과" |
| `android/app/src/main/res/mipmap-*` | 앱 아이콘 이미지 |
| `android/app/src/main/res/drawable-*` | adaptive 아이콘 foreground |
| `ios/Runner/Assets.xcassets/AppIcon.appiconset/*` | iOS 앱 아이콘 |
| `web/favicon.png`, `web/icons/*` | 웹 아이콘 |
| `windows/runner/resources/app_icon.ico` | Windows 아이콘 |
| `macos/Runner/Assets.xcassets/AppIcon.appiconset/*` | macOS 아이콘 |

---

### 2026-02-22: 게스트 모드 구현 및 랜딩 페이지 업데이트

#### 1. 게스트 모드 (비로그인 체험 후 가입 유도)

**목표**: 로그인 없이 기본 기능 사용 가능, 개인화 기능 사용 시 로그인 유도

**기능 정책**:
| 기능 | 비로그인 | 로그인 |
|---|:---:|:---:|
| 주소 검색 | O | O |
| 건축물/토지 정보 조회 | O | O |
| PDF 미리보기/저장/공유 | O | O |
| 검색기록 (로컬) | X | O |
| 즐겨찾기 (로컬) | X | O |
| 서버 동기화 | X | O |

**수정된 파일**:
- `lib/presentation/providers/auth_provider.dart` - `AuthStatus.guest` 추가
- `lib/core/router/app_router.dart` - 게스트 상태 접근 허용
- `lib/presentation/screens/home/home_screen.dart` - 게스트 모드 UI, 인증 상태 변경 감지
- `lib/presentation/screens/profile/profile_screen.dart` - 게스트 모드 UI, 로그아웃 시 데이터 리셋
- `lib/presentation/screens/history/history_screen.dart` - 게스트 안내 메시지
- `lib/presentation/screens/favorites/favorites_screen.dart` - 게스트 안내 메시지
- `lib/presentation/screens/search/result_screen.dart` - 즐겨찾기 시 로그인 유도
- `lib/presentation/providers/history_provider.dart` - `reset()` 로컬 DB 삭제, `skipServerSync`
- `lib/presentation/providers/favorites_provider.dart` - `reset()` 로컬 DB 삭제, `skipServerSync`
- `lib/data/repositories/history_repository.dart` - `skipServerSync` 파라미터
- `lib/data/repositories/favorites_repository.dart` - `skipServerSync` 파라미터
- `lib/presentation/widgets/common/login_prompt_dialog.dart` - 신규 (로그인 유도 다이얼로그)

**주요 변경 사항**:
- 앱 시작 시 토큰 없으면 `guest` 상태로 진입 (홈 화면 표시)
- 게스트 모드에서 검색기록/즐겨찾기 화면 진입 시 로그인 안내 표시
- 즐겨찾기 추가 시 로그인 유도 다이얼로그 표시
- 로그아웃 시 로컬 DB(Hive) 데이터도 함께 삭제 (`reset()` 메서드 수정)

#### 2. 랜딩 페이지 업데이트

**URL**: https://goldenrabbit.biz/proppedia/

**변경 사항**:
- 이미지 경로 통합: `screenshots/` 폴더 사용
- 앱 미리보기 섹션: 홈, 도로명 검색, 지번 검색, 검색 결과, 상세 정보, 지도 검색 (6개)
- 편리한 부가 기능 섹션: 검색 기록, 즐겨찾기, PDF 저장
  - 설명: "회원가입/로그인을 통해 더 편리하게 이용하세요"
- PDF 이미지 높이 통일 (280px)

**추가된 스크린샷**:
- `KakaoTalk_20260221_232554552.jpg` - PDF 저장 (모바일)
- `print pdf 001.png` - PDF 인쇄/저장 (PC)
- `print pdf 002.png` - PDF 결과물 미리보기

**정리**:
- `/var/www/proppedia/` 폴더 삭제 (미사용)
- 이미지는 `/home/webapp/goldenrabbit/frontend/public/proppedia/screenshots/`에 저장

#### 수정 파일 요약

| 파일 | 주요 변경 |
|------|----------|
| `auth_provider.dart` | `AuthStatus.guest` 추가 |
| `app_router.dart` | 게스트 상태 접근 허용 |
| `home_screen.dart` | 게스트 모드 UI, `ref.listen` 인증 상태 감지 |
| `profile_screen.dart` | 게스트 모드 UI, 로그아웃 시 `await reset()` |
| `history_screen.dart` | 게스트 안내 메시지 |
| `favorites_screen.dart` | 게스트 안내 메시지 |
| `result_screen.dart` | 즐겨찾기 시 로그인 유도 |
| `history_provider.dart` | `reset()` → `Future<void>` + DB 삭제 |
| `favorites_provider.dart` | `reset()` → `Future<void>` + DB 삭제 |
| `login_prompt_dialog.dart` (신규) | 로그인 유도 다이얼로그 |
| `marketing/proppedia/index.html` | 섹션 분리, PDF 스크린샷 추가 |

---

### 2026-02-22: 로그인 필수 기능 강화 및 지번 검색 UX 개선

#### 1. 비로그인 시 기능 제한 강화

**기능 정책 업데이트**:
| 기능 | 비로그인 | 로그인 |
|---|:---:|:---:|
| 주소 검색 | O | O |
| 건축물/토지 정보 조회 | O | O |
| PDF 미리보기/저장/공유 | X | O |
| 검색기록 | X | O |
| 즐겨찾기 | X | O |
| 서버 동기화 | X | O |

**수정된 파일 (Flutter)**:
- `lib/presentation/screens/search/result_screen.dart`
  - `_toggleFavorite()`: 비로그인 시 로그인 유도 다이얼로그 표시 후 return
  - `_saveSearchHistory()`: 비로그인 시 저장 스킵

**수정된 파일 (PWA 웹앱)**:
- `/home/webapp/goldenrabbit/frontend/public/app/result.html`
  - `saveSearchHistory()` 호출 전 로그인 체크 추가

#### 2. 지번 검색 UX 개선 (통합 입력)

**문제**: 기존 3단계 입력 필요 (법정동 선택 → 본번 입력 → 부번 입력)

**해결**: 단일 필드에 "사당동 272-26" 형식으로 한 번에 입력

**지원 형식**:
- "사당동 272-26"
- "동작구 사당동 272"
- "서울시 동작구 사당동 272-26"
- "산 123-45" (임야 자동 감지)

**구현 파일**:
- `lib/core/utils/jibun_address_parser.dart` (신규)
  - 주소 문자열 파싱하여 법정동 쿼리, 본번, 부번, 임야 여부 분리
- `lib/presentation/screens/search/search_jibun_screen.dart`
  - 통합 입력 필드 UI
  - 법정동 자동완성 + 단일 매칭 시 자동 선택
  - 산/대지 병렬 검색 후 선택 UI
- `lib/data/repositories/building_repository.dart`
  - `searchBothLandTypes()` 메서드 추가 (대지/임야 병렬 검색)
- `lib/presentation/providers/building_provider.dart`
  - `LandTypeSearchResult` 클래스 추가

**검색 플로우**:
```
입력: "사당동 272-26"
    ↓
파싱: addressQuery="사당동", bun="272", ji="26", isMountain=false
    ↓
법정동 검색 → 단일 매칭 시 자동 선택
    ↓
대지/임야 병렬 검색 (searchBothLandTypes)
    ↓
양쪽 존재 시 → 선택 UI / 단일 존재 시 → 바로 결과
```

#### 3. 지도 위치 정확도 개선

**문제**: 건물 없는 토지 검색 시 지도가 엉뚱한 위치 표시

**원인**: geocoding에 번지 정보 없이 "서울특별시 동작구 사당동"만 전달

**해결**: PNU 코드에서 번지 추출하여 주소에 추가

```dart
// PNU 구조: bjdong(10) + land_type(1) + bun(4) + ji(4)
final landType = pnu.substring(10, 11);
final bunStr = pnu.substring(11, 15);
final jiStr = pnu.substring(15, 19);
// → "서울특별시 동작구 사당동 산 32-77" 형식으로 geocoding
```

#### 수정 파일 요약

| 파일 | 주요 변경 |
|------|----------|
| `result_screen.dart` | 로그인 필수 체크 (즐겨찾기, 검색기록), 지도 위치 PNU 추출 |
| `jibun_address_parser.dart` (신규) | 지번 주소 파싱 유틸리티 |
| `search_jibun_screen.dart` | 통합 입력 UI, 산/대지 선택 UI |
| `building_repository.dart` | `searchBothLandTypes()` 병렬 검색 |
| `building_provider.dart` | 검색 상태 관리 업데이트 |
| PWA `result.html` | 비로그인 시 검색기록 저장 차단 |
| PWA `search-jibun.html` | 통합 입력 UI, 산/대지 병렬 검색 |

#### 3. 지번 검색 버튼 클릭 방식으로 변경

**문제**: 입력 시 자동 검색으로 인해 뒤로가기 후 검색 버튼이 안 보이는 UX 문제

**해결**: 버튼 클릭 방식으로 변경
- 입력 시 → 파싱 미리보기만 표시 (API 호출 없음)
- 검색 버튼 → 항상 표시
- 버튼 클릭 시 → API 검색 시작

**수정된 파일**:
- `lib/presentation/screens/search/search_jibun_screen.dart` - 버튼 클릭 방식 적용
- PWA `/app/search-jibun.html` - 버튼 클릭 방식 적용

#### 4. "산" 파싱 버그 수정

**문제**: "사당동산 32-77" 형태 (동+산+공백+숫자) 파싱 실패

**해결**: 새로운 정규식 패턴 추가

```dart
// "사당동산 32-77" 형태 (동/리/읍/면+산+공백+숫자)
else if (RegExp(r'[동리읍면]산\s+\d').hasMatch(working)) {
  isMountain = true;
  working = working.replaceFirstMapped(
    RegExp(r'([동리읍면])산\s+'),
    (match) => '${match.group(1)} ',
  );
}
```

**수정된 파일**:
- `lib/core/utils/jibun_address_parser.dart` - 파싱 패턴 추가
- PWA `/app/search-jibun.html` - 동일 패턴 추가

---

### 2026-02-26: 스켈레톤 로딩 UI 및 단계별 진행 메시지 (v1.0.2+6)

#### 1. 스켈레톤 로딩 UI 구현

**목표**: 로딩 중 실제 결과 화면과 유사한 스켈레톤 UI로 체감 속도 개선

**생성된 파일**:
- `lib/presentation/widgets/common/skeleton_loading.dart` - Shimmer 기반 스켈레톤 UI
- `lib/presentation/widgets/common/loading_progress_indicator.dart` - 시간 기반 로딩 위젯

**수정된 파일**:
- `lib/presentation/screens/search/result_screen.dart` - 로딩/에러 UI 교체
- `lib/core/network/api_client.dart` - 타임아웃 30초 → 60초

**스켈레톤 UI 구성**:
- 기본 정보 카드 (파란색 아이콘)
- 토지 정보 카드 (초록색 아이콘)
- 건물 정보 카드 (주황색 아이콘)
- 지도 섹션 (청록색 아이콘)

#### 2. 시간 기반 단계별 진행 메시지

서버 호출 없이 클라이언트 타이머만 사용 (추가 지연 없음)

**메시지 타이밍**:
| 경과 시간 | 메시지 |
|----------|--------|
| 0~3초 | 건축물 정보 조회 중... |
| 3~8초 | 토지 정보 확인 중... |
| 8~15초 | 전유부 정보 조회 중... |
| 15~25초 | 대지지분 계산 중... |
| 25~40초 | 데이터 정리 중... |
| 40초+ | 거의 완료되었습니다... |

#### 3. 에러 화면 개선

**변경 전**: 에러 메시지만 표시
**변경 후**:
- 큰 에러 아이콘 (64px)
- 에러 메시지 표시
- "다시 시도" 버튼 (새로고침)
- 네트워크 오류 안내 문구

#### 4. API 타임아웃 연장

**변경**: 30초 → 60초
**이유**: 대규모 아파트 (2만 세대+) 조회 시 타임아웃 방지

#### 5. PWA 앱 동일 적용

**수정 파일**: `/home/webapp/goldenrabbit/frontend/public/app/result.html`

- CSS animate-pulse 기반 스켈레톤 UI
- JavaScript 타이머로 단계별 메시지
- 에러 화면에 "다시 시도" / "돌아가기" 버튼

#### 빌드 결과

- APK: `build/app/outputs/flutter-apk/app-release.apk` (76.6MB)
- AAB: `build/app/outputs/bundle/release/app-release.aab` (61.2MB)

#### 수정 파일 요약

| 파일 | 주요 변경 |
|------|----------|
| `api_client.dart` | 타임아웃 60초 |
| `skeleton_loading.dart` (신규) | Shimmer 스켈레톤 UI |
| `loading_progress_indicator.dart` (신규) | 시간 기반 메시지 |
| `result_screen.dart` | LoadingProgressIndicator 사용, 에러 UI 개선 |
| PWA `result.html` | 스켈레톤 UI, 단계별 메시지, 에러 UI |

---

### 2026-03-01: 신규 행정구역 토지정보 조회 지원 (v1.0.2+7)

#### 1. VWorld API 대체 조회 로직

**서버 수정** (`vworld_service.py`):
- `_get_land_characteristics()`: 기존 getLandCharacteristics API
- `_get_land_from_ladfrl()`: 토지임야대장 API (지목, 면적)
- `_get_land_use_attr()`: 토지이용계획 API (용도지역)
- getLandCharacteristics 실패 시 자동 fallback

#### 2. 건물 없는 토지의 도로명주소 표시

- juso.go.kr API를 통한 지번→도로명주소 변환
- `get_road_address_by_jibun()` 함수 추가 (address_finder_service.py)

#### 3. 법정동 검색 개선

- 정확한 동 이름 매칭 우선 표시 (예: "신동" > 신동읍 > 서신동)
- 최대 5개 항목 높이 제한 + 내부 스크롤
- 지번 존재 여부 필터링: juso.go.kr API로 병렬 검증

#### 4. 신규 행정구역 주소 표시 개선

- `_inject_new_district_name()` 함수 추가 (app_api.py)
- 화성시 동탄구/만세구/효행구/병점구 주소에 구 이름 자동 삽입
- "화성시동탄구" → "화성시 동탄구" 띄어쓰기 정규화

#### 5. 버그 수정

- Regex 백레퍼런스 버그: `f'\1'` → `r'\1'` raw string 사용
- 오산동 법정동코드 누락: 4159710400 레코드 추가
- VWorld 토지 정보 없는 지번: 도로명주소 확인되면 유효한 결과로 인정

#### 빌드 결과

- APK: 76.5MB / AAB: 61.2MB
- 커밋: `0eb2e73 신규 행정구역 토지정보 조회 지원 (v1.0.2+7)`

---

### 2026-03-05: Google 로그인 및 브랜딩 업데이트 (v1.0.2+8)

#### 1. Google 로그인 기능 (서버 + 앱)

- Google Sign-In → JWT 토큰 발급 인증 플로우 구현
- 서버: `app_auth.py` 인증 모듈 (Flask Blueprint, port 8000)
- 앱: AuthProvider, AuthRepository, AuthApi 구현
- 프로필 화면에 사용자 정보 및 로그아웃 버튼 표시

#### 2. 브랜딩 업데이트

- 앱 정보 다이얼로그: PropNet 아이콘, 설명문, 웹사이트/문의 세로 레이아웃
- 푸터 리디자인: `[propnet_icon] 프롭넷 | 부동산 종합 서비스` + `© 2026 Propnet`
- PropNet 브랜드 중심으로 통일

#### 3. 서버

- nginx: `/app/api/auth/` → port 8000, `/app/api/` → port 5000 분리
- `app_auth.py`: 기존 `app_users` 테이블 스키마 호환
- 사용자 계정 데이터 마이그레이션 (검색기록 62건, 즐겨찾기 4건, 통계 13건)

#### 빌드 결과

- 커밋: `6564177 Google 로그인 및 브랜딩 업데이트 (v1.0.2+8)`

---

### 2026-03-08: 통합 인증 시스템 구축 및 프로덕션 출시

#### 1. Property Manager 통합 인증 (Phase 0)

**문제**: 로그인은 `app_auth.py`(port 8000)에서 JWT 생성, 즐겨찾기/검색기록은 Property Manager(port 5000)의 `token_required`로 검증 → JWT 시크릿 불일치 → **401 에러**

**해결**: Property Manager에 Google 로그인 엔드포인트 추가, nginx 라우팅 통합

**서버 수정**:
- `routes/app_auth.py` (Property Manager): `POST /api/auth/google` 추가
  - `GOOGLE_CLIENT_IDS` 리스트로 Android/Web Client ID 모두 지원
  - id_token 검증 → `app_users` 테이블 upsert → JWT 발급
- `services/app_user_service.py`: `create_or_update_google_user()` 메서드 추가
- nginx: `/app/api/auth/` 라우팅을 port 8000 → port 5000으로 변경
- `.env`: `DB_HOST=localhost` → `DB_HOST=127.0.0.1` (IPv6 문제 해결)
- PostgreSQL: `pg_hba.conf` scram-sha-256 → md5 (psycopg2 호환)

**Flutter 수정**:
- `auth_dto.dart`: `refreshToken` 필드 추가
- `auth_repository.dart`: refresh_token 저장
- `auth_interceptor.dart`: 401 시 refresh_token으로 갱신 시도
- `auth_provider.dart`: `serverClientId` 웹/모바일 분기, `processGoogleAccount()` 추가
- `login_screen.dart`: 웹 `renderButton` / 모바일 커스텀 버튼 분기

#### 2. 이메일/비밀번호 로그인 제거 → Google 로그인 전용

**PWA 웹앱 수정** (서버):
- `/app/login.html`: 이메일/비밀번호 폼, 회원가입 탭 제거 → Google Sign-In 버튼만 배치
  - Google Identity Services (`google.accounts.id.initialize()` + `renderButton()`) 사용
  - Propedia Web Client ID: `846392940969-sv2936v0tm85j8hvdn3srcmtei1kk25e`
- `/app/profile.html`: 비밀번호 변경 버튼/모달 제거
  - 회원 탈퇴: 비밀번호 입력 → 2단계 확인(confirm) 방식으로 변경

#### 3. 정리 작업

- `backend/api/app_user.py` 삭제 (불필요)
- `backend/api/app.py`에서 `app_user_bp` 참조 제거
- `backend/api/app_auth.py` 디버그 로깅 제거

#### 4. Google Cloud Console 설정

- Propedia Web Client ID 생성: `846392940969-sv2936v0tm85j8hvdn3srcmtei1kk25e`
- OAuth 동의 화면: 테스트 → 프로덕션 전환
- People API 활성화

#### 5. Google Play Store 프로덕션 출시

- v1.0.2+8 (빌드 번호 8) AAB 업로드
- 프로덕션 트랙 출시 → Google 검토 통과 → **게시 완료**

#### 빌드 결과

- APK: 76.5MB / AAB: 61.3MB

#### 수정 파일 요약

| 파일 | 주요 변경 |
|------|----------|
| `auth_dto.dart` | refreshToken 필드 추가 |
| `auth_repository.dart` | refresh_token 저장 |
| `auth_interceptor.dart` | refresh token 갱신 로직 |
| `auth_provider.dart` | serverClientId 분기, processGoogleAccount |
| `login_screen.dart` | 웹 renderButton / 모바일 버튼 분기 |
| `web/index.html` | google-signin-client_id 메타 태그 추가 |
| 서버 `routes/app_auth.py` | Google 로그인 엔드포인트 |
| 서버 `services/app_user_service.py` | create_or_update_google_user |
| 서버 nginx 설정 | /app/api/auth/ → port 5000 |
| PWA `login.html` | Google 로그인 전용으로 변경 |
| PWA `profile.html` | 비밀번호 변경 기능 제거 |

---

### 2026-03-09: 웹 페이지 반응형 레이아웃 전환

모바일 앱 전용으로 설계된 `/app/` 및 루트(`/`) 웹 페이지를 데스크탑 브라우저에서도 적절히 표시되도록 반응형 레이아웃으로 전환. CSS 클래스(Tailwind)만 변경하여 기능 변경 없음.

#### 1. /app/ 페이지 반응형 전환 (10개 HTML)

- 모든 페이지의 `max-w-md` (448px) → `max-w-md md:max-w-3xl` (768px+에서 768px)
- result.html, search-map.html은 데이터 테이블/지도용으로 `md:max-w-4xl` 적용
- 하단 nav의 `pb-8` → `pb-8 md:pb-2` (데스크탑에서 불필요한 여백 제거)
- index.html 검색 카드: `flex flex-col` → `md:grid md:grid-cols-3` (데스크탑 3열 그리드)
- search-map.html 지도 높이: `h-[500px]` → `h-[500px] md:h-[600px]`

| 파일 | max-width | 비고 |
|------|-----------|------|
| `index.html` | md:max-w-3xl | 검색 카드 3열 그리드 |
| `search-road.html` | md:max-w-3xl | |
| `search-jibun.html` | md:max-w-3xl | |
| `history.html` | md:max-w-3xl | |
| `favorites.html` | md:max-w-3xl | |
| `profile.html` | md:max-w-3xl | |
| `login.html` | md:max-w-3xl | nav 없음 |
| `about.html` | md:max-w-3xl | nav 없음 |
| `result.html` | md:max-w-4xl | 데이터 테이블용 넓은 폭 |
| `search-map.html` | md:max-w-4xl | 지도 높이 600px |

#### 2. about.html 브랜딩 업데이트

- 운영사: `금토끼부동산` → `프롭넷 (Propnet)`
- 영문명 행 제거
- Copyright: `© 2024 금토끼부동산` → `© 2026 프롭넷 (PropNet)`
- 푸터: `© 2026 프롭넷 (PropNet). All rights reserved.`

#### 3. 개인정보처리방침/이용약관 페이지 복사

- `/privacy-policy.html` → `/app/privacy-policy.html` 복사
- `/terms-of-service.html` → `/app/terms-of-service.html` 복사
- 파비콘: `/proppedia/favicon.png` (Proppedia 전용)
- 브랜딩: `골든래빗` → `프롭넷`, 타이틀 `부동산백과 Proppedia`
- about.html 링크: `/privacy-policy.html` → `/app/privacy-policy.html` 등으로 변경

#### 4. 루트 페이지 (goldenrabbit.biz/) 반응형 전환

- `max-w-lg` (512px) → `max-w-lg md:max-w-3xl`
- 지도 높이: `h-[480px] md:h-[580px]`, 검색결과 지도: `h-[420px] md:h-[520px]`
- 매물 목록: `flex flex-col` → `grid grid-cols-1 md:grid-cols-2` (데스크탑 2열)
- 매물 상세 모달: `max-w-lg` 유지, 이미지 `max-h-[400px] object-cover`

#### 수정 파일 요약

| 파일 | 주요 변경 |
|------|----------|
| PWA `/app/*.html` (10개) | max-w-md → max-w-md md:max-w-3xl/4xl 반응형 |
| PWA `/app/about.html` | 프롭넷 브랜딩 업데이트 |
| PWA `/app/privacy-policy.html` | 신규 (루트에서 복사, 브랜딩 변경) |
| PWA `/app/terms-of-service.html` | 신규 (루트에서 복사, 브랜딩 변경) |
| 루트 `/index.html` | max-w-lg → max-w-lg md:max-w-3xl 반응형 |

---

## 업데이트 이력 (CHANGELOG)

> 아래는 버전별 변경 이력 요약입니다. 상세 내용은 위 개발일지를 참조하세요.

### 웹 반응형 전환 - 2026-03-09

- `/app/` 전체 10개 페이지 반응형 레이아웃 전환 (CSS만 변경, 기능 변경 없음)
- 루트 페이지(`/`) 반응형 레이아웃 전환
- about.html 프롭넷 브랜딩 업데이트
- `/app/` 전용 개인정보처리방침/이용약관 페이지 추가

### [1.0.2+9] - 2026-03-12

- **공지사항 팝업 시스템** 구현
  - 백엔드: `app_notices` DB 테이블, CRUD 서비스(`app_notice_service.py`)
  - 관리자 대시보드: 공지 등록/게시/중지/삭제/기간설정 UI 추가
  - API: `GET /app/api/notices` (공개), 관리자 CRUD 6개 엔드포인트
  - Flutter 앱: NoticeDto, NoticeApi, NoticeProvider, NoticeDialog
  - PWA 웹: `notice-popup.js` - 전 페이지 공지 팝업 지원
  - 공지 유형: error(API 오류), maintenance(점검), info(안내)
  - "오늘 하루 안보기" 기능 (SharedPreferences / localStorage)
  - 홈화면 진입 시 + 30분 주기 자동 공지 확인
- `/test` 명령에 **보안 취약점 검사** 통합 (시크릿 탐지, Android 보안, 의존성, SQL 인젝션)
- 릴리즈 프로세스 개선: CHANGELOG → progress_development.md 통합

### [1.0.2+8] - 2026-03-05 ~ 2026-03-08

- **Google 로그인** 전환 (이메일/비밀번호 제거)
- **통합 인증 시스템**: Property Manager에 Google 로그인 엔드포인트 통합
- JWT 시크릿 통일로 즐겨찾기/검색기록 401 에러 해결
- Refresh token 지원 (access 24h + refresh 30d)
- PWA 웹앱: Google Sign-In 전용 로그인, 비밀번호 변경 기능 제거
- PropNet 브랜딩 업데이트
- **Google Play Store 프로덕션 출시**

### [1.0.2+10] - 2026-03-14

- **Google 로그인 오류 수정**: serverClientId를 Proppedia Web Client ID로 교정 (Proptalk Web ID 혼용 문제 해결)
- **앱 버전 표시 자동화**: package_info_plus 도입, pubspec.yaml에서 자동 읽기 (하드코딩 제거)
- **웹 푸터 통일**: /app 전체 페이지 푸터를 `© 2026 프롭넷 (PropNet). All rights reserved.` 형식으로 통일
- **결과화면 UX 개선**: 즐겨찾기/PDF 하단 플로팅 버튼을 상단 헤더 아이콘으로 이동
- **웹 지번검색 개선**: 번/지 입력 시 법정동 자동 필터링 및 단일 결과 자동 선택
- **버전 업데이트 스크립트**: `scripts/update_version.py` 추가 (앱+서버 버전 일괄 변경)

### [1.0.2+10] - 2026-03-16

- **역할 기반 권한 시스템 (RBAC)**: `app_users.role` 컬럼 추가 (user/editor/admin)
- **Airtable 저장 기능**: 건물매물/공동주택매물 저장 (editor/admin 권한 전용)
  - 웹: result.html에 건물 유형별 저장 버튼 (단일건물: domain_add, 공동주택: apartment)
  - 앱: result_screen.dart AppBar에 조건부 저장 버튼 (미배포)
  - API: `/app/api/airtable/save/building`, `/multi-unit`, `/general` (인증+권한 보호)
- **관리자 대시보드 역할 관리**: 사용자 목록에 역할 드롭다운 추가
- **주소 포맷 개선**: 리 단위 주소 자동 추출, PNU fallback, plat_plc fallback
- **웹 PNU 검색 지원**: 즐겨찾기/검색기록에서 PNU 파라미터로 결과 조회
- **Property Manager 웹 UI 제거**: nginx 라우트, 템플릿, 블루프린트 정리
- **앱 지도 검색 레이아웃**: 지도 영역 확대(4/5), 하단 정보 축소(1/5), 패딩 축소

### [1.0.2+9] - 2026-03-12

- 버전 업데이트 (빌드 번호 증가)

### [1.0.2+8] - 2026-03-08

- **통합 인증 시스템**: Google Cloud 프로젝트 통일 (846392940969)
- Google 로그인 전환 (이메일/비밀번호 로그인 제거)
- 웹/모바일 플랫폼별 로그인 분기 처리
- 공지사항 팝업 시스템 구현 (앱 + PWA 웹)

### [1.0.2+7] - 2026-03-01

- 신규 행정구역 토지정보 조회 지원 (VWorld API fallback)
- 건물 없는 토지 도로명주소 표시
- 법정동 검색 정렬/필터링 개선
- 신규 행정구역 주소 자동 보정

### [1.0.2+6] - 2026-02-26

- 스켈레톤 로딩 UI 및 단계별 진행 메시지
- API 타임아웃 60초, 에러 화면 개선
- 화성시 신규 행정구역 25개동 old_bjdong_code 매핑

### [1.0.2+5] - 2026-02-25

- API 병렬 호출, 건축물대장 TTL 캐싱
- VWorld API 호출 최적화
- PWA 앱 Flutter 앱과 동기화

### [1.0.2+4] - 2026-02-24

- VWorld API TTL 캐싱 (토지 24h, 공시가격 7d)
- 신규 행정구역 검색 오류 수정 (구/신 법정동코드 분리)

### [1.0.2+3] - 2026-02-23

- 대규모 아파트 지원 (최대 20,000세대)
- 대지지분 조회 속도 개선 (3분 → 30초)

### [1.0.2+2] - 2026-02-19

- 지번 검색 UX 개선, 버튼 클릭 방식 변경

### [1.0.2+1] - 2026-02-19

- 로그인 필수 기능 강화, 지번 검색 UX 개선

### [1.0.1] - 2026-02-18

- 초기 릴리즈 (도로명/지번/지도 검색, 토지/건물 조회, PDF, 즐겨찾기)

### 버전 형식

`X.Y.Z+N` - Major.Minor.Patch+BuildNumber

---


# Propedia 프로젝트 구조

## 전체 디렉토리 트리

```
lib/
├── main.dart                          # 앱 진입점
├── app.dart                           # MaterialApp 설정
│
├── core/                              # 프레임워크 레벨 유틸리티
│   ├── ads/
│   │   └── ad_service.dart            # AdMob 광고 서비스
│   ├── constants/
│   │   ├── app_colors.dart            # 색상 상수
│   │   ├── app_text_styles.dart       # 텍스트 스타일 상수
│   │   └── terms.dart                 # 이용약관/개인정보처리방침
│   ├── database/
│   │   └── database_service.dart      # Hive 로컬 DB 서비스
│   ├── network/
│   │   ├── api_client.dart            # Dio HTTP 클라이언트
│   │   └── auth_interceptor.dart      # JWT 토큰 인터셉터
│   ├── pdf/
│   │   ├── pdf_fonts.dart             # PDF 폰트 로더
│   │   ├── pdf_generator.dart         # PDF 문서 생성
│   │   └── pdf_styles.dart            # PDF 스타일 정의
│   ├── router/
│   │   └── app_router.dart            # go_router 라우팅 설정
│   ├── storage/
│   │   ├── login_preferences.dart     # 로그인 설정 저장소
│   │   └── token_storage.dart         # 토큰 보안 저장소
│   └── utils/
│       └── jibun_address_parser.dart  # 지번 주소 파싱 유틸리티
│
├── data/                              # 데이터 레이어
│   ├── datasources/
│   │   └── remote/
│   │       ├── auth_api.dart          # 인증 API
│   │       ├── building_api.dart      # 건축물 검색 API
│   │       ├── favorites_api.dart     # 즐겨찾기 API
│   │       ├── history_api.dart       # 검색기록 API
│   │       ├── map_api.dart           # 지도 API
│   │       ├── naver_map_api.dart     # 네이버 지도 API
│   │       ├── airtable_api.dart      # Airtable 저장 API (권한 보호)
│   │       ├── property_api.dart      # 매물 API ★
│   │       └── user_api.dart          # 사용자 API
│   ├── dto/
│   │   ├── auth_dto.dart              # 인증 DTO
│   │   ├── building_dto.dart          # 건축물 DTO
│   │   ├── map_dto.dart               # 지도 DTO
│   │   ├── property_dto.dart          # 매물 DTO ★
│   │   └── user_stats_dto.dart        # 사용 통계 DTO
│   ├── models/
│   │   ├── favorite.dart              # 즐겨찾기 Hive 모델
│   │   └── search_history.dart        # 검색기록 Hive 모델
│   └── repositories/
│       ├── auth_repository.dart       # 인증 Repository
│       ├── building_repository.dart   # 건축물 Repository
│       ├── favorites_repository.dart  # 즐겨찾기 Repository
│       ├── history_repository.dart    # 검색기록 Repository
│       ├── map_repository.dart        # 지도 Repository
│       ├── property_repository.dart   # 매물 Repository ★
│       └── user_repository.dart       # 사용자 Repository
│
├── domain/                            # 도메인 레이어
│   └── entities/
│       └── user.dart                  # 사용자 엔티티
│
├── presentation/                      # UI 레이어
│   ├── providers/
│   │   ├── airtable_provider.dart     # Airtable 저장 상태 (권한 기반)
│   │   ├── auth_provider.dart         # 인증 상태 관리 + 권한 Provider
│   │   ├── building_provider.dart     # 건축물 검색 상태
│   │   ├── favorites_provider.dart    # 즐겨찾기 상태
│   │   ├── history_provider.dart      # 검색기록 상태
│   │   ├── map_provider.dart          # 지도 상태
│   │   ├── pdf_provider.dart          # PDF 생성 상태
│   │   ├── property_provider.dart     # 매물 상태 관리 ★
│   │   ├── theme_provider.dart        # 다크모드 상태
│   │   └── user_provider.dart         # 사용자 통계 상태
│   │
│   ├── screens/
│   │   ├── splash/
│   │   │   └── splash_screen.dart     # 스플래시 화면
│   │   ├── auth/
│   │   │   ├── login_screen.dart      # 로그인 화면
│   │   │   └── register_screen.dart   # 회원가입 화면
│   │   ├── home/
│   │   │   └── home_screen.dart       # Proppedia 홈 화면
│   │   ├── search/
│   │   │   ├── result_screen.dart        # 검색 결과
│   │   │   ├── search_jibun_screen.dart  # 지번 검색
│   │   │   ├── search_map_screen.dart    # 지도 검색
│   │   │   └── search_road_screen.dart   # 도로명 검색
│   │   ├── history/
│   │   │   └── history_screen.dart    # 검색기록 화면
│   │   ├── favorites/
│   │   │   └── favorites_screen.dart  # 즐겨찾기 화면
│   │   ├── profile/
│   │   │   └── profile_screen.dart    # 프로필/설정 화면
│   │   │
│   │   └── property/                  # ★ 금토끼부동산 매물 ★
│   │       ├── property_detail_screen.dart    # 매물 상세
│   │       ├── property_home_screen.dart      # 매물 홈 화면
│   │       ├── property_list_screen.dart      # 매물 목록 (카테고리 탭)
│   │       ├── property_map_screen.dart       # 매물 지도
│   │       ├── property_search_map_screen.dart # 매물 지도 검색
│   │       └── property_search_screen.dart    # 매물 조건 검색
│   │
│   └── widgets/
│       ├── ads/
│       │   └── banner_ad_widget.dart  # 배너 광고 위젯
│       ├── common/
│       │   ├── app_drawer.dart        # 앱 드로어 (햄버거 메뉴)
│       │   ├── app_footer.dart        # 앱 푸터 위젯
│       │   └── login_prompt_dialog.dart # 로그인 유도 다이얼로그
│       │
│       └── property/                  # ★ 매물 관련 위젯 ★
│           ├── property_card.dart     # 매물 카드
│           ├── property_image.dart    # 매물 이미지 (3단 fallback)
│           └── property_info_chips.dart # 카테고리별 정보 칩
│
└── shared/                            # 공유 유틸리티
    ├── extensions/
    └── theme/
        └── app_theme.dart             # 라이트/다크 테마
```

---

## 기능별 화면 구성

### 1. Proppedia (부동산백과) - 건축물 정보 조회

```
홈 화면 (home_screen.dart)
├── 도로명 검색 → search_road_screen.dart → result_screen.dart
├── 지번 검색   → search_jibun_screen.dart → result_screen.dart
└── 지도 검색   → search_map_screen.dart → result_screen.dart
```

**화면 흐름:**
```
┌─────────────────────────────────────────────────────────────┐
│                      Proppedia 홈                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  도로명검색  │ │   지번검색   │ │   지도검색   │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │                   │
│         └───────────────┼───────────────┘                   │
│                         ▼                                   │
│              ┌─────────────────────┐                        │
│              │    검색 결과 화면    │                        │
│              │  - 주소 정보        │                        │
│              │  - 토지 정보        │                        │
│              │  - 건축물 정보      │                        │
│              │  - 층별 정보        │                        │
│              │  - PDF 저장/공유    │                        │
│              └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

### 2. 금토끼부동산 - 매물 정보

```
매물 홈 화면 (property_home_screen.dart)
├── 추천매물    → property_list_screen.dart → property_detail_screen.dart
├── 매물 지도   → property_map_screen.dart → property_detail_screen.dart
└── 조건 검색   → property_search_screen.dart → property_list_screen.dart
```

**화면 흐름:**
```
┌─────────────────────────────────────────────────────────────┐
│                   금토끼부동산 매물 홈                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   추천매물   │ │   지도보기   │ │   조건검색   │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │                   │
│         ▼               ▼               ▼                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  매물 목록   │ │  매물 지도   │ │  검색 조건   │           │
│  │ (카테고리탭) │ │ (마커 표시)  │ │  입력 화면   │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │                   │
│         └───────────────┼───────────────┘                   │
│                         ▼                                   │
│              ┌─────────────────────┐                        │
│              │    매물 상세 화면    │                        │
│              │  - 이미지           │                        │
│              │  - 지번/매매가      │                        │
│              │  - 실투자금/수익률   │                        │
│              │  - 상세정보         │                        │
│              │  - 금토끼부동산 정보 │                        │
│              │  - 문의하기/지도/링크│                        │
│              └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 라우팅 구조 (app_router.dart)

```
/                           → SplashScreen (자동 인증 체크)
│
├── /login                  → LoginScreen
├── /register               → RegisterScreen
│
├── /home                   → HomeScreen (Proppedia 홈)
│   ├── /search/road        → SearchRoadScreen
│   ├── /search/jibun       → SearchJibunScreen
│   ├── /search/map         → SearchMapScreen
│   └── /result             → ResultScreen
│
├── /history                → HistoryScreen (검색기록)
├── /favorites              → FavoritesScreen (즐겨찾기)
├── /profile                → ProfileScreen (프로필/설정)
│
└── /property               → PropertyHomeScreen (금토끼부동산)
    ├── /property/list      → PropertyListScreen (매물 목록)
    ├── /property/detail/:id → PropertyDetailScreen (매물 상세)
    ├── /property/map       → PropertyMapScreen (매물 지도)
    └── /property/search    → PropertySearchScreen (조건 검색)
```

---

## 하단 네비게이션 구성

### Proppedia 앱
```
┌─────────┬─────────┬─────────┬─────────┐
│   홈    │ 검색기록 │ 즐겨찾기 │  프로필  │
│  /home  │/history │/favorites│/profile │
└─────────┴─────────┴─────────┴─────────┘
```

### 금토끼부동산 (property 화면)
```
┌─────────────┬─────────────┬─────────────┐
│   추천매물   │   지도보기   │   조건검색   │
│ /property/  │/property/map│/property/   │
│    list     │             │  search     │
└─────────────┴─────────────┴─────────────┘
```

---

## 매물 카테고리별 표시 정보

| 카테고리 | property_info_chips.dart 표시 |
|---------|------------------------------|
| 재건축용 토지 | 대지면적, 용도지역 |
| 고수익률 건물 | 대지면적, 수익률, 사용승인일 |
| 저가단독주택 | 대지면적, 층수, 사용승인일 |

---

## API 엔드포인트 매핑

### Proppedia (건축물 조회)
| 화면 | API 엔드포인트 |
|------|---------------|
| 도로명 검색 | POST /app/api/search/road |
| 지번 검색 | POST /app/api/search/jibun |
| 지도 검색 | POST /app/api/map/click-jibun |
| 결과 조회 | POST /app/api/search/bdmgtsn |

### 금토끼부동산 (매물)
| 화면 | API 엔드포인트 |
|------|---------------|
| 전체 목록 | GET /api/property-list |
| 카테고리별 | GET /api/category-properties?view= |
| 매물 상세 | GET /api/property-detail?id= |
| 조건 검색 | POST /api/search-map |
| 이미지 확인 | GET /api/check-image?record_id= |

---

*마지막 업데이트: 2026-02-23*

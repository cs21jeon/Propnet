# API 성능 최적화 방안

> 작성일: 2026-02-23
> 공공데이터포털/VWorld API 호출 딜레이 개선 검토

---

## 1. 현재 문제점

### 1.1 순차적 다중 API 호출

한 번의 검색 요청(`/search/jibun`)에서 **5~8개의 외부 API**를 순차적으로 호출합니다.

```
search_by_jibun() 요청 시 호출 순서:

1. building_service.search_building()
   ├─ _get_all_pages()           → 공공데이터포털 (전유부, 페이징)
   ├─ _get_attached_jibun_info() → 공공데이터포털 (부속지번)
   ├─ _get_recap_title_info()    → 공공데이터포털 (총괄표제부)
   └─ _get_title_info()          → 공공데이터포털 (표제부)

2. vworld_service.get_land_info()            → VWorld (토지특성)
3. vworld_service.get_individual_house_price() → VWorld (주택공시가격)
4. bjdong_service.get_by_code()              → 로컬 DB
```

### 1.2 외부 API 응답 시간

| API | 평균 응답 시간 | 비고 |
|-----|--------------|------|
| 공공데이터포털 | 500ms ~ 2초 | 트래픽에 따라 변동 |
| VWorld | 300ms ~ 1초 | 3년 반복 조회 시 ×3 |
| juso.go.kr | 200ms ~ 500ms | 비교적 안정적 |

### 1.3 현재 서버 설정

```python
# building_unified_service.py
self.api_delay = 0.25   # API 호출 간 250ms 딜레이
self.api_timeout = 30   # 타임아웃 30초
```

### 1.4 캐싱 현황

- 영속적인 캐싱 없음 (Redis, 파일 캐시 등)
- 메모리 캐시는 요청 단위로만 유지 (`cached_recap_data`, `cached_title_data`)

---

## 2. 개선 방안

### 2.1 병렬 API 호출

독립적인 API 호출을 동시에 처리합니다.

**적용 전 (순차):**
```python
building_result = building_service.search_building()  # 2초
land_info = vworld_service.get_land_info()            # 1.5초
house_price = vworld_service.get_individual_house_price()  # 1.5초
# 총 5초
```

**적용 후 (병렬):**
```python
import asyncio

results = await asyncio.gather(
    building_service.search_building_async(),
    vworld_service.get_land_info_async(),
    vworld_service.get_individual_house_price_async()
)
# 총 2초 (가장 느린 호출 기준)
```

**예상 효과:** 50~70% 응답시간 단축

**문제점:**
| 문제 | 설명 |
|------|------|
| 의존성 있는 호출 불가 | B가 A 결과를 필요로 하면 순차 처리 필수 |
| Rate Limit | 동시 호출 증가 → API 일일 할당량 빠르게 소진 |
| 에러 처리 복잡 | 일부 실패 시 부분 데이터 처리 로직 필요 |
| 서버 리소스 | 동시 연결 수 증가 → 메모리/스레드 부담 |
| 코드 복잡도 | Flask 동기 구조 → asyncio 적용 번거로움 |

---

### 2.2 인메모리 캐싱 (TTL Cache)

자주 조회되는 데이터를 서버 메모리에 저장합니다.

```python
from cachetools import TTLCache

# 설정: 최대 1,000개, 10분 후 만료
land_cache = TTLCache(maxsize=1000, ttl=600)

def get_land_info(pnu):
    if pnu in land_cache:
        return land_cache[pnu]  # 캐시 히트

    result = _fetch_from_vworld(pnu)
    land_cache[pnu] = result
    return result
```

**동작 방식:**
```
A사용자: "사당동 272-26" 조회
         ↓
서버: 공공API 호출 (3초) → 캐시에 저장
         ↓
A사용자: 결과 받음

--- 5분 후 ---

B사용자: "사당동 272-26" 조회
         ↓
서버: 캐시에서 바로 반환 (0.1초)
         ↓
B사용자: 결과 받음
```

**캐시 삭제 정책 (LRU):**
- 용량 초과 시 **가장 오랫동안 사용 안 한 것**부터 삭제
- 자주 조회되는 인기 지역은 캐시에 계속 남음

**권장 TTL 설정:**
| 데이터 종류 | TTL | 이유 |
|------------|-----|------|
| 토지 정보 | 24시간 | 거의 변경 없음 |
| 공시가격 | 7일 | 연 1회만 변경 |
| 건축물대장 | 1시간 | 가끔 변경됨 |

**예상 효과:** 재조회 시 90% 응답시간 단축

**문제점:**
| 문제 | 설명 |
|------|------|
| 오래된 데이터 (Stale Data) | 원본 변경 시 캐시는 옛날 데이터 반환 |
| 메모리 사용량 | maxsize 설정 필수 |
| 첫 조회는 여전히 느림 | 캐시 미스 시 API 호출 필요 |
| 디버깅 어려움 | 사용자마다 다른 결과 (캐시 히트/미스) |
| 캐시 무효화 | 데이터 변경 시 캐시 삭제 로직 필요 |

**Proppedia에서 캐싱이 유리한 이유:**
- 외부 공공데이터 읽기 전용 → 무효화 복잡성 낮음
- 공시가격/건축물대장 변경 빈도 낮음 (연 1회 수준)
- 대단지 아파트/인기 지역 조회 집중 → 캐시 히트율 높음

---

### 2.3 응답 분할 (Lazy Loading)

기본 정보를 먼저 반환하고, 상세 정보는 별도 요청으로 분리합니다.

```
요청 1: /search/jibun (빠른 응답 ~1초)
  → 주소, 건물유형, 토지기본정보 반환

요청 2: /search/detail (지연 로딩 ~2초)
  → 공시가격, 층별정보, 동호정보 반환
```

**예상 효과:** 초기 화면 표시 50% 단축

**문제점:**
- 앱 + 서버 양쪽 수정 필요
- API 설계 변경 → 호환성 고려 필요

---

### 2.4 VWorld API 호출 최적화

현재 3년 순차 조회를 개선합니다.

**현재:**
```python
for year_offset in range(3):  # 최악의 경우 3번 호출
    target_year = current_year - year_offset
    response = requests.get(url, params=params)
    if data_exists:
        break
```

**개선안:**
```python
# 1. 최신년도 1회만 시도 (대부분 성공)
# 2. 실패 시에만 이전년도 시도
# 3. 결과 캐싱으로 재시도 방지
```

**예상 효과:** VWorld 호출 20~30% 단축

---

### 2.5 로딩 UX 개선 (앱 측)

서버 수정 없이 체감 속도를 개선합니다.

```dart
// 스켈레톤 로딩 UI
if (state.isLoading) {
  return Shimmer.fromColors(
    child: BuildingInfoSkeleton(),
  );
}

// 단계별 로딩 메시지
"주소 확인 중..." → "토지 정보 조회 중..." → "건물 정보 조회 중..."
```

---

## 3. 방안별 비교

| 방안 | 첫 조회 개선 | 재조회 개선 | 구현 난이도 | 위험도 |
|------|:----------:|:----------:|:----------:|:------:|
| 병렬 호출 | ◎ 50% | ◎ 50% | 중간 | 중간 |
| 캐싱 | ✗ | ◎ 90% | 낮음 | 낮음 |
| 응답 분할 | ○ 30% | ○ 30% | 높음 | 중간 |
| VWorld 최적화 | ○ 20% | ○ 20% | 낮음 | 낮음 |
| 로딩 UX | 체감 개선 | 체감 개선 | 낮음 | 낮음 |

---

## 4. 권장 적용 순서

### Phase 1: 즉시 적용 가능 (낮은 위험) ✅ 완료

1. **VWorld API 최적화** - 3년 반복 조회 개선 ✅ (2026-02-25)
   - 1-3월에는 전년도 데이터부터 조회
2. **인메모리 캐싱** - TTLCache 적용 ✅ (2026-02-24~25)
   - VWorld: 토지정보 24시간, 공시가격 7일
   - 건축물대장: 총괄표제부/표제부/전유부 1시간
3. **로딩 UX 개선** - 스켈레톤 UI, 단계별 메시지 ✅ (2026-02-26)
   - Flutter 앱: Shimmer 기반 스켈레톤 UI
   - PWA 앱: CSS animate-pulse 스켈레톤 UI
   - 시간 기반 단계별 메시지 (0~40초+)
   - 에러 화면에 "다시 시도" 버튼 추가

### Phase 2: 중기 개선 (중간 위험) ✅ 완료

4. **병렬 API 호출** - 독립적인 호출만 병렬화 ✅ (2026-02-25)
   - Phase 1: 건물정보, 부속지번, 법정동 주소 병렬 처리
   - Phase 2: 의존성 있는 API 순차 처리

### Phase 3: 장기 개선 (높은 위험)

5. **응답 분할** - API 구조 변경

---

## 5. 예상 개선 효과

| 단계 | 첫 조회 | 재조회 |
|------|:------:|:------:|
| 현재 | 3~5초 | 3~5초 |
| Phase 1 적용 후 | 2~3초 | 0.2초 |
| Phase 2 적용 후 | 1~2초 | 0.2초 |

---

## 6. 모니터링 권장 사항

캐싱 적용 시 다음 지표를 모니터링합니다:

```python
# 로깅 예시
logger.info(f"Cache HIT: {pnu}")
logger.info(f"Cache MISS: {pnu}")
logger.info(f"Cache size: {len(cache)}/{cache.maxsize}")
```

| 지표 | 목표 |
|------|------|
| 캐시 히트율 | 30% 이상 |
| 평균 응답 시간 | 2초 이하 |
| API Rate Limit 사용률 | 80% 이하 |

---

## 7. 참고: 캐시 키 구조

```python
# PNU(필지고유번호) 19자리 기준
cache_key = "1162010100102720026"  # 사당동 272-26

# 공동주택은 동/호 포함
cache_key = "1162010100102720026_101동_201호"
```

---

*문서 끝*

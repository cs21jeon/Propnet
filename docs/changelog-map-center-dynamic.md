# 지도 center 좌표 동적화

> 날짜: 2026-04-08
> 변경 파일: propsheet.py, map.html (goldenrabbit, silverrabbit, 루트)

## 개요

PropMap 지도의 초기 center 좌표를 하드코딩에서 DB 기반 동적 조회로 변경했다.
기존에는 agent별 map.html에 좌표가 하드코딩되어 있어 새 agent 추가 시 수동 수정이 필요했다.

## 변경 내용

### 1. API (propsheet.py)

`map-data` API 응답의 agent 정보에 `latitude`, `longitude` 필드 추가:

```python
# 변경 전
'SELECT a.name, a.agency_name, a.phone, a.address, a.license_no, a.slug '

# 변경 후
'SELECT a.name, a.agency_name, a.phone, a.address, a.license_no, a.slug, a.latitude, a.longitude '
```

### 2. map.html (3개 파일 공통)

- `/propmap/goldenrabbit/map.html`
- `/propmap/silverrabbit/map.html`
- `/map.html` (루트)

```javascript
// 변경 전: 하드코딩 좌표
center: new kakao.maps.LatLng(37.4834458778777, 126.970207234818),

// 변경 후: 임시 center(서울시청) + API 응답 후 agent 좌표로 이동
center: new kakao.maps.LatLng(37.5665, 126.9780),

// API 응답 처리부에 추가
if (data.agent.latitude && data.agent.longitude) {
    map.setCenter(new kakao.maps.LatLng(data.agent.latitude, data.agent.longitude));
}
```

## 효과

- 새 agent 가입 시 DB의 agents 테이블에 주소/좌표만 등록하면 지도 center가 자동 설정됨
- 기존 agent 주소 변경 시 DB만 수정하면 map.html 수정 불필요

# Phase 7 성능 검토 보고서

## 개요
현재 구현된 매물 기능의 성능 영향 요소를 분석하고 개선 방안을 제시합니다.

---

## 1. 데이터 로딩 문제

### 문제점 1: 페이지네이션 없음 ⚠️ **심각**

**현재 코드:**
```dart
// property_api.dart
Future<PropertyListResponse> getPropertyList() async {
  final response = await _dio.get('/api/property-list');
  return PropertyListResponse.fromJson(response.data);  // 전체 415개 한번에 로드
}
```

**영향:**
- 415개 매물 데이터를 한 번에 다운로드 (예상 크기: 500KB~1MB)
- 초기 로딩 시간 증가 (3G 네트워크: 3-5초)
- 메모리 사용량 증가

**개선 방안:**
```dart
// 페이지네이션 추가
Future<PropertyListResponse> getPropertyList({int page = 1, int limit = 20}) async {
  final response = await _dio.get('/api/property-list',
    queryParameters: {'page': page, 'limit': limit});
  return PropertyListResponse.fromJson(response.data);
}
```

---

### 문제점 2: 카테고리 변경 시 캐싱 없음 ⚠️ **중간**

**현재 코드:**
```dart
// property_provider.dart
Future<void> changeCategory(PropertyCategory category) async {
  if (state.category == category && state.status == SearchStatus.success) {
    return; // 같은 카테고리만 캐시
  }
  await loadProperties(category: category);  // 매번 새로 로드
}
```

**영향:**
- 탭 전환 시마다 API 호출
- 불필요한 네트워크 요청
- 사용자 경험 저하 (로딩 반복)

**개선 방안:**
```dart
// 카테고리별 캐시 Map 사용
class PropertyListState {
  final Map<PropertyCategory, List<PropertyRecord>> categoryCache;
  // ...
}
```

---

### 문제점 3: JSON 파싱 메인 스레드에서 실행 ⚠️ **중간**

**현재 코드:**
```dart
// property_api.dart
return PropertyListResponse.fromJson(response.data);  // 메인 스레드
```

**영향:**
- 415개 레코드 파싱 시 UI 프레임 드랍 가능
- 복잡한 nested 객체 (PropertyFields, AirtableAttachment)

**개선 방안:**
```dart
import 'package:flutter/foundation.dart';

// Isolate에서 파싱
final result = await compute(_parsePropertyList, response.data);

static PropertyListResponse _parsePropertyList(Map<String, dynamic> json) {
  return PropertyListResponse.fromJson(json);
}
```

---

## 2. 이미지 로딩 문제

### 문제점 4: 목록에서 모든 이미지 동시 로드 ⚠️ **심각**

**현재 코드:**
```dart
// property_card.dart - ListView.builder 내에서
CachedNetworkImage(
  imageUrl: imageUrl,
  fit: BoxFit.cover,
  // memCacheHeight/Width 없음
)
```

**영향:**
- 화면에 보이지 않는 이미지도 로드 시도
- 메모리 사용량 급증 (원본 이미지 크기 그대로 캐시)
- 스크롤 시 버벅임

**개선 방안:**
```dart
CachedNetworkImage(
  imageUrl: imageUrl,
  fit: BoxFit.cover,
  memCacheHeight: 360,  // 표시 크기의 2배 (180 * 2)
  memCacheWidth: 600,   // 디바이스 너비 기준
  fadeInDuration: const Duration(milliseconds: 200),
  fadeOutDuration: const Duration(milliseconds: 200),
)
```

---

### 문제점 5: 이미지 URL 체크 API 미활용 ⚠️ **낮음**

**현재 코드:**
```dart
// property_card.dart
// imageBaseUrl이 있어도 check-image API 호출하지 않음
if (imageUrl == null && imageBaseUrl != null) {
  // 이미지 존재 여부는 별도 확인 필요 - 일단 placeholder 표시
}
```

**영향:**
- 백업 이미지 있어도 사용 못함
- 불필요한 placeholder 표시

---

## 3. 목록 렌더링 문제

### 문제점 6: Card Key 미지정 ⚠️ **낮음**

**현재 코드:**
```dart
// property_list_screen.dart
ListView.builder(
  itemCount: state.properties.length,
  itemBuilder: (context, index) {
    final property = state.properties[index];
    return PropertyCard(
      property: property,  // key 없음
      onTap: () { ... },
    );
  },
)
```

**영향:**
- 목록 변경 시 불필요한 위젯 rebuild
- 애니메이션 깜빡임 가능

**개선 방안:**
```dart
return PropertyCard(
  key: ValueKey(property.id),  // 고유 키 지정
  property: property,
  onTap: () { ... },
);
```

---

### 문제점 7: 상세 화면 상태 공유 ⚠️ **중간**

**현재 코드:**
```dart
// property_detail_screen.dart
@override
void initState() {
  super.initState();
  WidgetsBinding.instance.addPostFrameCallback((_) {
    ref.read(propertyDetailProvider.notifier).loadDetail(widget.recordId);
  });
}
```

**영향:**
- 목록에서 이미 로드한 데이터를 다시 API 호출
- 불필요한 네트워크 요청

**개선 방안:**
```dart
// 목록에서 상세로 데이터 전달
final propertyDetailProvider = StateNotifierProvider.family<
    PropertyDetailNotifier, PropertyDetailState, String>((ref, recordId) {
  // 캐시에서 먼저 확인
  final listState = ref.read(propertyListProvider);
  final cached = listState.properties.firstWhereOrNull((p) => p.id == recordId);
  return PropertyDetailNotifier(cached: cached);
});
```

---

## 4. 지도 성능 문제

### 문제점 8: 마커 일괄 추가 ⚠️ **잠재적**

**현재 코드:**
```dart
// property_map_screen.dart
void _addPropertyMarkers(List<PropertyRecord> properties) async {
  final markers = <Marker>[];
  for (final property in properties) {
    // 모든 매물에 대해 마커 생성
    markers.add(Marker(...));
  }
  await _mapController!.addMarker(markers: markers);  // 한번에 추가
}
```

**영향:**
- 400개 이상 마커 동시 추가 시 지도 렌더링 지연
- 모바일에서 심각한 성능 저하 가능

**개선 방안:**
```dart
// 1. 클러스터링 적용
// 2. 뷰포트 내 마커만 표시
// 3. 줌 레벨에 따른 마커 수 제한
void _addVisibleMarkers(LatLngBounds bounds, int zoomLevel) {
  final visibleProperties = properties.where((p) {
    final coords = _extractCoordinates(p);
    return coords != null && bounds.contains(LatLng(coords['lat']!, coords['lon']!));
  }).take(50);  // 최대 50개로 제한
  // ...
}
```

---

## 5. 검색 성능 문제

### 문제점 9: 검색 디바운싱 없음 ⚠️ **낮음**

**현재 코드:**
```dart
// property_search_screen.dart
void _search() {
  if (_formKey.currentState?.validate() ?? false) {
    ref.read(propertySearchProvider.notifier).search(...);  // 즉시 실행
  }
}
```

**영향:**
- 버튼 연타 시 중복 API 호출

**개선 방안:**
```dart
// 디바운서 또는 로딩 중 비활성화
bool _isSearching = false;

void _search() async {
  if (_isSearching) return;
  _isSearching = true;
  try {
    await ref.read(propertySearchProvider.notifier).search(...);
  } finally {
    _isSearching = false;
  }
}
```

---

## 6. 메모리 문제

### 문제점 10: Provider 상태 누적 ⚠️ **낮음**

**현재 코드:**
```dart
// 전역 Provider - 앱 종료까지 유지
final propertyListProvider = StateNotifierProvider<...>((ref) { ... });
```

**영향:**
- 415개 PropertyRecord 객체가 메모리에 상주
- 이미지 캐시와 함께 메모리 압박

**개선 방안:**
```dart
// AutoDispose 적용 (화면 떠나면 해제)
final propertyListProvider = StateNotifierProvider.autoDispose<...>((ref) {
  ref.keepAlive();  // 필요시 유지
  return PropertyListNotifier(...);
});
```

---

## 성능 영향도 요약

| 문제 | 심각도 | 영향 범위 | 수정 난이도 |
|-----|--------|----------|------------|
| 페이지네이션 없음 | 🔴 심각 | 초기 로딩, 메모리 | 서버 수정 필요 |
| 이미지 동시 로드 | 🔴 심각 | 스크롤, 메모리 | 쉬움 |
| 카테고리 캐싱 없음 | 🟡 중간 | 탭 전환 | 쉬움 |
| JSON 메인 스레드 파싱 | 🟡 중간 | UI 프레임 | 쉬움 |
| 상세 데이터 재로드 | 🟡 중간 | 상세 화면 진입 | 중간 |
| 지도 마커 일괄 추가 | 🟡 잠재적 | 지도 화면 | 중간 |
| Card Key 미지정 | 🟢 낮음 | 목록 갱신 | 쉬움 |
| 검색 디바운싱 | 🟢 낮음 | 검색 | 쉬움 |
| 이미지 API 미활용 | 🟢 낮음 | 이미지 표시 | 중간 |
| Provider 상태 누적 | 🟢 낮음 | 장시간 사용 | 쉬움 |

---

## 즉시 적용 가능한 개선 (코드 변경만)

### 1. 이미지 메모리 캐시 최적화
```dart
// property_card.dart
CachedNetworkImage(
  imageUrl: imageUrl,
  fit: BoxFit.cover,
  memCacheHeight: 360,
  memCacheWidth: 600,
)
```

### 2. Card Key 추가
```dart
// property_list_screen.dart
return PropertyCard(
  key: ValueKey(property.id),
  property: property,
  ...
);
```

### 3. 카테고리 캐싱
```dart
// property_provider.dart
class PropertyListState {
  final Map<PropertyCategory, List<PropertyRecord>> cache;
  // 카테고리별 데이터 캐싱
}
```

---

## 서버 수정 필요한 개선

### 1. 페이지네이션 API
```python
# app.py
@app.route('/api/property-list')
def property_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    offset = (page - 1) * limit

    properties = all_properties[offset:offset + limit]
    return jsonify({
        'records': properties,
        'page': page,
        'total': len(all_properties),
        'hasMore': offset + limit < len(all_properties)
    })
```

### 2. 축소된 목록 데이터 API
```python
# 목록용 최소 필드만 반환
@app.route('/api/property-list-minimal')
def property_list_minimal():
    minimal = []
    for p in all_properties:
        minimal.append({
            'id': p['id'],
            'fields': {
                '지번 주소': p['fields'].get('지번 주소'),
                '매가(만원)': p['fields'].get('매가(만원)'),
                '토지면적(㎡)': p['fields'].get('토지면적(㎡)'),
                '융자제외수익률(%)': p['fields'].get('융자제외수익률(%)'),
                '층수': p['fields'].get('층수'),
                '대표사진': p['fields'].get('대표사진'),  # 썸네일 URL만
            }
        })
    return jsonify({'records': minimal})
```

---

## 결론

**즉시 조치 필요:**
1. 이미지 `memCacheHeight/Width` 추가
2. `ValueKey` 추가

**단기 개선 (클라이언트):**
3. 카테고리별 캐싱 구현
4. `compute()` 사용한 JSON 파싱

**중기 개선 (서버 필요):**
5. 페이지네이션 API 구현
6. 목록용 최소 데이터 API 구현

현재 415개 매물 규모에서는 큰 문제가 없지만, 매물 수가 증가하면 성능 저하가 발생할 수 있습니다.

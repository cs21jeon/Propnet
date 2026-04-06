import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:propedia/data/datasources/remote/property_api.dart';
import 'package:propedia/data/dto/property_dto.dart';
import 'package:propedia/data/repositories/property_repository.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';
import 'package:propedia/presentation/providers/building_provider.dart';

// =============================================================================
// Provider 정의
// =============================================================================

// PropertyApi Provider
final propertyApiProvider = Provider<PropertyApi>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return PropertyApi(apiClient.dio);
});

// PropertyRepository Provider
final propertyRepositoryProvider = Provider<PropertyRepository>((ref) {
  final propertyApi = ref.watch(propertyApiProvider);
  return PropertyRepository(propertyApi: propertyApi);
});

// 선택된 카테고리 Provider
final selectedCategoryProvider = StateProvider<PropertyCategory>((ref) {
  return PropertyCategory.reconstruction;
});

// =============================================================================
// 매물 목록 상태
// =============================================================================
class PropertyListState {
  final SearchStatus status;
  final List<PropertyRecord> properties;
  final String? errorMessage;
  final PropertyCategory category;

  const PropertyListState({
    this.status = SearchStatus.initial,
    this.properties = const [],
    this.errorMessage,
    this.category = PropertyCategory.reconstruction,
  });

  PropertyListState copyWith({
    SearchStatus? status,
    List<PropertyRecord>? properties,
    String? errorMessage,
    PropertyCategory? category,
  }) {
    return PropertyListState(
      status: status ?? this.status,
      properties: properties ?? this.properties,
      errorMessage: errorMessage,
      category: category ?? this.category,
    );
  }
}

// =============================================================================
// 매물 목록 Notifier
// =============================================================================
class PropertyListNotifier extends StateNotifier<PropertyListState> {
  final PropertyRepository _repository;

  PropertyListNotifier(this._repository) : super(const PropertyListState());

  /// 매물 목록 로드
  Future<void> loadProperties({PropertyCategory category = PropertyCategory.reconstruction}) async {
    state = state.copyWith(status: SearchStatus.loading, category: category);
    debugPrint('🏠 매물 목록 로드 시작: ${category.label}');

    try {
      final properties = await _repository.getCategoryProperties(category);
      state = PropertyListState(
        status: SearchStatus.success,
        properties: properties,
        category: category,
      );
      debugPrint('✅ 매물 목록 로드 완료: ${properties.length}개');
    } catch (e) {
      debugPrint('❌ 매물 목록 로드 에러: $e');
      state = PropertyListState(
        status: SearchStatus.error,
        errorMessage: e.toString().replaceFirst('Exception: ', ''),
        category: category,
      );
    }
  }

  /// 카테고리 변경
  Future<void> changeCategory(PropertyCategory category) async {
    if (state.category == category && state.status == SearchStatus.success) {
      return; // 이미 로드된 카테고리
    }
    await loadProperties(category: category);
  }

  /// 새로고침
  Future<void> refresh() async {
    await loadProperties(category: state.category);
  }

  void reset() {
    state = const PropertyListState();
  }
}

final propertyListProvider =
    StateNotifierProvider<PropertyListNotifier, PropertyListState>((ref) {
  final repository = ref.watch(propertyRepositoryProvider);
  return PropertyListNotifier(repository);
});

// =============================================================================
// 매물 상세 상태
// =============================================================================
class PropertyDetailState {
  final SearchStatus status;
  final PropertyRecord? property;
  final String? errorMessage;

  const PropertyDetailState({
    this.status = SearchStatus.initial,
    this.property,
    this.errorMessage,
  });

  PropertyDetailState copyWith({
    SearchStatus? status,
    PropertyRecord? property,
    String? errorMessage,
  }) {
    return PropertyDetailState(
      status: status ?? this.status,
      property: property ?? this.property,
      errorMessage: errorMessage,
    );
  }
}

// =============================================================================
// 매물 상세 Notifier
// =============================================================================
class PropertyDetailNotifier extends StateNotifier<PropertyDetailState> {
  final PropertyRepository _repository;

  PropertyDetailNotifier(this._repository) : super(const PropertyDetailState());

  /// 매물 상세 로드
  Future<void> loadDetail(String recordId, {int? dbId}) async {
    state = const PropertyDetailState(status: SearchStatus.loading);
    debugPrint('🏠 매물 상세 로드: $recordId (dbId=$dbId)');

    try {
      final property = await _repository.getPropertyDetail(recordId, dbId: dbId);
      if (property != null) {
        state = PropertyDetailState(
          status: SearchStatus.success,
          property: property,
        );
        debugPrint('✅ 매물 상세 로드 완료');
      } else {
        state = const PropertyDetailState(
          status: SearchStatus.error,
          errorMessage: '매물을 찾을 수 없습니다',
        );
      }
    } catch (e) {
      debugPrint('❌ 매물 상세 로드 에러: $e');
      state = PropertyDetailState(
        status: SearchStatus.error,
        errorMessage: e.toString().replaceFirst('Exception: ', ''),
      );
    }
  }

  void reset() {
    state = const PropertyDetailState();
  }
}

final propertyDetailProvider =
    StateNotifierProvider<PropertyDetailNotifier, PropertyDetailState>((ref) {
  final repository = ref.watch(propertyRepositoryProvider);
  return PropertyDetailNotifier(repository);
});

// =============================================================================
// 매물 검색 상태
// =============================================================================
class PropertySearchState {
  final SearchStatus status;
  final int count;
  final String? mapHtml;
  final List<PropertyRecord> results;
  final List<PropertyMapMarker> markers;
  final Map<String, dynamic>? statistics;
  final String? errorMessage;

  const PropertySearchState({
    this.status = SearchStatus.initial,
    this.count = 0,
    this.mapHtml,
    this.results = const [],
    this.markers = const [],
    this.statistics,
    this.errorMessage,
  });

  PropertySearchState copyWith({
    SearchStatus? status,
    int? count,
    String? mapHtml,
    List<PropertyRecord>? results,
    List<PropertyMapMarker>? markers,
    Map<String, dynamic>? statistics,
    String? errorMessage,
  }) {
    return PropertySearchState(
      status: status ?? this.status,
      count: count ?? this.count,
      mapHtml: mapHtml ?? this.mapHtml,
      results: results ?? this.results,
      markers: markers ?? this.markers,
      statistics: statistics ?? this.statistics,
      errorMessage: errorMessage,
    );
  }
}

// =============================================================================
// 매물 검색 Notifier
// =============================================================================
class PropertySearchNotifier extends StateNotifier<PropertySearchState> {
  final PropertyRepository _repository;

  PropertySearchNotifier(this._repository) : super(const PropertySearchState());

  /// 조건 검색
  Future<void> search({
    String? priceValue,
    String priceCondition = 'all',
    String? yieldValue,
    String yieldCondition = 'all',
    String? investmentValue,
    String investmentCondition = 'all',
    String? areaValue,
    String areaCondition = 'all',
  }) async {
    state = const PropertySearchState(status: SearchStatus.loading);
    debugPrint('🔍 매물 검색: price=$priceValue, yield=$yieldValue, area=$areaValue');

    try {
      final response = await _repository.searchProperties(
        priceValue: priceValue,
        priceCondition: priceCondition,
        yieldValue: yieldValue,
        yieldCondition: yieldCondition,
        investmentValue: investmentValue,
        investmentCondition: investmentCondition,
        areaValue: areaValue,
        areaCondition: areaCondition,
      );

      state = PropertySearchState(
        status: SearchStatus.success,
        count: response.count,
        mapHtml: response.mapHtml,
        results: response.properties,
        markers: response.markers,
        statistics: response.statistics,
      );
      debugPrint('✅ 매물 검색 완료: ${response.count}개, 마커: ${response.markers.length}개');
    } catch (e) {
      debugPrint('❌ 매물 검색 에러: $e');
      state = PropertySearchState(
        status: SearchStatus.error,
        errorMessage: e.toString().replaceFirst('Exception: ', ''),
      );
    }
  }

  void reset() {
    state = const PropertySearchState();
  }
}

final propertySearchProvider =
    StateNotifierProvider<PropertySearchNotifier, PropertySearchState>((ref) {
  final repository = ref.watch(propertyRepositoryProvider);
  return PropertySearchNotifier(repository);
});

// =============================================================================
// 지도 데이터 Provider (마커 + 좌표 통합)
// =============================================================================
final mapDataProvider = FutureProvider<MapDataResponse>((ref) async {
  final api = ref.watch(propertyApiProvider);
  return api.getMapData();
});

// 좌표 데이터 Provider (map-data에서 추출)
final coordinatesProvider = FutureProvider<Map<String, PropertyCoordinate>>((ref) async {
  final mapData = await ref.watch(mapDataProvider.future);
  final coords = <String, PropertyCoordinate>{};
  for (final marker in mapData.markers) {
    if (marker.recordId != null) {
      coords[marker.recordId!] = PropertyCoordinate(
        lat: marker.lat,
        lon: marker.lon,
        address: marker.address,
      );
    }
  }
  debugPrint('📍 좌표 로드 완료: ${coords.length}개');
  return coords;
});

// 전체 매물 목록 Provider (지도용 - map-data 마커를 PropertyRecord로 변환)
final allPropertiesProvider = FutureProvider<List<PropertyRecord>>((ref) async {
  final mapData = await ref.watch(mapDataProvider.future);
  return mapData.markers.map((m) => PropertyRecord(
    id: m.recordId ?? m.markerId,
    fields: PropertyFields(
      address: m.address,
      price: m.price?.toInt(),
      yieldRate: m.yieldRate,
      landArea: m.area,
      floors: m.floors,
      mainUsage: m.usage,
      approvalDate: m.approvalDate,
    ),
  )).toList();
});

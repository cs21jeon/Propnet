import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:propedia/data/datasources/remote/map_api.dart';
import 'package:propedia/data/dto/map_dto.dart';
import 'package:propedia/data/repositories/map_repository.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';
import 'package:propedia/presentation/providers/building_provider.dart';

// MapApi Provider
final mapApiProvider = Provider<MapApi>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return MapApi(apiClient.dio);
});

// MapRepository Provider
final mapRepositoryProvider = Provider<MapRepository>((ref) {
  final mapApi = ref.watch(mapApiProvider);
  return MapRepository(mapApi: mapApi);
});

// 지도 검색 상태
class MapSearchState {
  final SearchStatus status;
  final JibunInfo? jibunInfo;
  final double? selectedLat;
  final double? selectedLng;
  final ParcelGeometry? parcelGeometry;
  final ParcelProperties? parcelProperties;
  final String? errorMessage;

  const MapSearchState({
    this.status = SearchStatus.initial,
    this.jibunInfo,
    this.selectedLat,
    this.selectedLng,
    this.parcelGeometry,
    this.parcelProperties,
    this.errorMessage,
  });

  MapSearchState copyWith({
    SearchStatus? status,
    JibunInfo? jibunInfo,
    double? selectedLat,
    double? selectedLng,
    ParcelGeometry? parcelGeometry,
    ParcelProperties? parcelProperties,
    String? errorMessage,
  }) {
    return MapSearchState(
      status: status ?? this.status,
      jibunInfo: jibunInfo ?? this.jibunInfo,
      selectedLat: selectedLat ?? this.selectedLat,
      selectedLng: selectedLng ?? this.selectedLng,
      parcelGeometry: parcelGeometry ?? this.parcelGeometry,
      parcelProperties: parcelProperties ?? this.parcelProperties,
      errorMessage: errorMessage,
    );
  }

  MapSearchState reset() {
    return const MapSearchState();
  }
}

// 지도 검색 Notifier
class MapSearchNotifier extends StateNotifier<MapSearchState> {
  final MapRepository _repository;

  MapSearchNotifier(this._repository) : super(const MapSearchState());

  /// 좌표로 검색 (지도 클릭 시)
  Future<void> searchByCoordinate(double lat, double lng) async {
    state = MapSearchState(
      status: SearchStatus.loading,
      selectedLat: lat,
      selectedLng: lng,
    );
    debugPrint('🗺️ 지도 클릭: lat=$lat, lng=$lng');

    try {
      // 1. 좌표 → 지번 변환
      final jibunResponse = await _repository.clickToJibun(lat: lat, lng: lng);

      if (!jibunResponse.success || jibunResponse.jibunInfo == null) {
        state = MapSearchState(
          status: SearchStatus.error,
          selectedLat: lat,
          selectedLng: lng,
          errorMessage: jibunResponse.error ?? '해당 위치의 지번 정보를 찾을 수 없습니다',
        );
        return;
      }

      final jibunInfo = jibunResponse.jibunInfo!;
      debugPrint('✅ 지번 변환 성공: ${jibunInfo.address}');

      // 2. 필지 경계 조회
      final boundaryResponse = await _repository.getParcelBoundary(
        pnu: jibunInfo.pnu,
        lat: lat,
        lng: lng,
      );

      state = MapSearchState(
        status: SearchStatus.success,
        jibunInfo: jibunInfo,
        selectedLat: lat,
        selectedLng: lng,
        parcelGeometry: boundaryResponse.success ? boundaryResponse.geometry : null,
        parcelProperties: boundaryResponse.success ? boundaryResponse.properties : null,
      );
    } catch (e) {
      debugPrint('❌ 지도 검색 에러: $e');
      state = MapSearchState(
        status: SearchStatus.error,
        selectedLat: lat,
        selectedLng: lng,
        errorMessage: e.toString().replaceFirst('Exception: ', ''),
      );
    }
  }

  void resetState() {
    state = const MapSearchState();
  }
}

final mapSearchProvider =
    StateNotifierProvider<MapSearchNotifier, MapSearchState>((ref) {
  final repository = ref.watch(mapRepositoryProvider);
  return MapSearchNotifier(repository);
});

// 지오코딩 Provider (주소 → 좌표)
final geocodingProvider = FutureProvider.family<GeocodingResponse, String>((ref, address) async {
  final repository = ref.watch(mapRepositoryProvider);
  return repository.geocodeAddress(address);
});

// 현재 위치 Provider
final currentLocationProvider = FutureProvider<Position?>((ref) async {
  try {
    // 위치 서비스 활성화 확인
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      debugPrint('📍 위치 서비스가 비활성화되어 있습니다');
      return null;
    }

    // 위치 권한 확인
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        debugPrint('📍 위치 권한이 거부되었습니다');
        return null;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      debugPrint('📍 위치 권한이 영구적으로 거부되었습니다');
      return null;
    }

    // 현재 위치 가져오기
    final position = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
    );
    debugPrint('📍 현재 위치: ${position.latitude}, ${position.longitude}');
    return position;
  } catch (e) {
    debugPrint('📍 위치 가져오기 실패: $e');
    return null;
  }
});

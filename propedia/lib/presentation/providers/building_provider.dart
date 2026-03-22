import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:propedia/data/datasources/remote/building_api.dart';
import 'package:propedia/data/dto/building_dto.dart';
import 'package:propedia/data/repositories/building_repository.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';

// BuildingApi Provider
final buildingApiProvider = Provider<BuildingApi>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return BuildingApi(apiClient.dio);
});

// BuildingRepository Provider
final buildingRepositoryProvider = Provider<BuildingRepository>((ref) {
  final buildingApi = ref.watch(buildingApiProvider);
  return BuildingRepository(buildingApi: buildingApi);
});

// 도로명 검색 상태
enum SearchStatus {
  initial,
  loading,
  success,
  error,
}

// 도로명 검색 결과 상태
class RoadSearchState {
  final SearchStatus status;
  final List<RoadSearchResultItem> results;
  final String? errorMessage;

  const RoadSearchState({
    this.status = SearchStatus.initial,
    this.results = const [],
    this.errorMessage,
  });

  RoadSearchState copyWith({
    SearchStatus? status,
    List<RoadSearchResultItem>? results,
    String? errorMessage,
  }) {
    return RoadSearchState(
      status: status ?? this.status,
      results: results ?? this.results,
      errorMessage: errorMessage,
    );
  }
}

// 도로명 검색 Notifier
class RoadSearchNotifier extends StateNotifier<RoadSearchState> {
  final BuildingRepository _repository;

  RoadSearchNotifier(this._repository) : super(const RoadSearchState());

  Future<void> search(String roadName) async {
    if (roadName.trim().isEmpty) {
      state = const RoadSearchState(status: SearchStatus.initial);
      return;
    }

    state = state.copyWith(status: SearchStatus.loading);
    debugPrint('🔍 도로명 검색 시작: $roadName');

    try {
      final response = await _repository.searchByRoad(roadName);
      debugPrint('✅ 도로명 검색 응답: success=${response.success}, count=${response.results.length}');
      if (response.success) {
        state = RoadSearchState(
          status: SearchStatus.success,
          results: response.results,
        );
      } else {
        state = RoadSearchState(
          status: SearchStatus.error,
          errorMessage: response.error ?? '검색 결과가 없습니다',
        );
      }
    } catch (e) {
      debugPrint('❌ 도로명 검색 에러: $e');
      state = RoadSearchState(
        status: SearchStatus.error,
        errorMessage: e.toString().replaceFirst('Exception: ', ''),
      );
    }
  }

  void reset() {
    state = const RoadSearchState();
  }
}

final roadSearchProvider =
    StateNotifierProvider<RoadSearchNotifier, RoadSearchState>((ref) {
  final repository = ref.watch(buildingRepositoryProvider);
  return RoadSearchNotifier(repository);
});

// 건축물 검색 결과 상태 (지번/건물관리번호)
class BuildingSearchState {
  final SearchStatus status;
  final BuildingSearchResponse? result;
  final String? errorMessage;
  final String searchType; // 'road', 'jibun', 'map'

  const BuildingSearchState({
    this.status = SearchStatus.initial,
    this.result,
    this.errorMessage,
    this.searchType = 'jibun',
  });

  BuildingSearchState copyWith({
    SearchStatus? status,
    BuildingSearchResponse? result,
    String? errorMessage,
    String? searchType,
  }) {
    return BuildingSearchState(
      status: status ?? this.status,
      result: result ?? this.result,
      errorMessage: errorMessage,
      searchType: searchType ?? this.searchType,
    );
  }
}

// 건축물 검색 Notifier
class BuildingSearchNotifier extends StateNotifier<BuildingSearchState> {
  final BuildingRepository _repository;

  BuildingSearchNotifier(this._repository) : super(const BuildingSearchState());

  /// 지번으로 검색
  Future<void> searchByJibun({
    required String bjdongCode,
    required String bun,
    String ji = '0000',
    String landType = '1',
    String searchType = 'jibun', // 'jibun' or 'map'
  }) async {
    state = state.copyWith(status: SearchStatus.loading, searchType: searchType);

    try {
      final response = await _repository.searchByJibun(
        bjdongCode: bjdongCode,
        bun: bun,
        ji: ji,
        landType: landType,
      );
      if (response.success) {
        state = BuildingSearchState(
          status: SearchStatus.success,
          result: response,
          searchType: searchType,
        );
      } else {
        state = BuildingSearchState(
          status: SearchStatus.error,
          errorMessage: response.error ?? '검색 결과가 없습니다',
          searchType: searchType,
        );
      }
    } catch (e) {
      state = BuildingSearchState(
        status: SearchStatus.error,
        errorMessage: e.toString().replaceFirst('Exception: ', ''),
        searchType: searchType,
      );
    }
  }

  /// 건물관리번호로 검색 (도로명 검색 결과에서 선택 시 사용)
  Future<void> searchByBdMgtSn(
    String bdMgtSn, {
    String? lnbrMnnm,
    String? lnbrSlno,
    String? admCd,
    String searchType = 'road',
  }) async {
    state = state.copyWith(status: SearchStatus.loading, searchType: searchType);

    try {
      final response = await _repository.searchByBdMgtSn(
        bdMgtSn,
        lnbrMnnm: lnbrMnnm,
        lnbrSlno: lnbrSlno,
        admCd: admCd,
      );
      if (response.success) {
        state = BuildingSearchState(
          status: SearchStatus.success,
          result: response,
          searchType: searchType,
        );
      } else {
        state = BuildingSearchState(
          status: SearchStatus.error,
          errorMessage: response.error ?? '검색 결과가 없습니다',
          searchType: searchType,
        );
      }
    } catch (e) {
      state = BuildingSearchState(
        status: SearchStatus.error,
        errorMessage: e.toString().replaceFirst('Exception: ', ''),
        searchType: searchType,
      );
    }
  }

  /// 검색 결과 직접 설정 (병렬 검색 결과 사용 시)
  void setSearchResult(BuildingSearchResponse response, {String searchType = 'jibun'}) {
    if (response.success) {
      state = BuildingSearchState(
        status: SearchStatus.success,
        result: response,
        searchType: searchType,
      );
    } else {
      state = BuildingSearchState(
        status: SearchStatus.error,
        errorMessage: response.error ?? '검색 결과가 없습니다',
        searchType: searchType,
      );
    }
  }

  void reset() {
    state = const BuildingSearchState();
  }
}

final buildingSearchProvider =
    StateNotifierProvider<BuildingSearchNotifier, BuildingSearchState>((ref) {
  final repository = ref.watch(buildingRepositoryProvider);
  return BuildingSearchNotifier(repository);
});

// 법정동 검색 Provider (자동완성)
final bjdongSearchProvider = FutureProvider.family<List<BjdongSearchItem>, String>(
  (ref, query) async {
    if (query.trim().isEmpty) {
      return [];
    }
    final repository = ref.watch(buildingRepositoryProvider);
    return repository.searchBjdong(query);
  },
);

// 동/호 상세 정보 상태
class AreaInfoState {
  final SearchStatus status;
  final AreaInfo? areaInfo;
  final String? selectedDong;
  final String? selectedHo;
  final String? errorMessage;

  const AreaInfoState({
    this.status = SearchStatus.initial,
    this.areaInfo,
    this.selectedDong,
    this.selectedHo,
    this.errorMessage,
  });

  AreaInfoState copyWith({
    SearchStatus? status,
    AreaInfo? areaInfo,
    String? selectedDong,
    String? selectedHo,
    String? errorMessage,
  }) {
    return AreaInfoState(
      status: status ?? this.status,
      areaInfo: areaInfo ?? this.areaInfo,
      selectedDong: selectedDong ?? this.selectedDong,
      selectedHo: selectedHo ?? this.selectedHo,
      errorMessage: errorMessage,
    );
  }
}

// 동/호 상세 정보 Notifier
class AreaInfoNotifier extends StateNotifier<AreaInfoState> {
  final BuildingRepository _repository;

  AreaInfoNotifier(this._repository) : super(const AreaInfoState());

  void selectDong(String? dong) {
    state = AreaInfoState(
      selectedDong: dong,
      selectedHo: null,
    );
  }

  void selectHo(String? ho) {
    state = state.copyWith(selectedHo: ho);
  }

  Future<void> fetchAreaInfo({
    required String bjdongCode,
    required String bun,
    String ji = '0000',
    required String dongNm,
    required String hoNm,
  }) async {
    state = state.copyWith(status: SearchStatus.loading);
    debugPrint('🔍 동/호 상세 정보 조회: $dongNm $hoNm');

    try {
      final areaInfo = await _repository.getAreaInfo(
        bjdongCode: bjdongCode,
        bun: bun,
        ji: ji,
        dongNm: dongNm,
        hoNm: hoNm,
      );

      if (areaInfo != null) {
        debugPrint('✅ 동/호 상세 정보 조회 성공');
        state = state.copyWith(
          status: SearchStatus.success,
          areaInfo: areaInfo,
        );
      } else {
        state = state.copyWith(
          status: SearchStatus.error,
          errorMessage: '상세 정보가 없습니다',
        );
      }
    } catch (e) {
      debugPrint('❌ 동/호 상세 정보 조회 에러: $e');
      state = state.copyWith(
        status: SearchStatus.error,
        errorMessage: e.toString().replaceFirst('Exception: ', ''),
      );
    }
  }

  void reset() {
    state = const AreaInfoState();
  }
}

final areaInfoProvider =
    StateNotifierProvider<AreaInfoNotifier, AreaInfoState>((ref) {
  final repository = ref.watch(buildingRepositoryProvider);
  return AreaInfoNotifier(repository);
});

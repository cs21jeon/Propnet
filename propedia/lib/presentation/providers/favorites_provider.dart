import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:propedia/data/models/favorite.dart';
import 'package:propedia/data/repositories/favorites_repository.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';

// Repository Provider
final favoritesRepositoryProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return FavoritesRepository(apiClient.dio);
});

// 즐겨찾기 상태
class FavoritesState {
  final List<Favorite> localFavorites;
  final List<Map<String, dynamic>> serverFavorites;
  final bool isLoading;
  final String? error;

  const FavoritesState({
    this.localFavorites = const [],
    this.serverFavorites = const [],
    this.isLoading = false,
    this.error,
  });

  FavoritesState copyWith({
    List<Favorite>? localFavorites,
    List<Map<String, dynamic>>? serverFavorites,
    bool? isLoading,
    String? error,
  }) {
    return FavoritesState(
      localFavorites: localFavorites ?? this.localFavorites,
      serverFavorites: serverFavorites ?? this.serverFavorites,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

// 즐겨찾기 Provider
class FavoritesNotifier extends StateNotifier<FavoritesState> {
  final FavoritesRepository _repository;
  final Ref _ref;

  FavoritesNotifier(this._repository, this._ref) : super(const FavoritesState());

  /// 게스트 모드 여부 확인
  bool get _isGuestMode {
    final authState = _ref.read(authProvider);
    return authState.status == AuthStatus.guest;
  }

  /// 즐겨찾기 추가
  Future<bool> addFavorite({
    required String displayAddress,
    String? roadAddress,
    String? jibunAddress,
    String? buildingName,
    String? pnu,
    String? bdMgtSn,
    String? dongName,
    String? hoName,
    String? buildingType,
    String? memo,
  }) async {
    final result = await _repository.addFavorite(
      displayAddress: displayAddress,
      roadAddress: roadAddress,
      jibunAddress: jibunAddress,
      buildingName: buildingName,
      pnu: pnu,
      bdMgtSn: bdMgtSn,
      dongName: dongName,
      hoName: hoName,
      buildingType: buildingType,
      memo: memo,
      skipServerSync: _isGuestMode,
    );

    if (result) {
      loadLocalFavorites();
    }

    return result;
  }

  /// 로컬 즐겨찾기 로드
  void loadLocalFavorites() {
    final favorites = _repository.getFavorites();
    state = state.copyWith(localFavorites: favorites);
  }

  /// 서버 즐겨찾기 로드
  Future<void> loadServerFavorites() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final favorites = await _repository.getServerFavorites();
      state = state.copyWith(
        serverFavorites: favorites,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// 즐겨찾기 삭제 (로컬 + 서버)
  Future<void> deleteFavorite(String id) async {
    // 서버 ID 추출 (server_123 형태인 경우)
    if (id.startsWith('server_')) {
      final serverIdStr = id.replaceFirst('server_', '');
      final serverId = int.tryParse(serverIdStr);
      if (serverId != null) {
        try {
          await _repository.deleteServerFavorite(serverId);
        } catch (e) {
          // 서버 삭제 실패 무시
        }
      }
    }
    await _repository.deleteFavorite(id);
    loadLocalFavorites();
  }

  /// 즐겨찾기 삭제 (서버)
  Future<void> deleteServerFavorite(int id) async {
    try {
      await _repository.deleteServerFavorite(id);
      await loadServerFavorites();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  /// 즐겨찾기 전체 삭제
  Future<void> clearFavorites() async {
    await _repository.clearFavorites();
    state = state.copyWith(localFavorites: []);
  }

  /// 즐겨찾기 여부 확인
  bool isFavorite(String displayAddress, {String? dongName, String? hoName}) {
    return _repository.isFavorite(displayAddress, dongName: dongName, hoName: hoName);
  }

  /// 즐겨찾기 ID 찾기
  String? findFavoriteId(String displayAddress, {String? dongName, String? hoName}) {
    return _repository.findFavoriteId(displayAddress, dongName: dongName, hoName: hoName);
  }

  /// 즐겨찾기 토글
  Future<bool> toggleFavorite({
    required String displayAddress,
    String? roadAddress,
    String? jibunAddress,
    String? buildingName,
    String? pnu,
    String? bdMgtSn,
    String? dongName,
    String? hoName,
    String? buildingType,
  }) async {
    final isFav = isFavorite(displayAddress, dongName: dongName, hoName: hoName);

    if (isFav) {
      final id = findFavoriteId(displayAddress, dongName: dongName, hoName: hoName);
      if (id != null) {
        await deleteFavorite(id);
      }
      return false;
    } else {
      await addFavorite(
        displayAddress: displayAddress,
        roadAddress: roadAddress,
        jibunAddress: jibunAddress,
        buildingName: buildingName,
        pnu: pnu,
        bdMgtSn: bdMgtSn,
        dongName: dongName,
        hoName: hoName,
        buildingType: buildingType,
      );
      return true;
    }
  }

  /// 메모 수정
  Future<void> updateMemo(String id, String? memo) async {
    await _repository.updateMemo(id, memo);
    loadLocalFavorites();
  }

  /// 서버에서 즐겨찾기 동기화
  Future<int> syncFromServer() async {
    state = state.copyWith(isLoading: true);
    try {
      final syncedCount = await _repository.syncFromServer();
      loadLocalFavorites();
      return syncedCount;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return 0;
    } finally {
      state = state.copyWith(isLoading: false);
    }
  }

  /// 상태 초기화 (로그아웃 시 호출) - 로컬 DB도 함께 삭제
  Future<void> reset() async {
    await _repository.clearFavorites();
    state = const FavoritesState();
  }
}

final favoritesProvider = StateNotifierProvider<FavoritesNotifier, FavoritesState>((ref) {
  final repository = ref.watch(favoritesRepositoryProvider);
  return FavoritesNotifier(repository, ref);
});

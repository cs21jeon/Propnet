import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:propedia/data/models/search_history.dart';
import 'package:propedia/data/repositories/history_repository.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';

// Repository Provider
final historyRepositoryProvider = Provider((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return HistoryRepository(apiClient.dio);
});

// 검색 기록 상태
class HistoryState {
  final List<SearchHistory> localHistory;
  final Map<String, List<Map<String, dynamic>>> serverHistory;
  final bool isLoading;
  final String? error;

  const HistoryState({
    this.localHistory = const [],
    this.serverHistory = const {},
    this.isLoading = false,
    this.error,
  });

  HistoryState copyWith({
    List<SearchHistory>? localHistory,
    Map<String, List<Map<String, dynamic>>>? serverHistory,
    bool? isLoading,
    String? error,
  }) {
    return HistoryState(
      localHistory: localHistory ?? this.localHistory,
      serverHistory: serverHistory ?? this.serverHistory,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

// 검색 기록 Provider
class HistoryNotifier extends StateNotifier<HistoryState> {
  final HistoryRepository _repository;
  final Ref _ref;

  HistoryNotifier(this._repository, this._ref) : super(const HistoryState());

  /// 게스트 모드 여부 확인
  bool get _isGuestMode {
    final authState = _ref.read(authProvider);
    return authState.status == AuthStatus.guest;
  }

  /// 검색 기록 추가
  Future<void> addHistory({
    required String searchType,
    required String displayAddress,
    String? roadAddress,
    String? jibunAddress,
    String? buildingName,
    String? pnu,
    String? bdMgtSn,
    String? dongName,
    String? hoName,
    String? buildingType,
    double? latitude,
    double? longitude,
  }) async {
    try {
      await _repository.addHistory(
        searchType: searchType,
        displayAddress: displayAddress,
        roadAddress: roadAddress,
        jibunAddress: jibunAddress,
        buildingName: buildingName,
        pnu: pnu,
        bdMgtSn: bdMgtSn,
        dongName: dongName,
        hoName: hoName,
        buildingType: buildingType,
        latitude: latitude,
        longitude: longitude,
        skipServerSync: _isGuestMode,
      );

      // 목록 갱신
      loadLocalHistory();
    } catch (e) {
      debugPrint('검색 기록 저장 에러: $e');
    }
  }

  /// 로컬 검색 기록 로드
  void loadLocalHistory() {
    final history = _repository.getHistory();
    state = state.copyWith(localHistory: history);
  }

  /// 서버 검색 기록 로드
  Future<void> loadServerHistory() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final history = await _repository.getServerHistory();
      state = state.copyWith(
        serverHistory: history,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// 검색 기록 삭제 (로컬 + 서버)
  Future<void> deleteHistory(String id) async {
    // 삭제할 기록의 PNU 찾기
    final historyToDelete = state.localHistory.where((h) => h.id == id).firstOrNull;
    final pnuToDelete = historyToDelete?.pnu;

    // 서버 ID 추출 (server_123 형태인 경우)
    if (id.startsWith('server_')) {
      final serverIdStr = id.replaceFirst('server_', '');
      final serverId = int.tryParse(serverIdStr);
      if (serverId != null) {
        try {
          await _repository.deleteServerHistory(serverId);
        } catch (e) {
          debugPrint('서버 삭제 실패: $e');
        }
      }
    }

    // 같은 PNU를 가진 서버 기록 모두 삭제
    if (pnuToDelete != null && pnuToDelete.isNotEmpty) {
      try {
        final serverHistory = await _repository.getServerHistory();
        for (final dateGroup in serverHistory.values) {
          for (final item in dateGroup) {
            if (item['pnu'] == pnuToDelete) {
              final serverId = item['id'] as int?;
              if (serverId != null) {
                try {
                  await _repository.deleteServerHistory(serverId);
                } catch (_) {}
              }
            }
          }
        }
      } catch (e) {
        debugPrint('서버 중복 삭제 실패: $e');
      }
    }

    await _repository.deleteHistory(id);
    loadLocalHistory();
  }

  /// 검색 기록 삭제 (서버)
  Future<void> deleteServerHistory(int id) async {
    try {
      await _repository.deleteServerHistory(id);
      await loadServerHistory();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  /// 검색 기록 전체 삭제
  Future<void> clearHistory() async {
    await _repository.clearHistory();
    state = state.copyWith(localHistory: []);
  }

  /// 서버에서 검색 기록 동기화
  Future<int> syncFromServer() async {
    state = state.copyWith(isLoading: true);
    try {
      final syncedCount = await _repository.syncFromServer();
      loadLocalHistory();
      return syncedCount;
    } catch (e) {
      debugPrint('서버 동기화 에러: $e');
      return 0;
    } finally {
      state = state.copyWith(isLoading: false);
    }
  }

  /// 상태 초기화 (로그아웃 시 호출) - 로컬 DB도 함께 삭제
  Future<void> reset() async {
    await _repository.clearHistory();
    state = const HistoryState();
  }
}

final historyProvider = StateNotifierProvider<HistoryNotifier, HistoryState>((ref) {
  final repository = ref.watch(historyRepositoryProvider);
  return HistoryNotifier(repository, ref);
});

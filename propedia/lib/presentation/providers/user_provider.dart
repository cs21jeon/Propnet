import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:propedia/data/datasources/remote/user_api.dart';
import 'package:propedia/data/dto/user_stats_dto.dart';
import 'package:propedia/data/repositories/user_repository.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';

/// UserApi Provider
final userApiProvider = Provider<UserApi>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return UserApi(apiClient.dio);
});

/// UserRepository Provider
final userRepositoryProvider = Provider<UserRepository>((ref) {
  final userApi = ref.watch(userApiProvider);
  return UserRepository(userApi: userApi);
});

/// 사용 통계 상태
class UsageStatsState {
  final bool isLoading;
  final UsageStats? stats;
  final String? error;

  const UsageStatsState({
    this.isLoading = false,
    this.stats,
    this.error,
  });

  UsageStatsState copyWith({
    bool? isLoading,
    UsageStats? stats,
    String? error,
  }) {
    return UsageStatsState(
      isLoading: isLoading ?? this.isLoading,
      stats: stats ?? this.stats,
      error: error,
    );
  }
}

/// 사용 통계 StateNotifier
class UsageStatsNotifier extends StateNotifier<UsageStatsState> {
  final UserRepository _repository;

  UsageStatsNotifier(this._repository) : super(const UsageStatsState());

  /// 사용 통계 로드
  Future<void> loadStats() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final stats = await _repository.getUsageStats();

      if (stats != null) {
        state = UsageStatsState(isLoading: false, stats: stats);
      } else {
        state = const UsageStatsState(
          isLoading: false,
          error: '사용 통계를 불러올 수 없습니다',
        );
      }
    } catch (e) {
      state = UsageStatsState(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// 상태 초기화
  void reset() {
    state = const UsageStatsState();
  }
}

/// UsageStats Provider
final usageStatsProvider =
    StateNotifierProvider<UsageStatsNotifier, UsageStatsState>((ref) {
  final repository = ref.watch(userRepositoryProvider);
  return UsageStatsNotifier(repository);
});

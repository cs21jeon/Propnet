import 'package:propedia/data/datasources/remote/user_api.dart';
import 'package:propedia/data/dto/user_stats_dto.dart';

class UserRepository {
  final UserApi _userApi;

  UserRepository({required UserApi userApi}) : _userApi = userApi;

  /// 사용 통계 조회
  Future<UsageStats?> getUsageStats() async {
    try {
      final response = await _userApi.getUsageStats();

      if (response.success && response.data != null) {
        return response.data;
      }

      return null;
    } catch (e) {
      // 에러 발생 시 null 반환
      return null;
    }
  }
}

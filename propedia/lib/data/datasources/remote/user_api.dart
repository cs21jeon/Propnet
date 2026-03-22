import 'package:dio/dio.dart';
import 'package:propedia/data/dto/user_stats_dto.dart';

class UserApi {
  final Dio _dio;

  UserApi(this._dio);

  /// 사용 통계 조회
  Future<UsageStatsResponse> getUsageStats() async {
    try {
      final response = await _dio.get('/app/api/user/usage-stats');
      return UsageStatsResponse.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.data != null) {
        return UsageStatsResponse.fromJson(e.response!.data);
      }
      rethrow;
    }
  }
}

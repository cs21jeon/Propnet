import 'package:dio/dio.dart';

class HistoryApi {
  final Dio _dio;

  HistoryApi(this._dio);

  /// 검색 기록 조회 (서버)
  Future<Map<String, dynamic>> getSearchHistory({int limit = 100}) async {
    try {
      final response = await _dio.get(
        '/app/api/user/history',
        queryParameters: {'limit': limit},
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['message'] ?? '검색 기록 조회 실패');
    }
  }

  /// 검색 기록 저장 (서버)
  Future<Map<String, dynamic>> saveSearchHistory(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post(
        '/app/api/user/history',
        data: data,
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['message'] ?? '검색 기록 저장 실패');
    }
  }

  /// 검색 기록 삭제 (서버)
  Future<void> deleteSearchHistory(int id) async {
    try {
      await _dio.delete('/app/api/user/history/$id');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['message'] ?? '검색 기록 삭제 실패');
    }
  }
}

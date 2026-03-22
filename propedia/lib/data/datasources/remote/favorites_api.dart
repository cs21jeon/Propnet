import 'package:dio/dio.dart';

class FavoritesApi {
  final Dio _dio;

  FavoritesApi(this._dio);

  /// 즐겨찾기 목록 조회 (서버)
  Future<Map<String, dynamic>> getFavorites({int page = 1, int limit = 50}) async {
    try {
      final response = await _dio.get(
        '/app/api/user/favorites',
        queryParameters: {'page': page, 'limit': limit},
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['message'] ?? '즐겨찾기 조회 실패');
    }
  }

  /// 즐겨찾기 추가 (서버)
  Future<Map<String, dynamic>> addFavorite(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post(
        '/app/api/user/favorites',
        data: data,
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['message'] ?? '즐겨찾기 추가 실패');
    }
  }

  /// 즐겨찾기 삭제 (서버)
  Future<void> deleteFavorite(int id) async {
    try {
      await _dio.delete('/app/api/user/favorites/$id');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['message'] ?? '즐겨찾기 삭제 실패');
    }
  }

  /// 즐겨찾기 메모 수정 (서버)
  Future<Map<String, dynamic>> updateFavoriteMemo(int id, String? memo) async {
    try {
      final response = await _dio.patch(
        '/app/api/user/favorites/$id',
        data: {'memo': memo},
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['message'] ?? '메모 수정 실패');
    }
  }
}

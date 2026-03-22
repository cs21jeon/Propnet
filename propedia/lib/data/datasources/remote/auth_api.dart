import 'package:dio/dio.dart';
import 'package:propedia/data/dto/auth_dto.dart';

class AuthApi {
  final Dio _dio;

  AuthApi(this._dio);

  /// Google 로그인
  Future<AuthResponse> loginWithGoogle(GoogleLoginRequest request) async {
    try {
      final response = await _dio.post(
        '/app/api/auth/google',
        data: request.toJson(),
      );
      return AuthResponse.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.data != null && e.response!.data is Map<String, dynamic>) {
        return AuthResponse.fromJson(e.response!.data);
      }
      throw Exception('서버 연결에 실패했습니다 (${e.response?.statusCode ?? 'network error'})');
    }
  }

  /// 내 정보 조회
  Future<UserResponse> getMe() async {
    try {
      final response = await _dio.get('/app/api/auth/me');
      return UserResponse.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.data != null && e.response!.data is Map<String, dynamic>) {
        return UserResponse.fromJson(e.response!.data);
      }
      throw Exception('서버 연결에 실패했습니다 (${e.response?.statusCode ?? 'network error'})');
    }
  }

  /// 로그아웃
  Future<ApiResponse> logout() async {
    try {
      final response = await _dio.post('/app/api/auth/logout');
      return ApiResponse.fromJson(response.data);
    } on DioException catch (_) {
      return const ApiResponse(success: true, message: '로그아웃');
    }
  }
}

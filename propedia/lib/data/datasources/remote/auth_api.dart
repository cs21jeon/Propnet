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

  /// Google 로그인 (raw JSON 반환 - 동의 필드 포함)
  Future<Map<String, dynamic>> loginWithGoogleRaw(GoogleLoginRequest request) async {
    try {
      final response = await _dio.post(
        '/app/api/auth/google',
        data: request.toJson(),
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      if (e.response?.data != null && e.response!.data is Map<String, dynamic>) {
        return e.response!.data as Map<String, dynamic>;
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

  /// 동의 기록
  Future<Map<String, dynamic>> recordConsent(List<Map<String, dynamic>> consents) async {
    try {
      final response = await _dio.post(
        '/app/api/auth/consent',
        data: {'consents': consents},
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      if (e.response?.data != null && e.response!.data is Map<String, dynamic>) {
        return e.response!.data as Map<String, dynamic>;
      }
      throw Exception('동의 저장에 실패했습니다 (${e.response?.statusCode ?? 'network error'})');
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

  /// 유저 타입 선택
  Future<Map<String, dynamic>> selectUserType(String userType) async {
    try {
      final response = await _dio.post(
        '/app/api/auth/select-user-type',
        data: {'user_type': userType},
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      if (e.response?.data != null && e.response!.data is Map<String, dynamic>) {
        return e.response!.data as Map<String, dynamic>;
      }
      throw Exception('유저 타입 설정에 실패했습니다 (${e.response?.statusCode ?? 'network error'})');
    }
  }

  /// Agent slug 중복 확인
  Future<Map<String, dynamic>> checkSlug(String slug) async {
    try {
      final response = await _dio.get(
        '/app/api/auth/check-slug',
        queryParameters: {'slug': slug},
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      if (e.response?.data != null && e.response!.data is Map<String, dynamic>) {
        return e.response!.data as Map<String, dynamic>;
      }
      throw Exception('slug 확인에 실패했습니다');
    }
  }

  /// Agent 가입 신청 (multipart/form-data)
  Future<Map<String, dynamic>> submitAgentRequest({
    required String agentName,
    required String agentSlug,
    required String representativeName,
    required String phone,
    required String officeAddress,
    required String licenseFilePath,
    String? businessRegFilePath,
  }) async {
    try {
      final formData = FormData.fromMap({
        'agent_name': agentName,
        'agent_slug': agentSlug,
        'representative_name': representativeName,
        'phone': phone,
        'office_address': officeAddress,
        'license_file': await MultipartFile.fromFile(licenseFilePath),
        if (businessRegFilePath != null)
          'business_reg_file': await MultipartFile.fromFile(businessRegFilePath),
      });

      final response = await _dio.post(
        '/app/api/auth/agent/request',
        data: formData,
        options: Options(contentType: 'multipart/form-data'),
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      if (e.response?.data != null && e.response!.data is Map<String, dynamic>) {
        return e.response!.data as Map<String, dynamic>;
      }
      throw Exception('Agent 가입 신청에 실패했습니다 (${e.response?.statusCode ?? 'network error'})');
    }
  }

  /// Agent 가입 신청 상태 조회
  Future<Map<String, dynamic>> getAgentRequestStatus() async {
    try {
      final response = await _dio.get('/app/api/auth/agent/request/status');
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      if (e.response?.data != null && e.response!.data is Map<String, dynamic>) {
        return e.response!.data as Map<String, dynamic>;
      }
      throw Exception('신청 상태 조회에 실패했습니다');
    }
  }
}

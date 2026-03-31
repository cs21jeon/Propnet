import 'package:flutter/foundation.dart';
import 'package:propedia/core/storage/token_storage.dart';
import 'package:propedia/data/datasources/remote/auth_api.dart';
import 'package:propedia/data/dto/auth_dto.dart';
import 'package:propedia/domain/entities/user.dart';

/// 로그인 결과 (동의 필요 여부 + 신규 유저 여부 포함)
class LoginResult {
  final User? user;
  final bool consentRequired;
  final List<Map<String, dynamic>> missingConsents;
  final bool isNewUser;

  const LoginResult({
    this.user,
    this.consentRequired = false,
    this.missingConsents = const [],
    this.isNewUser = false,
  });
}

class AuthRepository {
  final AuthApi _authApi;
  final TokenStorage _tokenStorage;

  AuthRepository({
    required AuthApi authApi,
    required TokenStorage tokenStorage,
  })  : _authApi = authApi,
        _tokenStorage = tokenStorage;

  /// Google 로그인 (동의 필요 여부 포함)
  Future<LoginResult> loginWithGoogle({required String idToken}) async {
    // raw JSON으로 받아서 consent 필드 직접 파싱
    final rawData = await _authApi.loginWithGoogleRaw(
      GoogleLoginRequest(idToken: idToken),
    );

    final success = rawData['success'] as bool? ?? false;
    if (!success) {
      throw Exception(rawData['message'] as String? ?? 'Google 로그인에 실패했습니다');
    }

    // 토큰 저장
    final accessToken = rawData['access_token'] as String?;
    final refreshToken = rawData['refresh_token'] as String?;
    if (accessToken != null) {
      await _tokenStorage.saveAccessToken(accessToken);
    }
    if (refreshToken != null) {
      await _tokenStorage.saveRefreshToken(refreshToken);
    }

    // User 파싱
    User? user;
    if (rawData['user'] != null) {
      user = User.fromJson(rawData['user'] as Map<String, dynamic>);
    }

    // 동의 필요 여부 확인
    final consentRequired = rawData['consent_required'] as bool? ?? false;
    final missingConsentsRaw = rawData['missing_consents'] as List<dynamic>?;
    final missingConsents = missingConsentsRaw
        ?.map((e) => Map<String, dynamic>.from(e as Map))
        .toList() ?? [];

    // 신규 유저 여부
    final isNewUser = rawData['is_new_user'] as bool? ?? false;

    debugPrint('[AuthRepo] consent_required=$consentRequired, missing=${missingConsents.length}, is_new_user=$isNewUser');

    if (!consentRequired && user == null) {
      throw Exception('Google 로그인에 실패했습니다');
    }

    return LoginResult(
      user: user,
      consentRequired: consentRequired,
      missingConsents: missingConsents,
      isNewUser: isNewUser,
    );
  }

  /// 동의 기록
  Future<void> recordConsent(List<Map<String, dynamic>> consents) async {
    final result = await _authApi.recordConsent(consents);
    if (result['success'] != true) {
      throw Exception(result['message'] ?? '동의 저장에 실패했습니다');
    }
  }

  /// 내 정보 조회
  Future<User?> getMe() async {
    try {
      final response = await _authApi.getMe();
      if (response.success && response.user != null) {
        return response.user;
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// 로그아웃
  Future<void> logout() async {
    try {
      await _authApi.logout();
    } catch (e) {
      // 서버 로그아웃 실패해도 로컬 토큰 삭제
    }
    await _tokenStorage.deleteTokens();
  }

  /// 자동 로그인 체크
  Future<User?> checkAutoLogin() async {
    final hasToken = await _tokenStorage.hasToken();
    if (!hasToken) return null;
    return await getMe();
  }

  /// 토큰 존재 여부
  Future<bool> hasToken() async {
    return await _tokenStorage.hasToken();
  }

  /// 유저 타입 선택 (일반 사용자)
  Future<void> selectUserType(String userType) async {
    final result = await _authApi.selectUserType(userType);
    if (result['success'] != true) {
      throw Exception(result['message'] ?? '유저 타입 설정에 실패했습니다');
    }
  }

  /// Agent slug 중복 확인
  Future<Map<String, dynamic>> checkSlug(String slug) async {
    return await _authApi.checkSlug(slug);
  }

  /// Agent 가입 신청
  Future<Map<String, dynamic>> submitAgentRequest({
    required String agentName,
    required String agentSlug,
    required String representativeName,
    required String phone,
    required String officeAddress,
    required String licenseFilePath,
    String? businessRegFilePath,
  }) async {
    return await _authApi.submitAgentRequest(
      agentName: agentName,
      agentSlug: agentSlug,
      representativeName: representativeName,
      phone: phone,
      officeAddress: officeAddress,
      licenseFilePath: licenseFilePath,
      businessRegFilePath: businessRegFilePath,
    );
  }

  /// Agent 가입 신청 상태 조회
  Future<Map<String, dynamic>> getAgentRequestStatus() async {
    return await _authApi.getAgentRequestStatus();
  }
}

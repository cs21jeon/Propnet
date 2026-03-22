import 'package:propedia/core/storage/token_storage.dart';
import 'package:propedia/data/datasources/remote/auth_api.dart';
import 'package:propedia/data/dto/auth_dto.dart';
import 'package:propedia/domain/entities/user.dart';

class AuthRepository {
  final AuthApi _authApi;
  final TokenStorage _tokenStorage;

  AuthRepository({
    required AuthApi authApi,
    required TokenStorage tokenStorage,
  })  : _authApi = authApi,
        _tokenStorage = tokenStorage;

  /// Google 로그인
  Future<User> loginWithGoogle({required String idToken}) async {
    final response = await _authApi.loginWithGoogle(
      GoogleLoginRequest(idToken: idToken),
    );

    if (!response.success || response.accessToken == null || response.user == null) {
      throw Exception(response.message ?? 'Google 로그인에 실패했습니다');
    }

    // 토큰 저장
    await _tokenStorage.saveAccessToken(response.accessToken!);
    if (response.refreshToken != null) {
      await _tokenStorage.saveRefreshToken(response.refreshToken!);
    }

    return response.user!;
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
}

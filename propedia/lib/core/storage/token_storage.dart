import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class TokenStorage {
  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';

  final FlutterSecureStorage? _secureStorage;

  TokenStorage()
      : _secureStorage = kIsWeb
            ? null
            : const FlutterSecureStorage(
                aOptions: AndroidOptions(encryptedSharedPreferences: true),
                iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
              );

  /// Access Token 저장
  Future<void> saveAccessToken(String token) async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_accessTokenKey, token);
    } else {
      await _secureStorage!.write(key: _accessTokenKey, value: token);
    }
  }

  /// Refresh Token 저장
  Future<void> saveRefreshToken(String token) async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_refreshTokenKey, token);
    } else {
      await _secureStorage!.write(key: _refreshTokenKey, value: token);
    }
  }

  /// 토큰 모두 저장
  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await Future.wait([
      saveAccessToken(accessToken),
      saveRefreshToken(refreshToken),
    ]);
  }

  /// Access Token 가져오기
  Future<String?> getAccessToken() async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(_accessTokenKey);
    } else {
      return await _secureStorage!.read(key: _accessTokenKey);
    }
  }

  /// Refresh Token 가져오기
  Future<String?> getRefreshToken() async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(_refreshTokenKey);
    } else {
      return await _secureStorage!.read(key: _refreshTokenKey);
    }
  }

  /// 토큰 삭제 (로그아웃)
  Future<void> deleteTokens() async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      await Future.wait([
        prefs.remove(_accessTokenKey),
        prefs.remove(_refreshTokenKey),
      ]);
    } else {
      await Future.wait([
        _secureStorage!.delete(key: _accessTokenKey),
        _secureStorage!.delete(key: _refreshTokenKey),
      ]);
    }
  }

  /// 토큰 존재 여부 확인
  Future<bool> hasToken() async {
    final token = await getAccessToken();
    return token != null && token.isNotEmpty;
  }
}

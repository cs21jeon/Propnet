import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:propedia/core/storage/token_storage.dart';

class AuthInterceptor extends Interceptor {
  final TokenStorage tokenStorage;
  final Dio _dio;
  bool _isRefreshing = false;

  AuthInterceptor({required this.tokenStorage, required Dio dio}) : _dio = dio;

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // 인증이 필요없는 경로
    final noAuthPaths = [
      '/app/api/auth/google',
      '/app/api/auth/refresh',
    ];

    if (!noAuthPaths.any((path) => options.path.contains(path))) {
      final token = await tokenStorage.getAccessToken();
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    }

    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401 && !_isRefreshing) {
      // refresh 요청 자체가 401이면 토큰 삭제
      if (err.requestOptions.path.contains('/auth/refresh')) {
        await tokenStorage.deleteTokens();
        handler.next(err);
        return;
      }

      // refresh token으로 access token 갱신 시도
      final refreshToken = await tokenStorage.getRefreshToken();
      if (refreshToken != null) {
        _isRefreshing = true;
        try {
          final response = await _dio.post(
            '/app/api/auth/refresh',
            data: {'refresh_token': refreshToken},
          );

          if (response.statusCode == 200 && response.data['success'] == true) {
            final newAccessToken = response.data['access_token'] as String;
            await tokenStorage.saveAccessToken(newAccessToken);

            // 원래 요청 재시도
            final opts = err.requestOptions;
            opts.headers['Authorization'] = 'Bearer $newAccessToken';
            final retryResponse = await _dio.fetch(opts);
            handler.resolve(retryResponse);
            return;
          }
        } catch (e) {
          debugPrint('[AUTH] Token refresh failed: $e');
        } finally {
          _isRefreshing = false;
        }
      }

      // refresh 실패 시 토큰 삭제
      await tokenStorage.deleteTokens();
    }

    handler.next(err);
  }
}

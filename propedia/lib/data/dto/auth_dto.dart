import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:propedia/domain/entities/user.dart';

part 'auth_dto.freezed.dart';
part 'auth_dto.g.dart';

/// Google 로그인 요청
@freezed
class GoogleLoginRequest with _$GoogleLoginRequest {
  const factory GoogleLoginRequest({
    @JsonKey(name: 'id_token') required String idToken,
  }) = _GoogleLoginRequest;

  factory GoogleLoginRequest.fromJson(Map<String, dynamic> json) =>
      _$GoogleLoginRequestFromJson(json);
}

/// 인증 응답 (로그인)
@freezed
class AuthResponse with _$AuthResponse {
  const factory AuthResponse({
    required bool success,
    String? message,
    @JsonKey(name: 'access_token') String? accessToken,
    @JsonKey(name: 'refresh_token') String? refreshToken,
    User? user,
  }) = _AuthResponse;

  factory AuthResponse.fromJson(Map<String, dynamic> json) =>
      _$AuthResponseFromJson(json);
}

/// 기본 API 응답
@freezed
class ApiResponse with _$ApiResponse {
  const factory ApiResponse({
    required bool success,
    String? message,
  }) = _ApiResponse;

  factory ApiResponse.fromJson(Map<String, dynamic> json) =>
      _$ApiResponseFromJson(json);
}

/// 사용자 정보 응답
@freezed
class UserResponse with _$UserResponse {
  const factory UserResponse({
    required bool success,
    String? message,
    User? user,
  }) = _UserResponse;

  factory UserResponse.fromJson(Map<String, dynamic> json) =>
      _$UserResponseFromJson(json);
}

import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as path;
import 'package:shared_preferences/shared_preferences.dart';

/// VoiceRoom API 클라이언트
class ApiService {
  // ============================================================
  // 설정 - 실제 환경에 맞게 수정
  // ============================================================
  static const String baseUrl = 'https://goldenrabbit.biz/voiceroom';

  String? _token;
  String? _refreshToken;
  final http.Client _client = http.Client();

  /// 토큰 리프레시 진행 중 여부 (중복 호출 방지)
  bool _isRefreshing = false;

  /// JWT 토큰 설정 (access token)
  void setToken(String token) => _token = token;
  String? get token => _token;
  bool get isLoggedIn => _token != null;

  /// Refresh 토큰 설정
  void setRefreshToken(String? token) => _refreshToken = token;
  String? get refreshToken => _refreshToken;

  /// 인증 헤더
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (_token != null) 'Authorization': 'Bearer $_token',
  };
  
  // ============================================================
  // 인증
  // ============================================================
  
  /// Google 로그인 (serverAuthCode 포함 시 Drive 연동)
  Future<Map<String, dynamic>> loginWithGoogle(String idToken, {String? serverAuthCode}) async {
    final body = {'id_token': idToken};
    if (serverAuthCode != null) {
      body['server_auth_code'] = serverAuthCode;
    }

    final response = await _client.post(
      Uri.parse('$baseUrl/api/auth/google'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );

    final data = _handleResponse(response);
    // 통합 인증: access_token 우선, 기존 token 호환
    _token = data['access_token'] ?? data['token'];
    _refreshToken = data['refresh_token'];
    return data;
  }

  /// Access token 갱신 (refresh token 사용)
  Future<bool> refreshAccessToken() async {
    if (_refreshToken == null || _isRefreshing) return false;

    _isRefreshing = true;
    try {
      final response = await _client.post(
        Uri.parse('$baseUrl/api/auth/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': _refreshToken}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _token = data['access_token'] ?? data['token'];
        if (data['refresh_token'] != null) {
          _refreshToken = data['refresh_token'];
        }

        // SharedPreferences에 새 토큰 저장
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('auth_token', _token!);
        if (_refreshToken != null) {
          await prefs.setString('refresh_token', _refreshToken!);
        }

        debugPrint('[ApiService] 토큰 갱신 성공');
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('[ApiService] 토큰 갱신 실패: $e');
      return false;
    } finally {
      _isRefreshing = false;
    }
  }
  
  /// 내 정보
  Future<Map<String, dynamic>> getMe() async {
    return _authenticatedGet('$baseUrl/api/auth/me');
  }
  
  /// 프로필 이름 변경
  Future<Map<String, dynamic>> updateProfile({required String name}) async {
    final response = await _client.patch(
      Uri.parse('$baseUrl/api/auth/profile'),
      headers: _headers,
      body: jsonEncode({'name': name}),
    );
    return _handleResponse(response);
  }

  // ============================================================
  // FCM 디바이스 토큰
  // ============================================================

  /// FCM 토큰 등록
  Future<void> registerDeviceToken(String fcmToken, String platform) async {
    await _client.post(
      Uri.parse('$baseUrl/api/devices/register'),
      headers: _headers,
      body: jsonEncode({'fcm_token': fcmToken, 'platform': platform}),
    );
  }

  /// FCM 토큰 해제
  Future<void> unregisterDeviceToken(String fcmToken) async {
    await _client.post(
      Uri.parse('$baseUrl/api/devices/unregister'),
      headers: _headers,
      body: jsonEncode({'fcm_token': fcmToken}),
    );
  }

  // ============================================================
  // 채팅방
  // ============================================================
  
  /// 채팅방 목록
  Future<List<dynamic>> getRooms() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/rooms'),
      headers: _headers,
    );
    final data = _handleResponse(response);
    return data['rooms'] ?? [];
  }
  
  /// 채팅방 생성
  Future<Map<String, dynamic>> createRoom(String name, {
    String? description,
    bool enableDriveBackup = true,
    bool enableSheetsLogging = true,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms'),
      headers: _headers,
      body: jsonEncode({
        'name': name,
        'description': description ?? '',
        'enable_drive_backup': enableDriveBackup,
        'enable_sheets_logging': enableSheetsLogging,
      }),
    );
    return _handleResponse(response);
  }

  /// 채팅방 설정 변경
  Future<Map<String, dynamic>> updateRoomSettings(int roomId, {
    bool? enableDriveBackup,
    bool? enableSheetsLogging,
  }) async {
    final body = <String, dynamic>{};
    if (enableDriveBackup != null) body['enable_drive_backup'] = enableDriveBackup;
    if (enableSheetsLogging != null) body['enable_sheets_logging'] = enableSheetsLogging;
    final response = await _client.patch(
      Uri.parse('$baseUrl/api/rooms/$roomId/settings'),
      headers: _headers,
      body: jsonEncode(body),
    );
    return _handleResponse(response);
  }
  
  /// 채팅방 참여 (초대코드)
  Future<Map<String, dynamic>> joinRoom(String inviteCode) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/join'),
      headers: _headers,
      body: jsonEncode({'invite_code': inviteCode}),
    );
    return _handleResponse(response);
  }
  
  /// 채팅방 상세
  Future<Map<String, dynamic>> getRoom(int roomId) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/rooms/$roomId'),
      headers: _headers,
    );
    return _handleResponse(response);
  }
  
  // ============================================================
  // 메시지
  // ============================================================

  /// 메시지 검색
  Future<List<dynamic>> searchMessages(int roomId, String query) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/rooms/$roomId/messages/search?q=${Uri.encodeComponent(query)}'),
      headers: _headers,
    );
    final data = _handleResponse(response);
    return data['messages'] ?? [];
  }

  /// 메시지 목록
  Future<List<dynamic>> getMessages(int roomId, {int? beforeId, int limit = 50}) async {
    var url = '$baseUrl/api/rooms/$roomId/messages?limit=$limit';
    if (beforeId != null) url += '&before_id=$beforeId';
    
    final response = await _client.get(Uri.parse(url), headers: _headers);
    final data = _handleResponse(response);
    return data['messages'] ?? [];
  }
  
  /// 텍스트 메시지 전송
  Future<Map<String, dynamic>> sendMessage(int roomId, String content, {int? parentId}) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/$roomId/messages'),
      headers: _headers,
      body: jsonEncode({
        'content': content,
        if (parentId != null) 'parent_id': parentId,
      }),
    );
    return _handleResponse(response);
  }
  
  /// 음성 파일 업로드
  Future<Map<String, dynamic>> uploadAudio(int roomId, File audioFile, {String language = 'ko'}) async {
    final uri = Uri.parse('$baseUrl/api/rooms/$roomId/audio');
    final request = http.MultipartRequest('POST', uri);
    
    request.headers['Authorization'] = 'Bearer $_token';
    request.fields['language'] = language;
    request.files.add(
      await http.MultipartFile.fromPath('file', audioFile.path,
        filename: path.basename(audioFile.path)),
    );
    
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    return _handleResponse(response);
  }
  
  /// 일반 파일 업로드
  Future<Map<String, dynamic>> uploadFile(int roomId, File file) async {
    final uri = Uri.parse('$baseUrl/api/rooms/$roomId/files');
    final request = http.MultipartRequest('POST', uri);

    request.headers['Authorization'] = 'Bearer $_token';
    request.files.add(
      await http.MultipartFile.fromPath('file', file.path,
        filename: path.basename(file.path)),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    return _handleResponse(response);
  }

  /// 음성 파일 검색
  Future<List<dynamic>> searchAudio(int roomId, {
    String? phone, String? dateFrom, String? dateTo,
  }) async {
    var url = '$baseUrl/api/rooms/$roomId/audio/search?';
    if (phone != null) url += 'phone=$phone&';
    if (dateFrom != null) url += 'date_from=$dateFrom&';
    if (dateTo != null) url += 'date_to=$dateTo&';
    
    final response = await _client.get(Uri.parse(url), headers: _headers);
    final data = _handleResponse(response);
    return data['audio_files'] ?? [];
  }
  
  /// 음성 파일 상세
  Future<Map<String, dynamic>> getAudioDetail(int audioId) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/audio/$audioId'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 음성 파일 다운로드 URL
  String getAudioDownloadUrl(int audioId) {
    return '$baseUrl/api/audio/$audioId/download';
  }

  /// 음성 파일 다운로드 (바이트로 반환)
  Future<List<int>> downloadAudio(int audioId) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/audio/$audioId/download'),
      headers: _headers,
    );
    if (response.statusCode == 200) {
      return response.bodyBytes;
    }
    throw ApiException('다운로드 실패', response.statusCode);
  }
  
  // ============================================================
  // 멤버 승인/거절
  // ============================================================

  /// 채팅방 삭제
  Future<Map<String, dynamic>> deleteRoom(int roomId) async {
    final response = await _client.delete(
      Uri.parse('$baseUrl/api/rooms/$roomId'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 채팅방 이름 변경
  Future<Map<String, dynamic>> renameRoom(int roomId, String newName) async {
    final response = await _client.patch(
      Uri.parse('$baseUrl/api/rooms/$roomId'),
      headers: _headers,
      body: jsonEncode({'name': newName}),
    );
    return _handleResponse(response);
  }

  /// 채팅방 나가기
  Future<Map<String, dynamic>> leaveRoom(int roomId) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/$roomId/leave'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 관리자 권한 이전
  Future<Map<String, dynamic>> transferAdmin(int roomId, int newAdminId) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/$roomId/transfer-admin'),
      headers: _headers,
      body: jsonEncode({'user_id': newAdminId}),
    );
    return _handleResponse(response);
  }

  /// 즐겨찾기 토글
  Future<Map<String, dynamic>> toggleFavorite(int roomId) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/$roomId/favorite'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 멤버 승인
  Future<Map<String, dynamic>> approveMember(int roomId, int userId) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/$roomId/members/$userId/approve'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 멤버 거절
  Future<Map<String, dynamic>> rejectMember(int roomId, int userId) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/rooms/$roomId/members/$userId/reject'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  // ============================================================
  // 동의 관리
  // ============================================================

  /// 동의 기록 저장
  Future<Map<String, dynamic>> recordConsent(List<Map<String, String>> consents) async {
    return _authenticatedPost(
      '$baseUrl/api/auth/consent',
      body: {'consents': consents},
    );
  }

  /// 동의 상태 조회
  Future<Map<String, dynamic>> getConsentStatus() async {
    return _authenticatedGet('$baseUrl/api/auth/consent/status');
  }

  /// 동의 철회
  Future<Map<String, dynamic>> withdrawConsent(String consentType) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/auth/consent/withdraw'),
      headers: _headers,
      body: jsonEncode({'type': consentType}),
    );
    return _handleResponse(response);
  }

  /// 회원 탈퇴
  Future<Map<String, dynamic>> deleteAccount() async {
    final response = await _client.delete(
      Uri.parse('$baseUrl/api/auth/account'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  // ============================================================
  // Drive 연동
  // ============================================================

  /// Drive 연동 상태 확인
  Future<Map<String, dynamic>> getDriveStatus() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/auth/drive/status'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// Drive 연동 해제
  Future<Map<String, dynamic>> disconnectDrive() async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/auth/drive/disconnect'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  // ============================================================
  // 과금/결제
  // ============================================================

  /// 과금 상태 조회
  Future<Map<String, dynamic>> getBillingStatus() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/billing/status'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 요금제 목록
  Future<Map<String, dynamic>> getBillingPlans() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/billing/plans'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 결제 이력
  Future<Map<String, dynamic>> getBillingHistory() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/billing/history'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 사용량 이력
  Future<Map<String, dynamic>> getUsageHistory({int limit = 20}) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/billing/usage?limit=$limit'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  /// 구독 해지
  Future<Map<String, dynamic>> cancelSubscription() async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/billing/subscription/cancel'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  // ============================================================
  // 음성파일 요약 조회
  // ============================================================

  /// 음성파일 요약 목록 (크로스 룸)
  Future<Map<String, dynamic>> getAudioSummaries({
    int? roomId,
    String? phone,
    String? name,
    String? dateFrom,
    String? dateTo,
    int page = 1,
    int perPage = 30,
  }) async {
    var url = '$baseUrl/api/audio/summaries?page=$page&per_page=$perPage';
    if (roomId != null) url += '&room_id=$roomId';
    if (phone != null && phone.isNotEmpty) url += '&phone=${Uri.encodeComponent(phone)}';
    if (name != null && name.isNotEmpty) url += '&name=${Uri.encodeComponent(name)}';
    if (dateFrom != null) url += '&date_from=$dateFrom';
    if (dateTo != null) url += '&date_to=$dateTo';

    final response = await _client.get(Uri.parse(url), headers: _headers);
    return _handleResponse(response);
  }

  /// 채팅방 Drive 폴더 URL 조회
  Future<Map<String, dynamic>> getRoomDriveFolder(int roomId) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/rooms/$roomId/drive-folder'),
      headers: _headers,
    );
    return _handleResponse(response);
  }

  // ============================================================
  // 인증된 요청 (401 시 refresh token으로 재시도)
  // ============================================================

  /// GET 요청 with auto-refresh
  Future<Map<String, dynamic>> _authenticatedGet(String url) async {
    var response = await _client.get(Uri.parse(url), headers: _headers);

    if (response.statusCode == 401 && _refreshToken != null) {
      final refreshed = await refreshAccessToken();
      if (refreshed) {
        response = await _client.get(Uri.parse(url), headers: _headers);
      }
    }

    return _handleResponse(response);
  }

  /// POST 요청 with auto-refresh
  Future<Map<String, dynamic>> _authenticatedPost(String url, {Object? body}) async {
    var response = await _client.post(
      Uri.parse(url),
      headers: _headers,
      body: body != null ? (body is String ? body : jsonEncode(body)) : null,
    );

    if (response.statusCode == 401 && _refreshToken != null) {
      final refreshed = await refreshAccessToken();
      if (refreshed) {
        response = await _client.post(
          Uri.parse(url),
          headers: _headers,
          body: body != null ? (body is String ? body : jsonEncode(body)) : null,
        );
      }
    }

    return _handleResponse(response);
  }

  // ============================================================
  // 응답 처리
  // ============================================================
  Map<String, dynamic> _handleResponse(http.Response response) {
    dynamic data;
    try {
      data = jsonDecode(response.body);
    } on FormatException {
      throw ApiException(
        '서버 응답 파싱 오류 (status=${response.statusCode}): ${response.body.length > 200 ? response.body.substring(0, 200) : response.body}',
        response.statusCode,
      );
    }
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return data;
    }
    throw ApiException(
      data['error'] ?? '알 수 없는 오류',
      response.statusCode,
    );
  }

  void dispose() => _client.close();
}

class ApiException implements Exception {
  final String message;
  final int statusCode;
  ApiException(this.message, this.statusCode);
  
  @override
  String toString() => 'ApiException($statusCode): $message';
}

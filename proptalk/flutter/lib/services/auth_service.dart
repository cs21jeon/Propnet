import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';
import 'socket_service.dart';
import 'notification_service.dart';

/// 인증 상태 관리
class AuthService extends ChangeNotifier {
  final ApiService api;
  late final SocketService socket;
  
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: [
      'email',
      'profile',
      'https://www.googleapis.com/auth/drive.file',
      'https://www.googleapis.com/auth/spreadsheets',
    ],
    serverClientId: '846392940969-a7k37gkon1p451mlnhp0oj9qaok1d8o1.apps.googleusercontent.com',
  );
  
  Map<String, dynamic>? _currentUser;
  bool _isLoading = false;
  bool _consentRequired = false;
  List<Map<String, dynamic>> _missingConsents = [];

  Map<String, dynamic>? get currentUser => _currentUser;
  bool get isLoggedIn => _currentUser != null;
  bool get isLoading => _isLoading;
  bool get consentRequired => _consentRequired;

  /// 서버에서 받은 missing_consents (각 항목: type, version, label, required)
  List<Map<String, dynamic>> get missingConsents => _missingConsents;
  
  AuthService(this.api) {
    socket = SocketService(api);
  }
  
  /// 앱 시작 시 자동 로그인 시도
  Future<void> tryAutoLogin() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    final refreshToken = prefs.getString('refresh_token');

    if (token != null) {
      api.setToken(token);
      if (refreshToken != null) {
        api.setRefreshToken(refreshToken);
      }
      try {
        final data = await api.getMe();
        _currentUser = data['user'];

        // 동의 상태 확인
        try {
          final consentData = await api.getConsentStatus();
          _consentRequired = consentData['consent_required'] == true;
          _missingConsents = _parseMissingConsents(
            consentData['missing'] ?? consentData['missing_consents'],
          );
        } catch (_) {
          // 동의 API가 아직 없는 서버 호환
          _consentRequired = false;
          _missingConsents = [];
        }

        socket.connect();
        NotificationService().registerToken(api);
        notifyListeners();
      } catch (e) {
        // 토큰 만료 등
        await prefs.remove('auth_token');
        await prefs.remove('refresh_token');
        api.setToken('');
        api.setRefreshToken(null);
        _consentRequired = false;
        _missingConsents = [];
        notifyListeners();
      }
    } else {
      _consentRequired = false;
      _missingConsents = [];
      notifyListeners();
    }
  }
  
  /// Google 로그인
  Future<bool> signInWithGoogle() async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final account = await _googleSignIn.signIn();
      if (account == null) {
        _isLoading = false;
        notifyListeners();
        return false;
      }
      
      final auth = await account.authentication;
      final idToken = auth.idToken;

      if (idToken == null) {
        throw Exception('Google ID Token을 가져올 수 없습니다');
      }

      // serverAuthCode 가져오기 (Drive 권한용)
      final serverAuthCode = account.serverAuthCode;

      // 서버에 토큰 검증 요청 (serverAuthCode 포함)
      final data = await api.loginWithGoogle(idToken, serverAuthCode: serverAuthCode);
      _currentUser = data['user'];

      // 동의 상태 확인 (서버 응답에서 구조화된 missing_consents 파싱)
      _consentRequired = data['consent_required'] == true;
      _missingConsents = _parseMissingConsents(data['missing_consents']);

      // 토큰 저장 (access_token 우선, 기존 token 호환)
      final prefs = await SharedPreferences.getInstance();
      final accessToken = data['access_token'] ?? data['token'];
      await prefs.setString('auth_token', accessToken);
      if (data['refresh_token'] != null) {
        await prefs.setString('refresh_token', data['refresh_token']);
      }

      // WebSocket 연결
      socket.connect();

      // FCM 토큰 등록
      NotificationService().registerToken(api);

      _isLoading = false;
      notifyListeners();
      return true;
      
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }
  
  /// 프로필 이름 변경
  Future<void> updateName(String name) async {
    final data = await api.updateProfile(name: name);
    _currentUser = data['user'];
    notifyListeners();
  }

  /// 동의 완료 처리
  void markConsentCompleted() {
    _consentRequired = false;
    _missingConsents = [];
    notifyListeners();
  }

  /// missing_consents 파싱 (문자열 리스트 또는 객체 리스트 모두 지원)
  List<Map<String, dynamic>> _parseMissingConsents(dynamic raw) {
    if (raw == null) return [];
    if (raw is List) {
      return raw.map<Map<String, dynamic>>((item) {
        if (item is Map) {
          return Map<String, dynamic>.from(item);
        }
        // 기존 서버 호환: 문자열 리스트 → 객체로 변환
        return {
          'type': item.toString(),
          'version': '2026-04-01',
          'label': _defaultLabelForType(item.toString()),
          'required': true,
        };
      }).toList();
    }
    return [];
  }

  /// 타입명에서 기본 레이블 생성 (서버가 label을 제공하지 않을 때)
  static String _defaultLabelForType(String type) {
    switch (type) {
      case 'terms':
        return '[필수] 서비스 이용약관';
      case 'privacy':
        return '[필수] 개인정보 수집 및 이용 동의';
      case 'overseas_transfer':
        return '[필수] 개인정보 국외 이전 동의';
      case 'proptalk_voice_data':
        return '[필수] 음성 데이터 처리 동의';
      default:
        return '[필수] $type';
    }
  }

  /// 로그아웃
  Future<void> signOut() async {
    await NotificationService().unregisterToken(api);
    await _googleSignIn.signOut();
    socket.disconnect();

    _currentUser = null;
    _consentRequired = false;
    _missingConsents = [];
    api.setToken('');
    api.setRefreshToken(null);

    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('refresh_token');

    notifyListeners();
  }
  
  @override
  void dispose() {
    socket.dispose();
    super.dispose();
  }
}

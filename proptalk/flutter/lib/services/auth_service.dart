import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';
import 'socket_service.dart';

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
  List<String> _missingConsents = [];

  Map<String, dynamic>? get currentUser => _currentUser;
  bool get isLoggedIn => _currentUser != null;
  bool get isLoading => _isLoading;
  bool get consentRequired => _consentRequired;
  List<String> get missingConsents => _missingConsents;
  
  AuthService(this.api) {
    socket = SocketService(api);
  }
  
  /// 앱 시작 시 자동 로그인 시도
  Future<void> tryAutoLogin() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');

    if (token != null) {
      api.setToken(token);
      try {
        final data = await api.getMe();
        _currentUser = data['user'];

        // 동의 상태 확인
        try {
          final consentData = await api.getConsentStatus();
          _consentRequired = consentData['consent_required'] == true;
          _missingConsents = List<String>.from(consentData['missing'] ?? []);
        } catch (_) {
          // 동의 API가 아직 없는 서버 호환
          _consentRequired = false;
          _missingConsents = [];
        }

        socket.connect();
        notifyListeners();
      } catch (e) {
        // 토큰 만료 등
        await prefs.remove('auth_token');
        api.setToken('');
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

      // 동의 상태 확인
      _consentRequired = data['consent_required'] == true;
      _missingConsents = List<String>.from(data['missing_consents'] ?? []);

      // 토큰 저장
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('auth_token', data['token']);

      // WebSocket 연결
      socket.connect();

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

  /// 로그아웃
  Future<void> signOut() async {
    await _googleSignIn.signOut();
    socket.disconnect();

    _currentUser = null;
    _consentRequired = false;
    _missingConsents = [];
    api.setToken('');

    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');

    notifyListeners();
  }
  
  @override
  void dispose() {
    socket.dispose();
    super.dispose();
  }
}

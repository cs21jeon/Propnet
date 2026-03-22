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
    scopes: ['email', 'profile'],
  );
  
  Map<String, dynamic>? _currentUser;
  bool _isLoading = false;
  
  Map<String, dynamic>? get currentUser => _currentUser;
  bool get isLoggedIn => _currentUser != null;
  bool get isLoading => _isLoading;
  
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
        socket.connect();
        notifyListeners();
      } catch (e) {
        // 토큰 만료 등
        await prefs.remove('auth_token');
        api.setToken('');
      }
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
      
      // 서버에 토큰 검증 요청
      final data = await api.loginWithGoogle(idToken);
      _currentUser = data['user'];
      
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
  
  /// 로그아웃
  Future<void> signOut() async {
    await _googleSignIn.signOut();
    socket.disconnect();
    
    _currentUser = null;
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

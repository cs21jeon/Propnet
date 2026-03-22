import 'package:shared_preferences/shared_preferences.dart';

/// 로그인 관련 설정 저장 서비스
class LoginPreferences {
  static const _saveEmailKey = 'save_email';
  static const _savedEmailKey = 'saved_email';
  static const _autoLoginKey = 'auto_login';

  /// 이메일 저장 여부 가져오기
  Future<bool> getSaveEmail() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_saveEmailKey) ?? false;
  }

  /// 이메일 저장 여부 설정
  Future<void> setSaveEmail(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_saveEmailKey, value);
  }

  /// 저장된 이메일 가져오기
  Future<String?> getSavedEmail() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_savedEmailKey);
  }

  /// 이메일 저장
  Future<void> setSavedEmail(String? email) async {
    final prefs = await SharedPreferences.getInstance();
    if (email != null && email.isNotEmpty) {
      await prefs.setString(_savedEmailKey, email);
    } else {
      await prefs.remove(_savedEmailKey);
    }
  }

  /// 자동 로그인 여부 가져오기
  Future<bool> getAutoLogin() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_autoLoginKey) ?? true; // 기본값: true
  }

  /// 자동 로그인 여부 설정
  Future<void> setAutoLogin(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_autoLoginKey, value);
  }

  /// 로그인 설정 모두 불러오기
  Future<LoginSettings> getSettings() async {
    final saveEmail = await getSaveEmail();
    final savedEmail = await getSavedEmail();
    final autoLogin = await getAutoLogin();

    return LoginSettings(
      saveEmail: saveEmail,
      savedEmail: savedEmail,
      autoLogin: autoLogin,
    );
  }

  /// 로그아웃 시 자동 로그인 설정 확인
  Future<bool> shouldAutoLogin() async {
    return await getAutoLogin();
  }

  /// 로그아웃 시 설정 정리 (자동 로그인 해제 시)
  Future<void> clearAutoLoginIfDisabled() async {
    final autoLogin = await getAutoLogin();
    if (!autoLogin) {
      // 자동 로그인이 꺼져 있으면 토큰은 유지하되, 다음 앱 시작 시 로그인 화면 표시
      // 실제 토큰 삭제는 TokenStorage에서 처리
    }
  }
}

/// 로그인 설정 데이터 클래스
class LoginSettings {
  final bool saveEmail;
  final String? savedEmail;
  final bool autoLogin;

  const LoginSettings({
    required this.saveEmail,
    this.savedEmail,
    required this.autoLogin,
  });
}

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:propedia/core/network/api_client.dart';
import 'package:propedia/core/storage/token_storage.dart';
import 'package:propedia/data/datasources/remote/auth_api.dart';
import 'package:propedia/data/repositories/auth_repository.dart';
import 'package:propedia/domain/entities/user.dart';

// TokenStorage Provider
final tokenStorageProvider = Provider<TokenStorage>((ref) {
  return TokenStorage();
});

// ApiClient Provider
final apiClientProvider = Provider<ApiClient>((ref) {
  final tokenStorage = ref.watch(tokenStorageProvider);
  return ApiClient(tokenStorage: tokenStorage);
});

// AuthApi Provider
final authApiProvider = Provider<AuthApi>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AuthApi(apiClient.dio);
});

// AuthRepository Provider
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final authApi = ref.watch(authApiProvider);
  final tokenStorage = ref.watch(tokenStorageProvider);
  return AuthRepository(authApi: authApi, tokenStorage: tokenStorage);
});

// 인증 상태
enum AuthStatus {
  initial,
  loading,
  authenticated,
  unauthenticated,
  guest,
  consentRequired,
  userTypeRequired,
  error,
}

// 인증 상태 클래스
class AuthState {
  final AuthStatus status;
  final User? user;
  final String? errorMessage;
  final List<Map<String, dynamic>> missingConsents;
  final bool isNewUser;

  const AuthState({
    this.status = AuthStatus.initial,
    this.user,
    this.errorMessage,
    this.missingConsents = const [],
    this.isNewUser = false,
  });

  AuthState copyWith({
    AuthStatus? status,
    User? user,
    String? errorMessage,
    List<Map<String, dynamic>>? missingConsents,
    bool? isNewUser,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: user ?? this.user,
      errorMessage: errorMessage,
      missingConsents: missingConsents ?? this.missingConsents,
      isNewUser: isNewUser ?? this.isNewUser,
    );
  }
}

// AuthNotifier
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _authRepository;
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
    serverClientId: kIsWeb
        ? null
        : '846392940969-sv2936v0tm85j8hvdn3srcmtei1kk25e.apps.googleusercontent.com',
  );

  /// 웹에서 renderButton 사용을 위해 GoogleSignIn 인스턴스 노출
  GoogleSignIn get googleSignIn => _googleSignIn;

  AuthNotifier(this._authRepository) : super(const AuthState());

  /// 앱 시작 시 자동 로그인 체크
  Future<void> checkAuth() async {
    state = state.copyWith(status: AuthStatus.loading);

    try {
      final user = await _authRepository.checkAutoLogin();
      if (user != null) {
        debugPrint('[AUTH] 자동 로그인 성공: ${user.email}');
        state = AuthState(status: AuthStatus.authenticated, user: user);
      } else {
        debugPrint('[AUTH] 자동 로그인 실패: 토큰 없음 또는 서버 응답 실패');
        state = const AuthState(status: AuthStatus.guest);
      }
    } catch (e) {
      debugPrint('[AUTH] 자동 로그인 에러: $e');
      state = const AuthState(status: AuthStatus.guest);
    }
  }

  /// 로그인 결과 처리 (모바일/웹 공통)
  void _handleLoginResult(LoginResult result) {
    if (result.consentRequired) {
      debugPrint('[AUTH] 동의 필요: ${result.missingConsents.length}개 항목');
      state = AuthState(
        status: AuthStatus.consentRequired,
        user: result.user,
        missingConsents: result.missingConsents,
        isNewUser: result.isNewUser,
      );
    } else if (result.isNewUser && result.user != null) {
      debugPrint('[AUTH] 신규 유저 → 유저 타입 선택 필요: ${result.user!.email}');
      state = AuthState(
        status: AuthStatus.userTypeRequired,
        user: result.user,
        isNewUser: true,
      );
    } else if (result.user != null) {
      debugPrint('[AUTH] 로그인 성공: ${result.user!.email} (${result.user!.name})');
      state = AuthState(status: AuthStatus.authenticated, user: result.user);
    } else {
      throw Exception('로그인 응답에 사용자 정보가 없습니다');
    }
  }

  /// 웹: Google 계정 처리 (renderButton 콜백)
  Future<void> processGoogleAccount(GoogleSignInAccount account) async {
    state = state.copyWith(status: AuthStatus.loading);
    try {
      debugPrint('[AUTH] 웹 Google 계정: ${account.email}');
      final auth = await account.authentication;
      final idToken = auth.idToken;
      debugPrint('[AUTH] idToken: ${idToken != null ? '${idToken.substring(0, 20)}...' : 'null'}');

      if (idToken == null) {
        throw Exception('Google ID Token을 가져올 수 없습니다');
      }

      debugPrint('[AUTH] 서버 로그인 요청 중...');
      final result = await _authRepository.loginWithGoogle(idToken: idToken);
      _handleLoginResult(result);
    } catch (e, stack) {
      debugPrint('[AUTH] 로그인 에러: $e');
      debugPrint('[AUTH] 스택: $stack');
      state = AuthState(
        status: AuthStatus.error,
        errorMessage: e.toString().replaceFirst('Exception: ', ''),
      );
    }
  }

  /// Google 로그인 (모바일)
  Future<void> signInWithGoogle() async {
    state = state.copyWith(status: AuthStatus.loading);

    try {
      debugPrint('[AUTH] Google 로그인 시작...');
      // 캐시된 만료 토큰 방지: 기존 세션 클리어 후 새로 로그인
      await _googleSignIn.signOut();
      final account = await _googleSignIn.signIn();
      if (account == null) {
        debugPrint('[AUTH] Google 로그인 취소됨');
        state = const AuthState(status: AuthStatus.guest);
        return;
      }

      debugPrint('[AUTH] Google 계정: ${account.email}');
      final auth = await account.authentication;
      final idToken = auth.idToken;
      debugPrint('[AUTH] idToken: ${idToken != null ? '${idToken.substring(0, 20)}...' : 'null'}');

      if (idToken == null) {
        throw Exception('Google ID Token을 가져올 수 없습니다');
      }

      // 서버에 토큰 검증 요청
      debugPrint('[AUTH] 서버 로그인 요청 중...');
      final result = await _authRepository.loginWithGoogle(idToken: idToken);
      _handleLoginResult(result);
    } catch (e, stack) {
      debugPrint('[AUTH] 로그인 에러: $e');
      debugPrint('[AUTH] 스택: $stack');
      state = AuthState(
        status: AuthStatus.error,
        errorMessage: e.toString().replaceFirst('Exception: ', ''),
      );
    }
  }

  /// 동의 완료 처리
  Future<void> submitConsent(List<Map<String, dynamic>> consents) async {
    try {
      debugPrint('[AUTH] 동의 제출: ${consents.length}개 항목');
      await _authRepository.recordConsent(consents);
      debugPrint('[AUTH] 동의 저장 성공');

      // 신규 유저는 동의 후 유저 타입 선택으로 이동
      if (state.isNewUser) {
        debugPrint('[AUTH] 신규 유저 → 유저 타입 선택 화면으로');
        state = AuthState(
          status: AuthStatus.userTypeRequired,
          user: state.user,
          isNewUser: true,
        );
        return;
      }

      // 기존 유저는 동의 완료 후 인증 상태로 전환
      if (state.user != null) {
        state = AuthState(status: AuthStatus.authenticated, user: state.user);
      } else {
        // user가 없는 경우 서버에서 다시 조회
        final user = await _authRepository.getMe();
        if (user != null) {
          state = AuthState(status: AuthStatus.authenticated, user: user);
        } else {
          throw Exception('사용자 정보를 가져올 수 없습니다');
        }
      }
    } catch (e) {
      debugPrint('[AUTH] 동의 저장 에러: $e');
      rethrow;
    }
  }

  /// 유저 타입 선택 완료 (일반 사용자)
  Future<void> selectUserType() async {
    try {
      debugPrint('[AUTH] 유저 타입 선택: user');
      await _authRepository.selectUserType('user');
      debugPrint('[AUTH] 유저 타입 선택 완료');
      state = AuthState(status: AuthStatus.authenticated, user: state.user);
    } catch (e) {
      debugPrint('[AUTH] 유저 타입 선택 에러: $e');
      rethrow;
    }
  }

  /// Agent 가입 신청 완료 후 홈으로 이동
  void completeAgentRequest() {
    state = AuthState(status: AuthStatus.authenticated, user: state.user);
  }

  /// 로그아웃
  Future<void> logout() async {
    try {
      await _googleSignIn.signOut();
    } catch (_) {}
    await _authRepository.logout();
    state = const AuthState(status: AuthStatus.guest);
  }

  /// 에러 상태 초기화
  void clearError() {
    if (state.status == AuthStatus.error) {
      state = state.copyWith(
        status: AuthStatus.guest,
        errorMessage: null,
      );
    }
  }
}

// AuthNotifier Provider
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authRepository = ref.watch(authRepositoryProvider);
  return AuthNotifier(authRepository);
});

// PropSheet 저장 권한은 propsheet_provider.dart에서 관리

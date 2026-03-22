import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';
import 'package:propedia/presentation/screens/auth/login_screen.dart';
import 'package:propedia/presentation/screens/home/home_screen.dart';
import 'package:propedia/presentation/screens/splash/splash_screen.dart';
import 'package:propedia/presentation/screens/search/search_road_screen.dart';
import 'package:propedia/presentation/screens/search/search_jibun_screen.dart';
import 'package:propedia/presentation/screens/search/search_map_screen.dart';
import 'package:propedia/presentation/screens/search/result_screen.dart';
import 'package:propedia/presentation/screens/history/history_screen.dart';
import 'package:propedia/presentation/screens/favorites/favorites_screen.dart';
import 'package:propedia/presentation/screens/profile/profile_screen.dart';
import 'package:propedia/presentation/screens/property/property_home_screen.dart';
import 'package:propedia/presentation/screens/property/property_list_screen.dart';
import 'package:propedia/presentation/screens/property/property_detail_screen.dart';
import 'package:propedia/presentation/screens/property/property_map_screen.dart';
import 'package:propedia/presentation/screens/property/property_search_screen.dart';
import 'package:propedia/presentation/screens/property/property_search_map_screen.dart';
import 'package:propedia/data/dto/property_dto.dart';

// 인증 상태 변경을 감지하는 Listenable
class AuthNotifierListenable extends ChangeNotifier {
  AuthNotifierListenable(this._ref) {
    _ref.listen(authProvider, (previous, next) {
      notifyListeners();
    });
  }

  final Ref _ref;
}

final routerProvider = Provider<GoRouter>((ref) {
  final authNotifier = AuthNotifierListenable(ref);

  return GoRouter(
    initialLocation: '/',
    refreshListenable: authNotifier,
    redirect: (context, state) {
      final authState = ref.read(authProvider);
      final isAuthenticated = authState.status == AuthStatus.authenticated;
      final isGuest = authState.status == AuthStatus.guest;
      final canAccess = isAuthenticated || isGuest;
      final isLoading = authState.status == AuthStatus.loading ||
          authState.status == AuthStatus.initial;
      final isAuthRoute = state.matchedLocation == '/login';

      // 로딩 중이면 스플래시 화면
      if (isLoading) {
        return '/';
      }

      // 인증된 사용자가 인증 페이지 접근하면 홈으로 (guest는 로그인 가능)
      if (isAuthenticated && isAuthRoute) {
        return '/home';
      }

      // 인증되었거나 게스트이고 스플래시 화면이면 홈으로
      if (canAccess && state.matchedLocation == '/') {
        return '/home';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/home',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/search/road',
        builder: (context, state) => const SearchRoadScreen(),
      ),
      GoRoute(
        path: '/search/jibun',
        builder: (context, state) => const SearchJibunScreen(),
      ),
      GoRoute(
        path: '/search/map',
        builder: (context, state) => const SearchMapScreen(),
      ),
      GoRoute(
        path: '/result',
        builder: (context, state) => const ResultScreen(),
      ),
      GoRoute(
        path: '/history',
        builder: (context, state) => const HistoryScreen(),
      ),
      GoRoute(
        path: '/favorites',
        builder: (context, state) => const FavoritesScreen(),
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) => const ProfileScreen(),
      ),
      // 매물 관련 라우트
      GoRoute(
        path: '/property',
        builder: (context, state) => const PropertyHomeScreen(),
      ),
      GoRoute(
        path: '/property/list',
        builder: (context, state) {
          final category = state.uri.queryParameters['category'];
          return PropertyListScreen(initialCategory: category);
        },
      ),
      GoRoute(
        path: '/property/detail/:recordId',
        builder: (context, state) {
          final recordId = state.pathParameters['recordId']!;
          return PropertyDetailScreen(recordId: recordId);
        },
      ),
      GoRoute(
        path: '/property/map',
        builder: (context, state) => const PropertyMapScreen(),
      ),
      GoRoute(
        path: '/property/search',
        builder: (context, state) => const PropertySearchScreen(),
      ),
      GoRoute(
        path: '/property/search-map',
        builder: (context, state) {
          final markers = state.extra as List<PropertyMapMarker>? ?? [];
          return PropertySearchMapScreen(markers: markers);
        },
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Text('페이지를 찾을 수 없습니다: ${state.error}'),
      ),
    ),
  );
});

import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:propedia/core/constants/app_colors.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';
import 'package:propedia/presentation/providers/history_provider.dart';
import 'package:propedia/presentation/providers/favorites_provider.dart';
import 'package:propedia/presentation/providers/notice_provider.dart';
import 'package:propedia/presentation/widgets/ads/banner_ad_widget.dart';
import 'package:propedia/presentation/widgets/common/app_drawer.dart';
import 'package:propedia/presentation/widgets/common/app_footer.dart';
import 'package:propedia/presentation/widgets/common/notice_dialog.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  Timer? _noticeTimer;

  @override
  void initState() {
    super.initState();
    // 홈 화면 진입 시 데이터 로드
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadData();
    });
    // 30분 주기로 공지 재확인
    _noticeTimer = Timer.periodic(const Duration(minutes: 30), (_) {
      ref.read(noticeProvider.notifier).fetchNotices();
    });
  }

  @override
  void dispose() {
    _noticeTimer?.cancel();
    super.dispose();
  }

  void _loadData() {
    final authState = ref.read(authProvider);

    // 로컬 데이터 로드
    ref.read(historyProvider.notifier).loadLocalHistory();
    ref.read(favoritesProvider.notifier).loadLocalFavorites();

    // 로그인 상태면 서버 동기화도 수행
    if (authState.status == AuthStatus.authenticated) {
      ref.read(historyProvider.notifier).syncFromServer();
      ref.read(favoritesProvider.notifier).syncFromServer();
    }

    // 공지사항 확인
    ref.read(noticeProvider.notifier).fetchNotices();
  }

  @override
  Widget build(BuildContext context) {
    // 공지사항 표시
    ref.listen<NoticeState>(noticeProvider, (previous, next) {
      if (!next.isLoading && !next.hasShown && next.visibleNotices.isNotEmpty) {
        ref.read(noticeProvider.notifier).markShown();
        final notice = next.visibleNotices.first;
        NoticeDialog.show(
          context,
          notice: notice,
          onDismiss: () =>
              ref.read(noticeProvider.notifier).dismissNotice(notice.id),
          onDismissForToday: notice.isDismissible
              ? () => ref.read(noticeProvider.notifier).dismissForToday(notice.id)
              : null,
        );
      }
    });

    // 로그인 상태 변경 감지
    ref.listen<AuthState>(authProvider, (previous, next) {
      if (previous?.status != next.status) {
        if (next.status == AuthStatus.authenticated) {
          // 로그인됨 - 서버 동기화
          ref.read(historyProvider.notifier).syncFromServer();
          ref.read(favoritesProvider.notifier).syncFromServer();
        } else if (next.status == AuthStatus.guest) {
          // 로그아웃됨 - 로컬 데이터 로드
          ref.read(historyProvider.notifier).loadLocalHistory();
          ref.read(favoritesProvider.notifier).loadLocalFavorites();
        }
      }
    });

    final authState = ref.watch(authProvider);
    final user = authState.user;

    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 72,
        leading: Builder(
          builder: (context) => IconButton(
            icon: const Icon(Icons.menu),
            onPressed: () => Scaffold.of(context).openDrawer(),
          ),
        ),
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset(
              'assets/images/proppedia_logo.png',
              height: 56,
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Proppedia',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: AppColors.primary,
                  ),
                ),
                Text(
                  '부동산백과',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ],
        ),
        centerTitle: true,
      ),
      drawer: const AppDrawer(currentApp: AppType.main),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 사용자 정보 카드 (게스트/로그인 분기)
              if (authState.status != AuthStatus.authenticated)
                _buildGuestCard()
              else
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 30,
                          backgroundColor: AppColors.primary,
                          child: Text(
                            (user?.name?.isNotEmpty == true
                                    ? user!.name![0]
                                    : user?.email[0] ?? 'U')
                                .toUpperCase(),
                            style: const TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                user?.name ?? '사용자',
                                style: Theme.of(context)
                                    .textTheme
                                    .titleMedium
                                    ?.copyWith(fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                user?.email ?? '',
                                style: Theme.of(context)
                                    .textTheme
                                    .bodyMedium
                                    ?.copyWith(color: Colors.grey[600]),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 24),

              // 검색 방식 선택
              Text(
                '건축물 검색',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 16),

              // 도로명 검색
              _SearchOptionCard(
                icon: Icons.signpost_outlined,
                title: '도로명 주소로 검색',
                subtitle: '도로명 + 건물번호로 검색합니다',
                onTap: () {
                  context.push('/search/road');
                },
              ),
              const SizedBox(height: 12),

              // 지번 검색
              _SearchOptionCard(
                icon: Icons.location_on_outlined,
                title: '지번 주소로 검색',
                subtitle: '법정동 + 본번/부번으로 검색합니다',
                onTap: () {
                  context.push('/search/jibun');
                },
              ),
              const SizedBox(height: 12),

              // 지도 검색
              _SearchOptionCard(
                icon: Icons.map_outlined,
                title: '지도에서 검색',
                subtitle: '지도에서 위치를 선택하여 검색합니다',
                onTap: () {
                  context.push('/search/map');
                },
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 배너 광고 (웹이 아닌 경우에만 표시)
          if (!kIsWeb) const BannerAdWidget(),
          _buildBottomNavigation(context),
          const AppFooterSimple(),
        ],
      ),
    );
  }

  Widget _buildBottomNavigation(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        border: Border(
          top: BorderSide(color: isDark ? Colors.grey[700]! : Colors.grey[200]!),
        ),
      ),
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildNavItem(
            context: context,
            icon: Icons.home,
            label: '홈',
            isActive: true,
            onTap: () {},
          ),
          _buildNavItem(
            context: context,
            icon: Icons.history,
            label: '검색기록',
            isActive: false,
            onTap: () => context.go('/history'),
          ),
          _buildNavItem(
            context: context,
            icon: Icons.star_outline,
            label: '즐겨찾기',
            isActive: false,
            onTap: () => context.go('/favorites'),
          ),
          _buildNavItem(
            context: context,
            icon: Icons.person_outline,
            label: '프로필',
            isActive: false,
            onTap: () => context.go('/profile'),
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem({
    required BuildContext context,
    required IconData icon,
    required String label,
    required bool isActive,
    required VoidCallback onTap,
  }) {
    final color = isActive ? AppColors.primary : Colors.grey[400];

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        hoverColor: AppColors.primary.withValues(alpha: 0.1),
        splashColor: AppColors.primary.withValues(alpha: 0.2),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: color, size: 26),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// 게스트 모드 카드
  Widget _buildGuestCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: Colors.grey[400],
                  child: const Icon(
                    Icons.person_outline,
                    size: 32,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '체험 모드',
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '로그인하면 모든 기기에서 데이터를 동기화할 수 있습니다',
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: Colors.grey[600]),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => context.push('/login'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: const Text('Google 계정으로 로그인'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SearchOptionCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _SearchOptionCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  icon,
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey[600],
                          ),
                    ),
                  ],
                ),
              ),
              Icon(
                Icons.chevron_right,
                color: Colors.grey[400],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

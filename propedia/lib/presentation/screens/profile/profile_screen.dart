import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:propedia/core/constants/app_colors.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';
import 'package:propedia/presentation/providers/theme_provider.dart';
import 'package:propedia/presentation/providers/history_provider.dart';
import 'package:propedia/presentation/providers/favorites_provider.dart';
import 'package:propedia/presentation/providers/app_info_provider.dart';
import 'package:propedia/presentation/widgets/common/app_footer.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  @override
  void initState() {
    super.initState();
    // 화면 진입 시 데이터 로드
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadData();
    });
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
  }

  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('로그아웃'),
        content: const Text('정말 로그아웃하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('로그아웃'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      // 로컬 DB 및 상태 초기화
      await ref.read(historyProvider.notifier).reset();
      await ref.read(favoritesProvider.notifier).reset();
      // 로그아웃
      ref.read(authProvider.notifier).logout();
    }
  }

  @override
  Widget build(BuildContext context) {
    // 로그인 상태 변경 감지
    ref.listen<AuthState>(authProvider, (previous, next) {
      if (previous?.status != next.status) {
        if (next.status == AuthStatus.authenticated) {
          // 로그인됨 - 데이터 로드 및 서버 동기화
          _loadData();
        } else if (next.status == AuthStatus.guest) {
          // 로그아웃됨 - 이미 reset 호출됨
        }
      }
    });

    final authState = ref.watch(authProvider);
    final isAuthenticated = authState.status == AuthStatus.authenticated;
    final user = authState.user;
    final themeMode = ref.watch(themeModeProvider);
    final isDarkMode = themeMode == ThemeMode.dark;
    final historyState = ref.watch(historyProvider);
    final favoritesState = ref.watch(favoritesProvider);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/home'),
        ),
        title: const Text(
          '프로필',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          _loadData();
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 사용자 정보 카드
              _buildUserInfoCard(user),
              const SizedBox(height: 16),

              // 설정 섹션
              _buildSettingsSection(isDarkMode),
              const SizedBox(height: 16),

              // 사용 통계 섹션 (로컬 데이터 기반)
              _buildLocalStatsSection(historyState, favoritesState),
              const SizedBox(height: 24),

              // 로그아웃 버튼 (로그인한 경우에만 표시)
              if (isAuthenticated)
                _buildLogoutButton(),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
      bottomNavigationBar: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _buildBottomNavigation(),
          const AppFooterSimple(),
        ],
      ),
    );
  }

  Widget _buildUserInfoCard(dynamic user) {
    final authState = ref.watch(authProvider);
    final isAuthenticated = authState.status == AuthStatus.authenticated;

    if (!isAuthenticated) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              Row(
                children: [
                  CircleAvatar(
                    radius: 36,
                    backgroundColor: Colors.grey[400],
                    child: const Icon(
                      Icons.person_outline,
                      size: 36,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          '체험 모드',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '로그인하면 모든 기기에서 데이터를 동기화할 수 있습니다',
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey[600],
                          ),
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

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            CircleAvatar(
              radius: 36,
              backgroundColor: AppColors.primary,
              child: Text(
                (user?.name?.isNotEmpty == true
                        ? user!.name![0]
                        : user?.email[0] ?? 'U')
                    .toUpperCase(),
                style: const TextStyle(
                  fontSize: 28,
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
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user?.email ?? '',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSettingsSection(bool isDarkMode) {
    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Text(
              '설정',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          // 다크모드 토글
          SwitchListTile(
            title: const Text('다크 모드'),
            subtitle: Text(
              isDarkMode ? '다크 테마 사용 중' : '라이트 테마 사용 중',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[500],
              ),
            ),
            secondary: Icon(
              isDarkMode ? Icons.dark_mode : Icons.light_mode,
              color: isDarkMode ? Colors.amber : Colors.orange,
            ),
            value: isDarkMode,
            onChanged: (value) {
              ref.read(themeModeProvider.notifier).toggleDarkMode();
            },
          ),
          const Divider(height: 1),
          // 앱 버전
          ListTile(
            leading: const Icon(Icons.info_outline),
            title: const Text('앱 버전'),
            trailing: Text(
              ref.watch(appVersionProvider),
              style: TextStyle(
                color: Colors.grey[600],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLocalStatsSection(HistoryState historyState, FavoritesState favoritesState) {
    final historyCount = historyState.localHistory.length;
    final favoritesCount = favoritesState.localFavorites.length;

    // 검색 타입별 통계 계산
    int roadCount = 0;
    int jibunCount = 0;
    int mapCount = 0;

    for (final item in historyState.localHistory) {
      final searchType = item.searchType;
      if (searchType == 'road') {
        roadCount++;
      } else if (searchType == 'jibun') {
        jibunCount++;
      } else if (searchType == 'map') {
        mapCount++;
      }
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '사용 통계',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            // 주요 통계 그리드
            Row(
              children: [
                Expanded(
                  child: _buildStatItem(
                    icon: Icons.search,
                    label: '검색 기록',
                    value: '$historyCount건',
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildStatItem(
                    icon: Icons.star,
                    label: '즐겨찾기',
                    value: '$favoritesCount개',
                    color: Colors.amber,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 12),
            // 검색 타입별 통계
            const Text(
              '검색 방법별 통계',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _buildSearchTypeItem(
                    icon: Icons.signpost_outlined,
                    label: '도로명',
                    count: roadCount,
                  ),
                ),
                Expanded(
                  child: _buildSearchTypeItem(
                    icon: Icons.landscape_outlined,
                    label: '지번',
                    count: jibunCount,
                  ),
                ),
                Expanded(
                  child: _buildSearchTypeItem(
                    icon: Icons.map_outlined,
                    label: '지도',
                    count: mapCount,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 18, color: color),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchTypeItem({
    required IconData icon,
    required String label,
    required int count,
  }) {
    return Column(
      children: [
        Icon(icon, size: 24, color: AppColors.primary),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
        const SizedBox(height: 2),
        Text(
          '$count회',
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  Widget _buildLogoutButton() {
    return OutlinedButton.icon(
      onPressed: _logout,
      icon: const Icon(Icons.logout, color: Colors.red),
      label: const Text(
        '로그아웃',
        style: TextStyle(color: Colors.red),
      ),
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 16),
        side: const BorderSide(color: Colors.red),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }

  Widget _buildBottomNavigation() {
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
            icon: Icons.home_outlined,
            label: '홈',
            isActive: false,
            onTap: () => context.go('/home'),
          ),
          _buildNavItem(
            icon: Icons.history,
            label: '검색기록',
            isActive: false,
            onTap: () => context.go('/history'),
          ),
          _buildNavItem(
            icon: Icons.star_outline,
            label: '즐겨찾기',
            isActive: false,
            onTap: () => context.go('/favorites'),
          ),
          _buildNavItem(
            icon: Icons.person,
            label: '프로필',
            isActive: true,
            onTap: () {},
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem({
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
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
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
}

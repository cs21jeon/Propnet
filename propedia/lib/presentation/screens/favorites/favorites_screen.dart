import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:propedia/core/constants/app_colors.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';
import 'package:propedia/presentation/providers/favorites_provider.dart';
import 'package:propedia/presentation/providers/building_provider.dart';
import 'package:propedia/presentation/widgets/ads/banner_ad_widget.dart';
import 'package:propedia/presentation/widgets/common/app_footer.dart';

class FavoritesScreen extends ConsumerStatefulWidget {
  const FavoritesScreen({super.key});

  @override
  ConsumerState<FavoritesScreen> createState() => _FavoritesScreenState();
}

class _FavoritesScreenState extends ConsumerState<FavoritesScreen> {
  @override
  void initState() {
    super.initState();
    // 화면 진입 시 데이터 로드
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      ref.read(favoritesProvider.notifier).loadLocalFavorites();
      // 로그인 상태에서만 서버 동기화
      final authState = ref.read(authProvider);
      if (authState.status == AuthStatus.authenticated) {
        await ref.read(favoritesProvider.notifier).syncFromServer();
      }
    });
  }

  Future<void> _navigateToResult(Map<String, dynamic> item) async {
    final pnu = item['pnu'] as String?;
    if (pnu == null || pnu.length < 19) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('유효하지 않은 즐겨찾기입니다')),
      );
      return;
    }

    // PNU에서 코드 추출
    final sigunguCd = pnu.substring(0, 5);
    final bjdongCd = pnu.substring(5, 10);
    final landType = pnu.substring(10, 11);
    final bun = pnu.substring(11, 15);
    final ji = pnu.substring(15, 19);

    // 지번 검색 수행
    await ref.read(buildingSearchProvider.notifier).searchByJibun(
          bjdongCode: sigunguCd + bjdongCd,
          bun: bun,
          ji: ji,
          landType: landType == '2' ? '2' : '1',
        );

    if (mounted) {
      context.push('/result');
    }
  }

  Future<void> _deleteFavorite(int id) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('즐겨찾기 삭제'),
        content: const Text('이 즐겨찾기를 삭제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('삭제', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await ref.read(favoritesProvider.notifier).deleteServerFavorite(id);
    }
  }

  Future<void> _editFavorite(Map<String, dynamic> item) async {
    final id = item['id'] as int?;
    if (id == null) return;

    final nicknameController = TextEditingController(text: item['nickname'] as String? ?? '');
    final memoController = TextEditingController(text: item['memo'] as String? ?? '');

    final result = await showDialog<Map<String, String?>>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('즐겨찾기 편집'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '별칭',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: nicknameController,
              decoration: InputDecoration(
                hintText: '예: 투자 검토중',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              '메모',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: memoController,
              maxLines: 3,
              decoration: InputDecoration(
                hintText: '메모를 입력하세요',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                contentPadding: const EdgeInsets.all(16),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('취소'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, {
              'nickname': nicknameController.text.isEmpty ? null : nicknameController.text,
              'memo': memoController.text.isEmpty ? null : memoController.text,
            }),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
            ),
            child: const Text('저장'),
          ),
        ],
      ),
    );

    if (result != null) {
      // TODO: 서버 업데이트 API 호출
      await ref.read(favoritesProvider.notifier).loadServerFavorites();
    }
  }

  @override
  Widget build(BuildContext context) {
    final favoritesState = ref.watch(favoritesProvider);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/home'),
        ),
        title: const Text(
          '즐겨찾기',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
      ),
      body: _buildBody(favoritesState),
      bottomNavigationBar: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 배너 광고 (웹이 아닌 경우에만 표시)
          if (!kIsWeb) const BannerAdWidget(),
          _buildBottomNavigation(),
          const AppFooterSimple(),
        ],
      ),
    );
  }

  Widget _buildBody(FavoritesState state) {
    final authState = ref.watch(authProvider);
    final isGuest = authState.status == AuthStatus.guest;

    if (state.isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('즐겨찾기를 불러오는 중...'),
          ],
        ),
      );
    }

    // 로컬 즐겨찾기 표시
    if (state.localFavorites.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.star,
              size: 64,
              color: Colors.amber[200],
            ),
            const SizedBox(height: 16),
            Text(
              isGuest ? '로그인 후 즐겨찾기 기능을\n사용할 수 있습니다' : '즐겨찾기가 없습니다',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            if (isGuest) ...[
              ElevatedButton(
                onPressed: () => context.push('/login'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text('로그인'),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () => context.go('/home'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text('게스트로 검색하기'),
              ),
            ] else
              ElevatedButton(
                onPressed: () => context.go('/home'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text('검색하러 가기'),
              ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(favoritesProvider.notifier).syncFromServer();
      },
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.localFavorites.length,
        itemBuilder: (context, index) {
          final item = state.localFavorites[index];
          return _buildLocalFavoriteCard(item);
        },
      ),
    );
  }

  Widget _buildLocalFavoriteCard(dynamic item) {
    final jibunAddress = item.jibunAddress as String?;
    final roadAddress = item.roadAddress as String?;
    final buildingName = item.buildingName as String?;
    final memo = item.memo as String?;
    final id = item.id as String;

    // 지번 주소 우선 표시
    final displayText = jibunAddress ?? item.displayAddress ?? '';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.amber.withValues(alpha: 0.3)),
      ),
      child: InkWell(
        onTap: () => _navigateToResultFromLocal(item),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 즐겨찾기 아이콘
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: Colors.amber.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.star, color: Colors.amber, size: 24),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 지번 주소
                    Text(
                      displayText,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    // 도로명 주소 (지번과 다른 경우)
                    if (roadAddress != null && roadAddress.isNotEmpty && roadAddress != displayText) ...[
                      const SizedBox(height: 2),
                      Text(
                        roadAddress,
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                    if (buildingName != null && buildingName.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        buildingName,
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[500],
                        ),
                      ),
                    ],
                    if (memo != null && memo.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Builder(
                        builder: (context) {
                          final isDark = Theme.of(context).brightness == Brightness.dark;
                          return Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: isDark ? Colors.grey[800] : Colors.grey[100],
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              memo,
                              style: TextStyle(
                                fontSize: 12,
                                color: isDark ? Colors.grey[400] : Colors.grey[600],
                              ),
                            ),
                          );
                        },
                      ),
                    ],
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.delete_outline, color: Colors.red),
                onPressed: () => _deleteLocalFavorite(id),
                constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                padding: EdgeInsets.zero,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _navigateToResultFromLocal(dynamic item) async {
    final pnu = item.pnu as String?;
    if (pnu == null || pnu.length < 19) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('유효하지 않은 즐겨찾기입니다')),
      );
      return;
    }

    // PNU에서 코드 추출
    final sigunguCd = pnu.substring(0, 5);
    final bjdongCd = pnu.substring(5, 10);
    final landType = pnu.substring(10, 11);
    final bun = pnu.substring(11, 15);
    final ji = pnu.substring(15, 19);

    // 지번 검색 수행
    await ref.read(buildingSearchProvider.notifier).searchByJibun(
          bjdongCode: sigunguCd + bjdongCd,
          bun: bun,
          ji: ji,
          landType: landType == '2' ? '2' : '1',
        );

    if (mounted) {
      context.push('/result');
    }
  }

  Future<void> _deleteLocalFavorite(String id) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('즐겨찾기 삭제'),
        content: const Text('이 즐겨찾기를 삭제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('삭제', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await ref.read(favoritesProvider.notifier).deleteFavorite(id);
    }
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
            icon: Icons.star,
            label: '즐겨찾기',
            isActive: true,
            activeColor: Colors.amber,
            onTap: () {},
          ),
          _buildNavItem(
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
    required IconData icon,
    required String label,
    required bool isActive,
    Color? activeColor,
    required VoidCallback onTap,
  }) {
    final color = isActive ? (activeColor ?? AppColors.primary) : Colors.grey[400];

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
}

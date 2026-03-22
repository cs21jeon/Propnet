import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:propedia/core/constants/app_colors.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';
import 'package:propedia/presentation/providers/history_provider.dart';
import 'package:propedia/presentation/providers/building_provider.dart';
import 'package:propedia/presentation/widgets/ads/banner_ad_widget.dart';
import 'package:propedia/presentation/widgets/common/app_footer.dart';

class HistoryScreen extends ConsumerStatefulWidget {
  const HistoryScreen({super.key});

  @override
  ConsumerState<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends ConsumerState<HistoryScreen> {
  @override
  void initState() {
    super.initState();
    // 화면 진입 시 데이터 로드
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      ref.read(historyProvider.notifier).loadLocalHistory();
      // 로그인 상태에서만 서버 동기화
      final authState = ref.read(authProvider);
      if (authState.status == AuthStatus.authenticated) {
        await ref.read(historyProvider.notifier).syncFromServer();
      }
    });
  }

  String _formatDate(String dateString) {
    try {
      final date = DateTime.parse(dateString);
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      final yesterday = today.subtract(const Duration(days: 1));
      final itemDate = DateTime(date.year, date.month, date.day);

      if (itemDate == today) {
        return '오늘';
      } else if (itemDate == yesterday) {
        return '어제';
      } else {
        return DateFormat('yyyy년 M월 d일').format(date);
      }
    } catch (_) {
      return dateString;
    }
  }

  String _formatTime(String isoString) {
    try {
      final date = DateTime.parse(isoString);
      return _formatTimeFromDateTime(date);
    } catch (_) {
      return '';
    }
  }

  String _formatTimeFromDateTime(DateTime date) {
    final hour = date.hour;
    final minute = date.minute.toString().padLeft(2, '0');
    final period = hour < 12 ? '오전' : '오후';
    final displayHour = hour % 12 == 0 ? 12 : hour % 12;
    return '$period $displayHour:$minute';
  }

  IconData _getSearchTypeIcon(String? type) {
    switch (type) {
      case 'road':
        return Icons.signpost_outlined;
      case 'jibun':
        return Icons.landscape_outlined;
      case 'map':
        return Icons.map_outlined;
      default:
        return Icons.search;
    }
  }

  String _getSearchTypeText(String? type) {
    switch (type) {
      case 'road':
        return '도로명';
      case 'jibun':
        return '지번';
      case 'map':
        return '지도';
      default:
        return '검색';
    }
  }

  Future<void> _navigateToResultFromLocal(dynamic item) async {
    final pnu = item.pnu as String?;
    if (pnu == null || pnu.length < 19) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('유효하지 않은 검색 기록입니다')),
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
          searchType: item.searchType ?? 'jibun',
        );

    if (mounted) {
      context.push('/result');
    }
  }

  Future<void> _deleteLocalHistory(String id) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('검색 기록 삭제'),
        content: const Text('이 검색 기록을 삭제하시겠습니까?'),
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
      await ref.read(historyProvider.notifier).deleteHistory(id);
    }
  }

  Future<void> _deleteAllHistory() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('전체 삭제'),
        content: const Text('모든 검색 기록을 삭제하시겠습니까?'),
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
      await ref.read(historyProvider.notifier).clearHistory();
      // 로컬 기록 다시 로드 (목록 갱신)
      ref.read(historyProvider.notifier).loadLocalHistory();
    }
  }

  @override
  Widget build(BuildContext context) {
    final historyState = ref.watch(historyProvider);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/home'),
        ),
        title: const Text(
          '검색 기록',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline, color: Colors.red),
            onPressed: historyState.localHistory.isEmpty ? null : _deleteAllHistory,
          ),
        ],
      ),
      body: _buildBody(historyState),
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

  Widget _buildBody(HistoryState state) {
    final authState = ref.watch(authProvider);
    final isGuest = authState.status == AuthStatus.guest;

    if (state.isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('검색 기록을 불러오는 중...'),
          ],
        ),
      );
    }

    // 로컬 기록 표시
    if (state.localHistory.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.history,
              size: 64,
              color: Colors.grey[300],
            ),
            const SizedBox(height: 16),
            Text(
              isGuest ? '로그인 후 검색기록 기능을\n사용할 수 있습니다' : '검색 기록이 없습니다',
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

    // 날짜별 그룹핑
    final groupedHistory = <String, List<dynamic>>{};
    for (final item in state.localHistory) {
      final dateKey = DateFormat('yyyy-MM-dd').format(item.searchedAt);
      groupedHistory.putIfAbsent(dateKey, () => []);
      groupedHistory[dateKey]!.add(item);
    }

    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(historyProvider.notifier).syncFromServer();
      },
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: groupedHistory.length,
        itemBuilder: (context, index) {
          final dateKey = groupedHistory.keys.elementAt(index);
          final items = groupedHistory[dateKey]!;

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
                child: Text(
                  _formatDate(dateKey),
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: Colors.grey[600],
                  ),
                ),
              ),
              ...items.map((item) => _buildLocalHistoryCard(item)),
              if (index < groupedHistory.length - 1) const SizedBox(height: 8),
            ],
          );
        },
      ),
    );
  }

  Widget _buildLocalHistoryCard(dynamic item) {
    final searchType = item.searchType as String?;
    final jibunAddress = item.jibunAddress as String?;
    final roadAddress = item.roadAddress as String?;
    final buildingName = item.buildingName as String?;
    final searchedAt = item.searchedAt as DateTime;
    final id = item.id as String;

    // 지번주소 우선 표시, 없으면 displayAddress 사용
    final displayText = jibunAddress ?? item.displayAddress ?? '';

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: () => _navigateToResultFromLocal(item),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          _getSearchTypeIcon(searchType),
                          size: 18,
                          color: AppColors.primary,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          _getSearchTypeText(searchType),
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                            color: AppColors.primary,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          _formatTimeFromDateTime(searchedAt),
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[400],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    // 지번 주소 표시
                    Text(
                      displayText,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    // 도로명 주소 표시 (지번과 다른 경우)
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
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.delete_outline, color: Colors.red),
                onPressed: () => _deleteLocalHistory(id),
              ),
            ],
          ),
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
            isActive: true,
            onTap: () {},
          ),
          _buildNavItem(
            icon: Icons.star_outline,
            label: '즐겨찾기',
            isActive: false,
            onTap: () => context.go('/favorites'),
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
}

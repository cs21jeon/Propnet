import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:propedia/presentation/widgets/common/app_drawer.dart';
import 'package:url_launcher/url_launcher.dart';

/// 금토끼부동산 홈 화면
class PropertyHomeScreen extends ConsumerWidget {
  const PropertyHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
            // 금토끼 아이콘 이미지 (좌측)
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.asset(
                'assets/images/goldenrabbit_icon.png',
                height: 44,
                width: 44,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: const Color(0xFFD4AF37).withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.home_work,
                    color: Color(0xFFD4AF37),
                    size: 26,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            // 텍스트 (중앙정렬)
            Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  '금토끼부동산',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFFD4AF37),
                  ),
                ),
                Text(
                  '매물정보',
                  style: TextStyle(
                    fontSize: 12,
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
      drawer: const AppDrawer(currentApp: AppType.property),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 안내 배너
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      const Color(0xFFD4AF37).withValues(alpha: 0.2),
                      const Color(0xFFD4AF37).withValues(alpha: 0.1),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: const Color(0xFFD4AF37).withValues(alpha: 0.3),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.info_outline,
                      color: Color(0xFFD4AF37),
                      size: 32,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            '금토끼부동산 매물 정보',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '수익형 부동산 전문',
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
              ),

              const SizedBox(height: 32),

              // 메뉴 섹션
              Text(
                '매물 조회',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 16),

              // 매물 지도
              _MenuCard(
                icon: Icons.map_outlined,
                title: '매물 지도',
                subtitle: '지도에서 매물 위치를 확인합니다',
                color: const Color(0xFFD4AF37),
                onTap: () => context.push('/property/map'),
              ),
              const SizedBox(height: 12),

              // 매물 검색
              _MenuCard(
                icon: Icons.search,
                title: '조건 검색',
                subtitle: '가격, 수익률, 면적 등 조건으로 검색합니다',
                color: const Color(0xFFD4AF37),
                onTap: () => context.push('/property/search'),
              ),

              const SizedBox(height: 32),

              // 카테고리 섹션
              Text(
                '카테고리별 매물',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 16),

              // 재건축용 토지
              _MenuCard(
                icon: Icons.landscape_outlined,
                title: '재건축용 토지',
                subtitle: '재건축 가능한 80평 이상 토지 매물',
                color: Colors.green,
                onTap: () => context.push('/property/list?category=reconstruction'),
              ),
              const SizedBox(height: 12),

              // 고수익률 건물
              _MenuCard(
                icon: Icons.trending_up,
                title: '고수익률 건물',
                subtitle: '6%이상 수익률 높은 건물 매물',
                color: Colors.blue,
                onTap: () => context.push('/property/list?category=highYield'),
              ),
              const SizedBox(height: 12),

              // 저가단독주택
              _MenuCard(
                icon: Icons.house_outlined,
                title: '저가단독주택',
                subtitle: '합리적 가격의 단독주택 매물',
                color: Colors.orange,
                onTap: () => context.push('/property/list?category=lowCost'),
              ),

              const SizedBox(height: 32),

              // 문의 섹션
              Text(
                '문의하기',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 16),

              _MenuCard(
                icon: Icons.contact_phone_outlined,
                title: '매물접수 및 상담신청',
                subtitle: '02-3471-7377',
                color: Colors.teal,
                onTap: () => _showContactDialog(context),
              ),

              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  void _showContactDialog(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    const phoneNumber = '02-3471-7377';
    const address = '서울시 동작구 사당동 272-26 남성역센트럴뷰 1층';

    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: Image.asset(
                'assets/images/goldenrabbit_icon.png',
                height: 32,
                width: 32,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const Icon(
                  Icons.home_work,
                  color: Color(0xFFD4AF37),
                  size: 32,
                ),
              ),
            ),
            const SizedBox(width: 10),
            const Text(
              '금토끼부동산중개',
              style: TextStyle(fontSize: 18),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildInfoRowCompact('대표', '전창성', isDark),
            const SizedBox(height: 8),
            // 전화번호 링크
            _buildInfoRowLink(
              '전화',
              phoneNumber,
              Icons.phone,
              isDark,
              () => _makePhoneCall(phoneNumber),
            ),
            const SizedBox(height: 8),
            // 주소 링크
            _buildInfoRowLink(
              '주소',
              address,
              Icons.map_outlined,
              isDark,
              () => _openNaverMap(address),
            ),
            const SizedBox(height: 14),
            Divider(color: isDark ? Colors.grey[700] : Colors.grey[300]),
            const SizedBox(height: 10),
            _buildInfoRowWide('사업자등록번호', '520-41-01170', isDark),
            const SizedBox(height: 5),
            _buildInfoRowWide('중개등록번호', '11590-2024-00048', isDark),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('닫기'),
          ),
        ],
      ),
    );
  }

  /// 전화 걸기
  Future<void> _makePhoneCall(String phoneNumber) async {
    final cleanNumber = phoneNumber.replaceAll('-', '');
    final uri = Uri.parse('tel:$cleanNumber');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  /// 네이버 지도 열기
  Future<void> _openNaverMap(String address) async {
    final encodedAddress = Uri.encodeComponent(address);
    final uri = Uri.parse('https://map.naver.com/p/search/$encodedAddress');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  /// 대표용 (좁은 라벨, 작은 내용 글씨)
  Widget _buildInfoRowCompact(String label, String value, bool isDark) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 45,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: isDark ? Colors.grey[400] : Colors.grey[600],
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: isDark ? Colors.white : Colors.black87,
            ),
          ),
        ),
      ],
    );
  }

  /// 전화, 주소용 (링크 스타일)
  Widget _buildInfoRowLink(
    String label,
    String value,
    IconData icon,
    bool isDark,
    VoidCallback onTap,
  ) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 45,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: isDark ? Colors.grey[400] : Colors.grey[600],
            ),
          ),
        ),
        Expanded(
          child: InkWell(
            onTap: onTap,
            child: Row(
              children: [
                Flexible(
                  child: Text(
                    value,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                      color: const Color(0xFFD4AF37),
                      decoration: TextDecoration.underline,
                      decorationColor: const Color(0xFFD4AF37),
                    ),
                  ),
                ),
                const SizedBox(width: 4),
                Icon(
                  icon,
                  size: 14,
                  color: const Color(0xFFD4AF37),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  /// 사업자등록번호용 (넓은 라벨)
  Widget _buildInfoRowWide(String label, String value, bool isDark) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 95,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: isDark ? Colors.grey[500] : Colors.grey[600],
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: isDark ? Colors.grey[300] : Colors.grey[700],
            ),
          ),
        ),
      ],
    );
  }
}

class _MenuCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  const _MenuCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
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
                  color: color.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  icon,
                  color: color,
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

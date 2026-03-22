import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';

/// 스켈레톤 로딩을 위한 기본 shimmer 박스
class ShimmerBox extends StatelessWidget {
  final double? width;
  final double height;
  final BorderRadius? borderRadius;

  const ShimmerBox({
    super.key,
    this.width,
    required this.height,
    this.borderRadius,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Shimmer.fromColors(
      baseColor: isDark ? Colors.grey[700]! : Colors.grey[300]!,
      highlightColor: isDark ? Colors.grey[600]! : Colors.grey[100]!,
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: borderRadius ?? BorderRadius.circular(4),
        ),
      ),
    );
  }
}

/// 결과 화면용 스켈레톤 UI
class ResultScreenSkeleton extends StatelessWidget {
  const ResultScreenSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 1. 기본 정보 카드 스켈레톤
          _buildCardSkeleton(
            context: context,
            icon: Icons.info_outline,
            title: '기본 정보',
            color: Colors.blue,
            rows: 3,
          ),

          const SizedBox(height: 16),

          // 2. 토지 정보 카드 스켈레톤
          _buildCardSkeleton(
            context: context,
            icon: Icons.landscape,
            title: '토지 정보',
            color: Colors.green,
            rows: 5,
          ),

          const SizedBox(height: 16),

          // 3. 건물 정보 카드 스켈레톤
          _buildCardSkeleton(
            context: context,
            icon: Icons.apartment,
            title: '건물 정보',
            color: Colors.orange,
            rows: 8,
          ),

          const SizedBox(height: 16),

          // 4. 지도 섹션 스켈레톤
          _buildMapSkeleton(context),
        ],
      ),
    );
  }

  Widget _buildCardSkeleton({
    required BuildContext context,
    required IconData icon,
    required String title,
    required Color color,
    required int rows,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 헤더 (실제 아이콘과 제목)
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(icon, color: color),
                ),
                const SizedBox(width: 12),
                Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ],
            ),
            const Divider(height: 24),

            // Shimmer 행들
            ...List.generate(
              rows,
              (index) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 라벨
                    Shimmer.fromColors(
                      baseColor: isDark ? Colors.grey[700]! : Colors.grey[300]!,
                      highlightColor:
                          isDark ? Colors.grey[600]! : Colors.grey[100]!,
                      child: Container(
                        width: 60 + (index % 3) * 20,
                        height: 12,
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                    ),
                    const SizedBox(height: 6),
                    // 값
                    Shimmer.fromColors(
                      baseColor: isDark ? Colors.grey[700]! : Colors.grey[300]!,
                      highlightColor:
                          isDark ? Colors.grey[600]! : Colors.grey[100]!,
                      child: Container(
                        width: double.infinity,
                        height: 16,
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMapSkeleton(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 헤더
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.teal.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.map, color: Colors.teal),
                ),
                const SizedBox(width: 12),
                const Text(
                  '위치',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ],
            ),
            const Divider(height: 24),

            // 지도 플레이스홀더
            Shimmer.fromColors(
              baseColor: isDark ? Colors.grey[700]! : Colors.grey[300]!,
              highlightColor: isDark ? Colors.grey[600]! : Colors.grey[100]!,
              child: Container(
                height: 200,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';

/// 간단한 Footer - 홈/검색 화면용
class AppFooterSimple extends StatelessWidget {
  const AppFooterSimple({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return SafeArea(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
        decoration: BoxDecoration(
          color: Theme.of(context).scaffoldBackgroundColor,
          border: Border(
            top: BorderSide(color: isDark ? Colors.grey[700]! : Colors.grey[200]!),
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Image.asset(
                  'assets/images/propnet_icon.png',
                  height: 13,
                  errorBuilder: (context, error, stackTrace) =>
                      Icon(Icons.language, size: 13, color: Colors.grey[400]),
                ),
                const SizedBox(width: 4),
                Text(
                  '프롭넷',
                  style: TextStyle(
                    fontSize: 10,
                    color: Colors.grey[500],
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  '|',
                  style: TextStyle(
                    fontSize: 10,
                    color: Colors.grey[400],
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  '부동산 종합 서비스',
                  style: TextStyle(
                    fontSize: 10,
                    color: Colors.grey[500],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              '© 2026 Propnet',
              style: TextStyle(
                fontSize: 9,
                color: Colors.grey[400],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 안내문구가 포함된 Footer - 결과 화면용 (현재 미사용)
class AppFooterWithDisclaimer extends StatelessWidget {
  const AppFooterWithDisclaimer({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return SafeArea(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
        decoration: BoxDecoration(
          color: isDark ? Colors.grey[900] : Colors.grey[50],
          border: Border(
            top: BorderSide(color: isDark ? Colors.grey[700]! : Colors.grey[200]!),
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 안내문구
            Text(
              '본 자료는 공공데이터포털 및 VWorld를 기반으로 생성되었습니다.\n오류가 있을 수 있으니 정확한 정보는 공적장부를 참고하세요.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 9,
                color: Colors.grey[500],
                height: 1.4,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Image.asset(
                  'assets/images/propnet_icon.png',
                  height: 13,
                  errorBuilder: (context, error, stackTrace) =>
                      Icon(Icons.language, size: 13, color: Colors.grey[400]),
                ),
                const SizedBox(width: 4),
                Text(
                  '프롭넷',
                  style: TextStyle(
                    fontSize: 10,
                    color: Colors.grey[500],
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  '|',
                  style: TextStyle(
                    fontSize: 10,
                    color: Colors.grey[400],
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  '부동산 종합 서비스',
                  style: TextStyle(
                    fontSize: 10,
                    color: Colors.grey[500],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              '© 2026 Propnet',
              style: TextStyle(
                fontSize: 9,
                color: Colors.grey[400],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

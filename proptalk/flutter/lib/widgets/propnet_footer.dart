import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';

/// 프롭넷 공통 푸터 위젯 (앱 버전 포함)
class PropnetFooter extends StatelessWidget {
  const PropnetFooter({super.key});

  static String _cachedVersion = '';

  /// 앱 버전을 미리 로드 (main.dart에서 호출)
  static Future<void> loadVersion() async {
    final info = await PackageInfo.fromPlatform();
    _cachedVersion = 'v${info.version}';
  }

  /// 현재 캐시된 버전 문자열
  static String get version => _cachedVersion;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Image.asset(
                'assets/images/Propnet_icon_transparent_full_size.png',
                height: 20,
                width: 20,
              ),
              const SizedBox(width: 6),
              Text(
                '프롭넷 | 부동산 종합 서비스',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.outline,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '\u00a9 2026 Propnet  $_cachedVersion',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.outline,
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }
}

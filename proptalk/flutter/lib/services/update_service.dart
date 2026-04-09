import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:package_info_plus/package_info_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import 'api_service.dart';

/// 인앱 업데이트 체크 서비스
class UpdateService {
  static const String _versionUrl = '${ApiService.baseUrl}/api/app-version';

  /// 앱 시작 시 호출: 서버에서 최신 버전을 조회하고 업데이트 필요 시 다이얼로그 표시
  static Future<void> checkForUpdate(BuildContext context) async {
    try {
      final packageInfo = await PackageInfo.fromPlatform();
      final currentVersionCode = int.tryParse(packageInfo.buildNumber) ?? 0;

      final response = await http.get(
        Uri.parse('$_versionUrl?version_code=$currentVersionCode'),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode != 200) return;

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final latestVersionCode = data['latest_version_code'] as int? ?? 0;
      final forceUpdate = data['force_update'] as bool? ?? false;
      final updateMessage = data['update_message'] as String? ?? '새로운 버전이 출시되었습니다.';
      final storeUrl = data['store_url'] as String? ?? '';
      final latestVersion = data['latest_version'] as String? ?? '';

      // 최신 버전이면 아무것도 하지 않음
      if (currentVersionCode >= latestVersionCode) return;

      // 다이얼로그 표시 전 context 유효성 확인
      if (!context.mounted) return;

      _showUpdateDialog(
        context,
        latestVersion: latestVersion,
        message: updateMessage,
        storeUrl: storeUrl,
        forceUpdate: forceUpdate,
      );
    } catch (e) {
      // 네트워크 오류 등은 조용히 무시 (업데이트 체크 실패가 앱 사용을 막으면 안 됨)
      debugPrint('[UpdateService] 버전 체크 실패: $e');
    }
  }

  /// 업데이트 안내 다이얼로그
  static void _showUpdateDialog(
    BuildContext context, {
    required String latestVersion,
    required String message,
    required String storeUrl,
    required bool forceUpdate,
  }) {
    showDialog(
      context: context,
      barrierDismissible: !forceUpdate,
      builder: (ctx) {
        final theme = Theme.of(ctx);
        return PopScope(
          canPop: !forceUpdate,
          child: AlertDialog(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            title: Row(
              children: [
                Icon(Icons.system_update, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                const Text('업데이트 알림'),
              ],
            ),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(message),
                const SizedBox(height: 12),
                Text(
                  '최신 버전: v$latestVersion',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
            actions: [
              if (!forceUpdate)
                TextButton(
                  onPressed: () => Navigator.of(ctx).pop(),
                  child: const Text('나중에'),
                ),
              FilledButton(
                onPressed: () => _openStore(storeUrl),
                child: const Text('업데이트'),
              ),
            ],
          ),
        );
      },
    );
  }

  /// Play Store 열기
  static Future<void> _openStore(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}

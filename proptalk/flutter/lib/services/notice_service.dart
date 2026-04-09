import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

/// 앱 공지사항 서비스
class NoticeService {
  static const String _noticesUrl = '${ApiService.baseUrl}/api/notices';

  /// 공지 조회 후 다이얼로그 표시
  static Future<void> checkAndShowNotice(BuildContext context) async {
    try {
      final response = await http.get(Uri.parse(_noticesUrl))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode != 200) return;

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final notices = (data['notices'] as List?) ?? [];
      if (notices.isEmpty) return;

      final prefs = await SharedPreferences.getInstance();

      for (final notice in notices) {
        final id = notice['id'];
        final dismissKey = 'notice_dismiss_$id';
        final dismissedDate = prefs.getString(dismissKey);

        // 오늘 이미 닫은 공지는 건너뛰기
        if (dismissedDate != null) {
          final today = DateTime.now().toIso8601String().substring(0, 10);
          if (dismissedDate == today) continue;
        }

        if (!context.mounted) return;

        _showNoticeDialog(
          context,
          id: id,
          title: notice['title'] ?? '',
          content: notice['content'] ?? '',
          noticeType: notice['notice_type'] ?? 'info',
          isDismissible: notice['is_dismissible'] ?? true,
        );
        break; // 한 번에 하나만 표시
      }
    } catch (e) {
      debugPrint('[NoticeService] 공지 조회 실패: $e');
    }
  }

  static void _showNoticeDialog(
    BuildContext context, {
    required int id,
    required String title,
    required String content,
    required String noticeType,
    required bool isDismissible,
  }) {
    final theme = Theme.of(context);
    final (icon, color) = switch (noticeType) {
      'error' => (Icons.error_outline, Colors.red),
      'maintenance' => (Icons.build_circle_outlined, Colors.orange),
      _ => (Icons.info_outline, theme.colorScheme.primary),
    };

    showDialog(
      context: context,
      barrierDismissible: isDismissible,
      builder: (ctx) => PopScope(
        canPop: isDismissible,
        child: AlertDialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          title: Row(
            children: [
              Icon(icon, color: color),
              const SizedBox(width: 8),
              Expanded(child: Text(title, style: const TextStyle(fontSize: 16))),
            ],
          ),
          content: Text(content),
          actions: [
            if (isDismissible)
              TextButton(
                onPressed: () async {
                  final prefs = await SharedPreferences.getInstance();
                  final today = DateTime.now().toIso8601String().substring(0, 10);
                  await prefs.setString('notice_dismiss_$id', today);
                  if (ctx.mounted) Navigator.of(ctx).pop();
                },
                child: const Text('오늘 하루 안보기'),
              ),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('확인'),
            ),
          ],
        ),
      ),
    );
  }
}

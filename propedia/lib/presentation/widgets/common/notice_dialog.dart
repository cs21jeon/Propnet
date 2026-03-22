import 'package:flutter/material.dart';
import 'package:propedia/core/constants/app_colors.dart';
import 'package:propedia/data/dto/notice_dto.dart';

/// 공지사항 팝업 다이얼로그
class NoticeDialog extends StatelessWidget {
  final NoticeDto notice;
  final VoidCallback onDismiss;
  final VoidCallback? onDismissForToday;

  const NoticeDialog({
    super.key,
    required this.notice,
    required this.onDismiss,
    this.onDismissForToday,
  });

  /// 다이얼로그 표시
  static Future<void> show(
    BuildContext context, {
    required NoticeDto notice,
    required VoidCallback onDismiss,
    VoidCallback? onDismissForToday,
  }) {
    return showDialog(
      context: context,
      barrierDismissible: notice.isDismissible,
      builder: (_) => NoticeDialog(
        notice: notice,
        onDismiss: onDismiss,
        onDismissForToday: onDismissForToday,
      ),
    );
  }

  IconData _getIcon() {
    switch (notice.noticeType) {
      case 'error':
        return Icons.error_outline;
      case 'maintenance':
        return Icons.build_outlined;
      default:
        return Icons.info_outline;
    }
  }

  Color _getColor() {
    switch (notice.noticeType) {
      case 'error':
        return AppColors.error;
      case 'maintenance':
        return AppColors.warning;
      default:
        return AppColors.primary;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getColor();
    final icon = _getIcon();

    return AlertDialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      title: Row(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              notice.title,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
      content: Text(
        notice.content,
        style: TextStyle(
          fontSize: 14,
          color: Colors.grey[700],
          height: 1.5,
        ),
      ),
      actions: [
        if (notice.isDismissible && onDismissForToday != null)
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              onDismissForToday!();
            },
            child: Text(
              '오늘 하루 안보기',
              style: TextStyle(color: Colors.grey[600]),
            ),
          ),
        ElevatedButton(
          onPressed: () {
            Navigator.pop(context);
            onDismiss();
          },
          style: ElevatedButton.styleFrom(
            backgroundColor: color,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          child: const Text('확인'),
        ),
      ],
    );
  }
}

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/billing_service.dart';
import '../theme/app_colors.dart';
import 'chat_screen.dart';

/// 외부 앱에서 공유받은 파일을 업로드할 채팅방을 선택하는 화면
class ShareRoomPickerScreen extends StatefulWidget {
  final List<File> sharedFiles;
  final bool isAudio;

  const ShareRoomPickerScreen({
    super.key,
    required this.sharedFiles,
    this.isAudio = true,
  });

  @override
  State<ShareRoomPickerScreen> createState() => _ShareRoomPickerScreenState();
}

class _ShareRoomPickerScreenState extends State<ShareRoomPickerScreen> {
  List<dynamic> _rooms = [];
  bool _isLoading = true;
  bool _isUploading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadRooms();
  }

  static IconData _iconForFile(String name) {
    final ext = name.split('.').last.toLowerCase();
    const audioExts = {'mp3', 'wav', 'ogg', 'm4a', 'flac', 'webm', 'mp4', 'aac', 'amr', '3gp'};
    const imageExts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'};
    if (audioExts.contains(ext)) return Icons.audio_file;
    if (imageExts.contains(ext)) return Icons.image;
    if (ext == 'pdf') return Icons.picture_as_pdf;
    return Icons.insert_drive_file;
  }

  Future<void> _loadRooms() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final api = context.read<ApiService>();
      _rooms = await api.getRooms();
    } catch (e) {
      _error = '채팅방 목록을 불러올 수 없습니다: $e';
    }
    if (mounted) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _uploadToRoom(Map<String, dynamic> room) async {
    final roomId = room['id'] as int;
    final roomName = room['name'] as String? ?? '채팅방';

    // context.read를 async gap 전에 미리 캡처
    final billing = context.read<BillingService>();
    final api = context.read<ApiService>();

    // 음성 파일인 경우만 잔여 시간 확인
    if (widget.isAudio) {
      await billing.loadBillingStatus();
      if (!billing.canTranscribe) {
        if (!mounted) return;
        await showDialog<void>(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('이용 시간 소진'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('음성 변환 이용 시간이 소진되었습니다.\n아래 주소에서 충전할 수 있습니다.'),
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Theme.of(ctx).colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: SelectableText(
                    BillingService.billingWebUrl,
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: Theme.of(ctx).colorScheme.primary,
                    ),
                  ),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('확인'),
              ),
            ],
          ),
        );
        return;
      }
    }

    setState(() => _isUploading = true);

    try {
      int successCount = 0;

      for (final file in widget.sharedFiles) {
        if (widget.isAudio) {
          await api.uploadAudio(roomId, file);
        } else {
          await api.uploadFile(roomId, file);
        }
        successCount++;
      }

      if (!mounted) return;

      // 업로드 완료 후 해당 채팅방으로 이동
      final snackText = widget.isAudio
          ? '$successCount개 파일 업로드 완료! 변환 중...'
          : '$successCount개 파일 업로드 완료!';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(snackText)),
      );

      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => ChatScreen(roomId: roomId, roomName: roomName),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _isUploading = false);

      String message = '업로드 실패: $e';
      if (e is ApiException && e.statusCode == 402) {
        message = e.message;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.extension<AppColors>()!;
    final fileNames = widget.sharedFiles
        .map((f) => f.path.split('/').last)
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('채팅방 선택'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: Column(
        children: [
          // 공유된 파일 정보
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            color: colors.cardSurface,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '공유된 파일 (${widget.sharedFiles.length}개)',
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                ...fileNames.map((name) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Row(
                    children: [
                      Icon(_iconForFile(name), size: 18,
                          color: theme.colorScheme.primary),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          name,
                          style: theme.textTheme.bodySmall,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                )),
              ],
            ),
          ),
          const Divider(height: 1),

          // 업로드 진행 중 표시
          if (_isUploading)
            Container(
              padding: const EdgeInsets.all(16),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  SizedBox(width: 12),
                  Text('업로드 중...'),
                ],
              ),
            ),

          // 방 선택 안내
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Text(
              '업로드할 채팅방을 선택하세요',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ),

          // 채팅방 목록
          Expanded(
            child: _buildRoomList(theme, colors),
          ),
        ],
      ),
    );
  }

  Widget _buildRoomList(ThemeData theme, AppColors colors) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!, style: TextStyle(color: colors.danger)),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _loadRooms,
              icon: const Icon(Icons.refresh),
              label: const Text('다시 시도'),
            ),
          ],
        ),
      );
    }

    if (_rooms.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.chat_bubble_outline, size: 48,
                color: theme.colorScheme.onSurfaceVariant),
            const SizedBox(height: 16),
            Text(
              '참여 중인 채팅방이 없습니다',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadRooms,
      child: ListView.separated(
        itemCount: _rooms.length,
        separatorBuilder: (_, __) => const Divider(height: 1, indent: 72),
        itemBuilder: (context, index) {
          final room = _rooms[index];
          final name = room['name'] ?? '채팅방';
          final memberCount = room['member_count'] ?? 0;

          return ListTile(
            enabled: !_isUploading,
            leading: CircleAvatar(
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Icon(Icons.chat,
                  color: theme.colorScheme.onPrimaryContainer),
            ),
            title: Text(
              name,
              style: theme.textTheme.bodyLarge?.copyWith(
                fontWeight: FontWeight.w500,
              ),
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Text('$memberCount명 참여'),
            trailing: Icon(Icons.upload,
                color: theme.colorScheme.primary),
            onTap: () => _confirmAndUpload(room),
          );
        },
      ),
    );
  }

  Future<void> _confirmAndUpload(Map<String, dynamic> room) async {
    final roomName = room['name'] ?? '채팅방';
    final fileCount = widget.sharedFiles.length;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('파일 업로드'),
        content: Text(
          '"$roomName"에 $fileCount개 파일을 업로드할까요?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('업로드'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _uploadToRoom(room);
    }
  }
}

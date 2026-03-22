import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../theme/app_colors.dart';
import 'chat_screen.dart';
import 'settings_screen.dart';
import '../widgets/ad_banner_widget.dart';
import '../widgets/propnet_footer.dart';

class RoomsScreen extends StatefulWidget {
  const RoomsScreen({super.key});

  @override
  State<RoomsScreen> createState() => _RoomsScreenState();
}

class _RoomsScreenState extends State<RoomsScreen> {
  List<dynamic> _rooms = [];
  bool _isLoading = true;
  String _sortBy = 'recent'; // recent, name, members
  bool _sortAsc = false; // false=내림차순, true=오름차순
  
  @override
  void initState() {
    super.initState();
    _loadRooms();
  }
  
  Future<void> _loadRooms() async {
    setState(() => _isLoading = true);
    try {
      final api = context.read<ApiService>();
      _rooms = await api.getRooms();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('목록 로딩 실패: $e')),
        );
      }
    }
    if (mounted) {
      _sortRooms();
      setState(() => _isLoading = false);
    }
  }

  void _sortRooms() {
    _rooms.sort((a, b) {
      // 즐겨찾기 항상 우선
      final aFav = a['is_favorite'] == true ? 0 : 1;
      final bFav = b['is_favorite'] == true ? 0 : 1;
      if (aFav != bFav) return aFav.compareTo(bFav);

      int result;
      switch (_sortBy) {
        case 'name':
          result = (a['name'] ?? '').toString().compareTo((b['name'] ?? '').toString());
          break;
        case 'members':
          result = (a['member_count'] ?? 0).compareTo(b['member_count'] ?? 0);
          break;
        default: // recent - 생성순
          final aDate = (a['created_at'] ?? '').toString();
          final bDate = (b['created_at'] ?? '').toString();
          result = aDate.compareTo(bDate);
          break;
      }
      return _sortAsc ? result : -result;
    });
  }
  
  void _showCreateRoomDialog() {
    final nameController = TextEditingController();
    final descController = TextEditingController();
    bool enableDrive = true;
    bool enableSheets = true;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
        title: const Text('새 채팅방 만들기'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                decoration: const InputDecoration(
                  labelText: '채팅방 이름',
                  hintText: '예: 부동산 상담방',
                  border: OutlineInputBorder(),
                ),
                autofocus: true,
              ),
              const SizedBox(height: 12),
              TextField(
                controller: descController,
                decoration: const InputDecoration(
                  labelText: '설명 (선택)',
                  border: OutlineInputBorder(),
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 8),
              SwitchListTile(
                title: const Text('Drive 자동 저장', style: TextStyle(fontSize: 14)),
                subtitle: const Text('음성파일을 Google Drive에 백업', style: TextStyle(fontSize: 12)),
                value: enableDrive,
                dense: true,
                contentPadding: EdgeInsets.zero,
                onChanged: (v) => setDialogState(() => enableDrive = v),
              ),
              SwitchListTile(
                title: const Text('시트 기록', style: TextStyle(fontSize: 14)),
                subtitle: const Text('변환 결과를 Google Sheets에 기록', style: TextStyle(fontSize: 12)),
                value: enableSheets,
                dense: true,
                contentPadding: EdgeInsets.zero,
                onChanged: (v) => setDialogState(() => enableSheets = v),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () async {
              if (nameController.text.trim().isEmpty) return;
              Navigator.pop(ctx);

              try {
                final api = context.read<ApiService>();
                final result = await api.createRoom(
                  nameController.text.trim(),
                  description: descController.text.trim(),
                  enableDriveBackup: enableDrive,
                  enableSheetsLogging: enableSheets,
                );
                
                final inviteCode = result['invite_code'];
                if (mounted) {
                  // 초대코드 복사 다이얼로그로 표시
                  Clipboard.setData(ClipboardData(text: inviteCode));
                  if (mounted) {
                    showDialog(
                      context: context,
                      builder: (ctx) => AlertDialog(
                        title: const Text('채팅방 생성 완료'),
                        content: Column(
                          mainAxisSize: MainAxisSize.min,
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('초대코드가 클립보드에 복사되었습니다.'),
                            const SizedBox(height: 12),
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: SelectableText(
                                inviteCode,
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 18,
                                  letterSpacing: 1.5,
                                ),
                              ),
                            ),
                          ],
                        ),
                        actions: [
                          FilledButton(
                            onPressed: () => Navigator.pop(ctx),
                            child: const Text('확인'),
                          ),
                        ],
                      ),
                    );
                  }
                }
                _loadRooms();
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('생성 실패: $e')),
                  );
                }
              }
            },
            child: const Text('만들기'),
          ),
        ],
      ),
      ),
    );
  }
  
  void _showJoinRoomDialog() {
    final codeController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('채팅방 참여'),
        content: TextField(
          controller: codeController,
          decoration: const InputDecoration(
            labelText: '초대 코드',
            hintText: 'ABC12345',
            border: OutlineInputBorder(),
          ),
          textCapitalization: TextCapitalization.characters,
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () async {
              if (codeController.text.trim().isEmpty) return;
              Navigator.pop(ctx);

              try {
                final api = context.read<ApiService>();
                final result = await api.joinRoom(codeController.text.trim());
                if (mounted) {
                  final status = result['status'] ?? 'active';
                  if (status == 'pending') {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('참여 신청 완료! 방장의 승인을 기다려 주세요.'),
                        duration: Duration(seconds: 4),
                      ),
                    );
                  } else {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(result['message'] ?? '채팅방에 참여했습니다!')),
                    );
                  }
                }
                _loadRooms();
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('참여 실패: $e')),
                  );
                }
              }
            },
            child: const Text('참여'),
          ),
        ],
      ),
    );
  }
  
  void _showActionSheet() {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text('채팅방',
                  style: Theme.of(context).textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.bold)),
            ),
            ListTile(
              leading: Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.add, color: Theme.of(context).colorScheme.primary),
              ),
              title: const Text('새 톡방 만들기'),
              subtitle: const Text('새로운 채팅방을 만듭니다'),
              onTap: () {
                Navigator.pop(ctx);
                _showCreateRoomDialog();
              },
            ),
            ListTile(
              leading: Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.secondaryContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.login, color: Theme.of(context).colorScheme.secondary),
              ),
              title: const Text('초대코드로 참여'),
              subtitle: const Text('기존 채팅방에 참여합니다'),
              onTap: () {
                Navigator.pop(ctx);
                _showJoinRoomDialog();
              },
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final user = auth.currentUser;
    final theme = Theme.of(context);
    final appColors = theme.extension<AppColors>()!;

    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 72,
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset(
              'assets/images/Proptalk_transparent icon_half size.png',
              height: 44,
              width: 44,
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('Proptalk',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20)),
                Text('세상 쉬운 업무 공유',
                  style: TextStyle(
                    fontSize: 12,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.sort),
            tooltip: '정렬',
            onSelected: (value) {
              setState(() {
                if (value == 'toggle_order') {
                  _sortAsc = !_sortAsc;
                } else {
                  _sortBy = value;
                }
                _sortRooms();
              });
            },
            itemBuilder: (ctx) => [
              PopupMenuItem(
                value: 'recent',
                child: Row(
                  children: [
                    Icon(_sortBy == 'recent' ? Icons.check : Icons.access_time, size: 20),
                    const SizedBox(width: 8),
                    const Text('생성순'),
                  ],
                ),
              ),
              PopupMenuItem(
                value: 'name',
                child: Row(
                  children: [
                    Icon(_sortBy == 'name' ? Icons.check : Icons.sort_by_alpha, size: 20),
                    const SizedBox(width: 8),
                    const Text('이름순'),
                  ],
                ),
              ),
              PopupMenuItem(
                value: 'members',
                child: Row(
                  children: [
                    Icon(_sortBy == 'members' ? Icons.check : Icons.people, size: 20),
                    const SizedBox(width: 8),
                    const Text('참여인원순'),
                  ],
                ),
              ),
              const PopupMenuDivider(),
              PopupMenuItem(
                value: 'toggle_order',
                child: Row(
                  children: [
                    Icon(_sortAsc ? Icons.arrow_upward : Icons.arrow_downward, size: 20),
                    const SizedBox(width: 8),
                    Text(_sortAsc ? '오름차순' : '내림차순'),
                  ],
                ),
              ),
            ],
          ),
          if (user != null)
            GestureDetector(
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const SettingsScreen()),
                );
              },
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                child: CircleAvatar(
                  radius: 16,
                  backgroundImage: user['avatar_url'] != null
                    ? NetworkImage(user['avatar_url'])
                    : null,
                  child: user['avatar_url'] == null
                    ? Text(user['name']?[0] ?? '?') : null,
                ),
              ),
            ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _isLoading
              ? const Center(child: CircularProgressIndicator())
              : _rooms.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 32),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 100,
                            height: 100,
                            decoration: BoxDecoration(
                              color: theme.colorScheme.primaryContainer.withValues(alpha: 0.3),
                              shape: BoxShape.circle,
                            ),
                            child: Icon(Icons.chat_bubble_outline, size: 48,
                                color: theme.colorScheme.primary.withValues(alpha: 0.6)),
                          ),
                          const SizedBox(height: 24),
                          Text('아직 채팅방이 없어요',
                              style: theme.textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w600,
                              )),
                          const SizedBox(height: 8),
                          Text('새 채팅방을 만들거나\n초대코드로 참여해 보세요',
                            textAlign: TextAlign.center,
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.colorScheme.outline,
                              height: 1.5,
                            ),
                          ),
                          const SizedBox(height: 24),
                          FilledButton.icon(
                            onPressed: () => _showActionSheet(),
                            icon: const Icon(Icons.add),
                            label: const Text('시작하기'),
                          ),
                        ],
                      ),
                    ),
                  )
                : RefreshIndicator(
                    onRefresh: _loadRooms,
                    child: ListView.builder(
                padding: EdgeInsets.only(
                  top: 8,
                  bottom: MediaQuery.of(context).padding.bottom + 8,
                ),
                itemCount: _rooms.length,
                itemBuilder: (ctx, i) {
                  final room = _rooms[i];
                  final myStatus = room['my_status'] ?? 'active';
                  final isPending = myStatus == 'pending';
                  final pendingCount = room['pending_count'] ?? 0;

                  return Card(
                    margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: isPending
                            ? appColors.warningContainer
                            : theme.colorScheme.primaryContainer,
                        child: Icon(
                          isPending ? Icons.hourglass_top : Icons.group,
                          color: isPending ? appColors.warning : theme.colorScheme.primary,
                        ),
                      ),
                      title: Text(room['name'] ?? '',
                        style: const TextStyle(fontWeight: FontWeight.w600)),
                      subtitle: Text(
                        isPending
                            ? '승인 대기 중'
                            : room['last_message'] ?? room['description'] ?? '',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: isPending
                            ? TextStyle(color: appColors.onWarningContainer, fontStyle: FontStyle.italic)
                            : null,
                      ),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (!isPending)
                            GestureDetector(
                              onTap: () async {
                                try {
                                  final api = context.read<ApiService>();
                                  await api.toggleFavorite(room['id']);
                                  _loadRooms();
                                } catch (_) {}
                              },
                              child: Icon(
                                room['is_favorite'] == true ? Icons.star : Icons.star_border,
                                color: room['is_favorite'] == true ? appColors.warning : theme.colorScheme.outline,
                                size: 20,
                              ),
                            ),
                          const SizedBox(width: 8),
                          Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              if (!isPending)
                                Text('${room['member_count'] ?? 0}명',
                                  style: theme.textTheme.bodySmall),
                              if (room['role'] == 'admin') ...[
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                  decoration: BoxDecoration(
                                    color: theme.colorScheme.primary.withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Text('관리자',
                                    style: TextStyle(fontSize: 10, color: theme.colorScheme.primary)),
                                ),
                                if (pendingCount > 0)
                                  Container(
                                    margin: const EdgeInsets.only(top: 4),
                                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                    decoration: BoxDecoration(
                                      color: appColors.warning,
                                      borderRadius: BorderRadius.circular(10),
                                    ),
                                    child: Text('$pendingCount',
                                      style: TextStyle(fontSize: 10, color: appColors.onWarning, fontWeight: FontWeight.bold)),
                                  ),
                              ],
                            ],
                          ),
                        ],
                      ),
                      onTap: () {
                        if (isPending) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('방장의 승인을 기다리고 있습니다.')),
                          );
                          return;
                        }
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => ChatScreen(
                              roomId: room['id'],
                              roomName: room['name'] ?? '',
                            ),
                          ),
                        ).then((_) => _loadRooms());
                      },
                    ),
                  );
                },
                    ),
                  ),
          ),
          const AdBannerWidget(),
          Padding(
            padding: EdgeInsets.only(
              top: 8,
              bottom: 8 + MediaQuery.of(context).padding.bottom,
            ),
            child: const PropnetFooter(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showActionSheet(),
        child: const Icon(Icons.add),
      ),
    );
  }
}

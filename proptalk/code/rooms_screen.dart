import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import 'chat_screen.dart';

class RoomsScreen extends StatefulWidget {
  const RoomsScreen({super.key});

  @override
  State<RoomsScreen> createState() => _RoomsScreenState();
}

class _RoomsScreenState extends State<RoomsScreen> {
  List<dynamic> _rooms = [];
  bool _isLoading = true;
  
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
    if (mounted) setState(() => _isLoading = false);
  }
  
  void _showCreateRoomDialog() {
    final nameController = TextEditingController();
    final descController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('새 채팅방 만들기'),
        content: Column(
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
          ],
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
                );
                
                final inviteCode = result['invite_code'];
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('채팅방 생성! 초대코드: $inviteCode'),
                      action: SnackBarAction(
                        label: '복사',
                        onPressed: () {
                          Clipboard.setData(ClipboardData(text: inviteCode));
                        },
                      ),
                    ),
                  );
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
                await api.joinRoom(codeController.text.trim());
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('채팅방에 참여했습니다!')),
                  );
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
  
  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final user = auth.currentUser;
    final theme = Theme.of(context);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('VoiceRoom'),
        actions: [
          if (user != null)
            PopupMenuButton(
              icon: CircleAvatar(
                radius: 16,
                backgroundImage: user['avatar_url'] != null
                  ? NetworkImage(user['avatar_url'])
                  : null,
                child: user['avatar_url'] == null 
                  ? Text(user['name']?[0] ?? '?') : null,
              ),
              itemBuilder: (ctx) => [
                PopupMenuItem(
                  child: Text(user['name'] ?? ''),
                  enabled: false,
                ),
                PopupMenuItem(
                  child: Text(user['email'] ?? '', style: const TextStyle(fontSize: 12)),
                  enabled: false,
                ),
                const PopupMenuDivider(),
                PopupMenuItem(
                  onTap: () => auth.signOut(),
                  child: const Row(
                    children: [
                      Icon(Icons.logout, size: 20),
                      SizedBox(width: 8),
                      Text('로그아웃'),
                    ],
                  ),
                ),
              ],
            ),
        ],
      ),
      body: _isLoading
        ? const Center(child: CircularProgressIndicator())
        : _rooms.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.chat_bubble_outline, size: 80, color: theme.colorScheme.outline),
                  const SizedBox(height: 16),
                  Text('아직 채팅방이 없어요', style: theme.textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Text('새 채팅방을 만들거나 초대코드로 참여하세요',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.outline,
                    ),
                  ),
                ],
              ),
            )
          : RefreshIndicator(
              onRefresh: _loadRooms,
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(vertical: 8),
                itemCount: _rooms.length,
                itemBuilder: (ctx, i) {
                  final room = _rooms[i];
                  return Card(
                    margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: theme.colorScheme.primaryContainer,
                        child: Icon(Icons.group, color: theme.colorScheme.primary),
                      ),
                      title: Text(room['name'] ?? '', 
                        style: const TextStyle(fontWeight: FontWeight.w600)),
                      subtitle: Text(
                        room['last_message'] ?? room['description'] ?? '',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text('${room['member_count'] ?? 0}명',
                            style: theme.textTheme.bodySmall),
                          if (room['role'] == 'admin')
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                              decoration: BoxDecoration(
                                color: theme.colorScheme.primary.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text('관리자', 
                                style: TextStyle(fontSize: 10, color: theme.colorScheme.primary)),
                            ),
                        ],
                      ),
                      onTap: () {
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
      floatingActionButton: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          FloatingActionButton.small(
            heroTag: 'join',
            onPressed: _showJoinRoomDialog,
            tooltip: '초대코드로 참여',
            child: const Icon(Icons.login),
          ),
          const SizedBox(height: 8),
          FloatingActionButton(
            heroTag: 'create',
            onPressed: _showCreateRoomDialog,
            tooltip: '새 채팅방',
            child: const Icon(Icons.add),
          ),
        ],
      ),
    );
  }
}

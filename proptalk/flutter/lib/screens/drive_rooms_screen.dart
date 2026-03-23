import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';

class DriveRoomsScreen extends StatefulWidget {
  const DriveRoomsScreen({super.key});

  @override
  State<DriveRoomsScreen> createState() => _DriveRoomsScreenState();
}

class _DriveRoomsScreenState extends State<DriveRoomsScreen> {
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

  Future<void> _openDriveFolder(int roomId, String roomName) async {
    try {
      final api = context.read<ApiService>();
      final result = await api.getRoomDriveFolder(roomId);
      final url = Uri.parse(result['drive_folder_url']);
      if (await canLaunchUrl(url)) {
        await launchUrl(url, mode: LaunchMode.externalApplication);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$roomName: Drive 폴더가 없습니다')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('음성파일 원본'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _rooms.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.folder_off_outlined,
                          size: 64,
                          color: theme.colorScheme.onSurfaceVariant
                              .withOpacity(0.4)),
                      const SizedBox(height: 16),
                      Text('참여 중인 채팅방이 없습니다',
                          style: theme.textTheme.bodyLarge?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          )),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadRooms,
                  child: ListView.builder(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    itemCount: _rooms.length,
                    itemBuilder: (context, index) {
                      final room = _rooms[index];
                      final hasDrive = room['drive_folder_id'] != null;

                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12)),
                        child: ListTile(
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12)),
                          leading: CircleAvatar(
                            backgroundColor: hasDrive
                                ? theme.colorScheme.primaryContainer
                                : theme.colorScheme.surfaceContainerHighest,
                            child: Icon(
                              hasDrive ? Icons.folder : Icons.folder_off,
                              color: hasDrive
                                  ? theme.colorScheme.primary
                                  : theme.colorScheme.onSurfaceVariant,
                            ),
                          ),
                          title: Text(room['name'] ?? ''),
                          subtitle: Text(
                            hasDrive ? 'Drive 연동됨' : 'Drive 미설정',
                            style: TextStyle(
                              color: hasDrive
                                  ? theme.colorScheme.primary
                                  : theme.colorScheme.onSurfaceVariant,
                              fontSize: 12,
                            ),
                          ),
                          trailing: hasDrive
                              ? const Icon(Icons.open_in_new, size: 20)
                              : null,
                          onTap: () => _openDriveFolder(
                              room['id'], room['name'] ?? ''),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}

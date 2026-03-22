import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

class ChatScreen extends StatefulWidget {
  final int roomId;
  final String roomName;

  const ChatScreen({
    super.key,
    required this.roomId,
    required this.roomName,
  });

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final AudioRecorder _recorder = AudioRecorder();

  List<dynamic> _messages = [];
  bool _isLoading = true;
  bool _isSending = false;
  bool _isRecording = false;
  bool _isUploadingAudio = false;
  String? _typingUser;

  StreamSubscription? _messageSub;
  StreamSubscription? _audioStatusSub;
  StreamSubscription? _typingSub;

  @override
  void initState() {
    super.initState();
    _loadMessages();
    _setupWebSocket();
  }

  @override
  void dispose() {
    _messageSub?.cancel();
    _audioStatusSub?.cancel();
    _typingSub?.cancel();
    _textController.dispose();
    _scrollController.dispose();
    _recorder.dispose();

    final auth = context.read<AuthService>();
    auth.socket.leaveRoom(widget.roomId);
    super.dispose();
  }

  // ============================================================
  // WebSocket 설정
  // ============================================================
  void _setupWebSocket() {
    final auth = context.read<AuthService>();
    final socket = auth.socket;

    socket.joinRoom(widget.roomId);

    // 새 메시지 수신
    _messageSub = socket.onMessage.listen((msg) {
      if (!mounted) return;
      setState(() {
        if (msg['parent_id'] != null) {
          // 댓글 → 부모 메시지에 replies로 추가
          final parentIdx =
              _messages.indexWhere((m) => m['id'] == msg['parent_id']);
          if (parentIdx >= 0) {
            final parent = Map<String, dynamic>.from(_messages[parentIdx]);
            final replies = List.from(parent['replies'] ?? []);
            replies.add(msg);
            parent['replies'] = replies;
            _messages[parentIdx] = parent;
          }
        } else {
          _messages.insert(0, msg);
        }
      });
      _scrollToBottom();
    });

    // 음성 변환 상태
    _audioStatusSub = socket.onAudioStatus.listen((data) {
      if (!mounted) return;
      setState(() {
        final idx =
            _messages.indexWhere((m) => m['id'] == data['message_id']);
        if (idx >= 0) {
          _messages[idx] = {
            ..._messages[idx],
            'audio_status': data['status'],
          };
        }
      });
    });

    // 타이핑 표시
    _typingSub = socket.onTyping.listen((data) {
      if (!mounted) return;
      setState(
          () => _typingUser = data['is_typing'] ? data['user_name'] : null);
      if (data['is_typing'] == true) {
        Future.delayed(const Duration(seconds: 3), () {
          if (mounted) setState(() => _typingUser = null);
        });
      }
    });
  }

  // ============================================================
  // 메시지 로드
  // ============================================================
  Future<void> _loadMessages() async {
    setState(() => _isLoading = true);
    try {
      final api = context.read<ApiService>();
      _messages = await api.getMessages(widget.roomId);
    } catch (e) {
      _showError('메시지 로딩 실패: $e');
    }
    if (mounted) setState(() => _isLoading = false);
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      Future.delayed(const Duration(milliseconds: 100), () {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(0,
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeOut);
        }
      });
    }
  }

  void _showError(String msg) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
    }
  }

  // ============================================================
  // 텍스트 메시지 전송
  // ============================================================
  Future<void> _sendTextMessage() async {
    final text = _textController.text.trim();
    if (text.isEmpty || _isSending) return;

    _textController.clear();
    setState(() => _isSending = true);

    try {
      final api = context.read<ApiService>();
      await api.sendMessage(widget.roomId, text);
    } catch (e) {
      _textController.text = text;
      _showError('전송 실패: $e');
    }
    if (mounted) setState(() => _isSending = false);
  }

  // ============================================================
  // 음성 파일 선택 업로드
  // ============================================================
  Future<void> _pickAndUploadAudio() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: [
        'mp3', 'wav', 'ogg', 'm4a', 'flac', 'webm', 'mp4', 'aac'
      ],
    );
    if (result == null || result.files.single.path == null) return;
    await _uploadAudio(File(result.files.single.path!));
  }

  Future<void> _uploadAudio(File file) async {
    setState(() => _isUploadingAudio = true);
    try {
      final api = context.read<ApiService>();
      await api.uploadAudio(widget.roomId, file);
      _showError('음성 파일 업로드 완료! 변환 중...');
    } catch (e) {
      _showError('업로드 실패: $e');
    }
    if (mounted) setState(() => _isUploadingAudio = false);
  }

  // ============================================================
  // 녹음
  // ============================================================
  Future<void> _toggleRecording() async {
    if (_isRecording) {
      final path = await _recorder.stop();
      setState(() => _isRecording = false);
      if (path != null) await _uploadAudio(File(path));
    } else {
      if (!await _recorder.hasPermission()) {
        _showError('마이크 권한이 필요합니다');
        return;
      }
      final dir = await getTemporaryDirectory();
      final filePath =
          '${dir.path}/rec_${DateTime.now().millisecondsSinceEpoch}.m4a';
      await _recorder.start(
        const RecordConfig(encoder: AudioEncoder.aacLc),
        path: filePath,
      );
      setState(() => _isRecording = true);
    }
  }

  // ============================================================
  // 첨부 메뉴
  // ============================================================
  void _showAttachMenu() {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.audio_file, color: Colors.blue),
              title: const Text('음성 파일 선택'),
              subtitle: const Text('mp3, wav, m4a, ogg 등'),
              onTap: () {
                Navigator.pop(ctx);
                _pickAndUploadAudio();
              },
            ),
            ListTile(
              leading: Icon(
                _isRecording ? Icons.stop_circle : Icons.mic,
                color: _isRecording ? Colors.red : Colors.green,
              ),
              title: Text(_isRecording ? '녹음 중지' : '녹음 시작'),
              subtitle: const Text('직접 녹음하여 업로드'),
              onTap: () {
                Navigator.pop(ctx);
                _toggleRecording();
              },
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // 채팅방 정보 / 검색
  // ============================================================
  void _showRoomInfo() async {
    try {
      final api = context.read<ApiService>();
      final data = await api.getRoom(widget.roomId);
      final room = data['room'];
      final members = data['members'] as List? ?? [];
      final inviteCode = room['invite_code'] ?? '';

      if (!mounted) return;
      showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        builder: (ctx) => DraggableScrollableSheet(
          initialChildSize: 0.5,
          minChildSize: 0.3,
          maxChildSize: 0.8,
          expand: false,
          builder: (_, scrollCtrl) => Padding(
            padding: const EdgeInsets.all(20),
            child: ListView(
              controller: scrollCtrl,
              children: [
                Text(room['name'] ?? '',
                    style: Theme.of(context).textTheme.headlineSmall),
                if (room['description']?.isNotEmpty ?? false) ...[
                  const SizedBox(height: 8),
                  Text(room['description']),
                ],
                const SizedBox(height: 16),
                // 초대코드
                Card(
                  child: ListTile(
                    title: const Text('초대 코드'),
                    subtitle: Text(inviteCode,
                        style: const TextStyle(
                            fontSize: 20, fontWeight: FontWeight.bold,
                            letterSpacing: 2)),
                    trailing: IconButton(
                      icon: const Icon(Icons.copy),
                      onPressed: () {
                        Clipboard.setData(ClipboardData(text: inviteCode));
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('초대코드 복사됨!')),
                        );
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Text('멤버 (${members.length}명)',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                ...members.map((m) => ListTile(
                      leading: CircleAvatar(
                        backgroundImage: m['avatar_url'] != null
                            ? NetworkImage(m['avatar_url'])
                            : null,
                        child: m['avatar_url'] == null
                            ? Text(m['name']?[0] ?? '?')
                            : null,
                      ),
                      title: Text(m['name'] ?? ''),
                      subtitle: Text(m['email'] ?? ''),
                      trailing: m['role'] == 'admin'
                          ? const Chip(label: Text('관리자'))
                          : null,
                    )),
              ],
            ),
          ),
        ),
      );
    } catch (e) {
      _showError('정보 로딩 실패: $e');
    }
  }

  // ============================================================
  // 메시지 위젯 빌더
  // ============================================================
  Widget _buildMessageItem(Map<String, dynamic> msg) {
    final auth = context.read<AuthService>();
    final isMe = msg['user_id'] == auth.currentUser?['id'];
    final type = msg['type'] ?? 'text';
    final theme = Theme.of(context);

    // 시스템 메시지
    if (type == 'system') {
      return Center(
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 4),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest.withOpacity(0.5),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(msg['content'] ?? '',
              style: theme.textTheme.bodySmall
                  ?.copyWith(color: theme.colorScheme.outline)),
        ),
      );
    }

    final replies = msg['replies'] as List? ?? [];

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: Column(
        crossAxisAlignment:
            isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          // 사용자 이름
          if (!isMe)
            Padding(
              padding: const EdgeInsets.only(left: 4, bottom: 2),
              child: Text(msg['user_name'] ?? '',
                  style: theme.textTheme.bodySmall
                      ?.copyWith(fontWeight: FontWeight.w600)),
            ),

          // 메시지 버블
          Container(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.75,
            ),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: isMe
                  ? theme.colorScheme.primary
                  : theme.colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(16),
                topRight: const Radius.circular(16),
                bottomLeft: Radius.circular(isMe ? 16 : 4),
                bottomRight: Radius.circular(isMe ? 4 : 16),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 음성 메시지 아이콘
                if (type == 'audio') ...[
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.mic,
                          size: 18,
                          color:
                              isMe ? Colors.white70 : theme.colorScheme.primary),
                      const SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          msg['content'] ?? '',
                          style: TextStyle(
                            color: isMe ? Colors.white : null,
                          ),
                        ),
                      ),
                    ],
                  ),
                  // 변환 상태 표시
                  if (msg['audio_status'] == 'transcribing')
                    Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          SizedBox(
                            width: 14, height: 14,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: isMe ? Colors.white70 : theme.colorScheme.primary,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text('텍스트 변환 중...',
                              style: TextStyle(
                                fontSize: 12,
                                color: isMe ? Colors.white60 : theme.colorScheme.outline,
                              )),
                        ],
                      ),
                    ),
                ] else ...[
                  // 일반 텍스트 또는 변환 결과
                  Text(
                    msg['content'] ?? '',
                    style: TextStyle(
                      color: isMe ? Colors.white : null,
                      height: 1.4,
                    ),
                  ),
                ],
              ],
            ),
          ),

          // 시간
          Padding(
            padding: const EdgeInsets.only(top: 2, left: 4, right: 4),
            child: Text(
              _formatTime(msg['created_at']),
              style: theme.textTheme.bodySmall
                  ?.copyWith(color: theme.colorScheme.outline, fontSize: 11),
            ),
          ),

          // 댓글 (replies) — 자동 변환 텍스트가 여기에 표시됨
          if (replies.isNotEmpty) ...[
            const SizedBox(height: 4),
            Container(
              margin: EdgeInsets.only(left: isMe ? 0 : 20, right: isMe ? 20 : 0),
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerLow,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                    color: theme.colorScheme.outlineVariant.withOpacity(0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: replies
                    .map<Widget>((reply) => Padding(
                          padding: const EdgeInsets.only(bottom: 6),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                reply['user_name'] ?? '시스템',
                                style: theme.textTheme.bodySmall?.copyWith(
                                    fontWeight: FontWeight.w600,
                                    color: theme.colorScheme.primary),
                              ),
                              const SizedBox(height: 2),
                              Text(reply['content'] ?? '',
                                  style: const TextStyle(height: 1.4)),
                            ],
                          ),
                        ))
                    .toList(),
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _formatTime(dynamic dateStr) {
    if (dateStr == null) return '';
    try {
      final dt = DateTime.parse(dateStr.toString()).toLocal();
      final hour = dt.hour.toString().padLeft(2, '0');
      final min = dt.minute.toString().padLeft(2, '0');
      return '$hour:$min';
    } catch (_) {
      return '';
    }
  }

  // ============================================================
  // 빌드
  // ============================================================
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Column(
          children: [
            Text(widget.roomName, style: const TextStyle(fontSize: 16)),
            if (_typingUser != null)
              Text('$_typingUser 입력 중...',
                  style: TextStyle(
                      fontSize: 11, color: theme.colorScheme.primary)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            tooltip: '음성파일 검색',
            onPressed: () => _showAudioSearch(),
          ),
          IconButton(
            icon: const Icon(Icons.info_outline),
            tooltip: '채팅방 정보',
            onPressed: _showRoomInfo,
          ),
        ],
      ),
      body: Column(
        children: [
          // 녹음 중 표시
          if (_isRecording)
            Container(
              width: double.infinity,
              color: Colors.red.shade50,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  Icon(Icons.fiber_manual_record,
                      color: Colors.red, size: 16),
                  const SizedBox(width: 8),
                  const Text('녹음 중...', style: TextStyle(color: Colors.red)),
                  const Spacer(),
                  TextButton(
                    onPressed: _toggleRecording,
                    child: const Text('중지 및 업로드'),
                  ),
                ],
              ),
            ),

          // 업로드 중 표시
          if (_isUploadingAudio)
            const LinearProgressIndicator(),

          // 메시지 리스트
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _messages.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.chat, size: 60,
                                color: theme.colorScheme.outline),
                            const SizedBox(height: 12),
                            Text('첫 메시지를 보내보세요!',
                                style: TextStyle(
                                    color: theme.colorScheme.outline)),
                            const SizedBox(height: 4),
                            Text('음성 파일을 올리면 자동으로 텍스트 변환됩니다',
                                style: TextStyle(
                                    fontSize: 12,
                                    color: theme.colorScheme.outline)),
                          ],
                        ),
                      )
                    : ListView.builder(
                        controller: _scrollController,
                        reverse: true,
                        padding: const EdgeInsets.only(top: 8, bottom: 8),
                        itemCount: _messages.length,
                        itemBuilder: (ctx, i) {
                          final msg = Map<String, dynamic>.from(_messages[i]);
                          return _buildMessageItem(msg);
                        },
                      ),
          ),

          // 입력 영역
          Container(
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 8,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: SafeArea(
              child: Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                child: Row(
                  children: [
                    // 첨부 버튼 (음성 파일 / 녹음)
                    IconButton(
                      icon: Icon(
                        _isRecording ? Icons.stop_circle : Icons.add_circle_outline,
                        color: _isRecording ? Colors.red : theme.colorScheme.primary,
                      ),
                      onPressed: _isRecording ? _toggleRecording : _showAttachMenu,
                    ),

                    // 텍스트 입력
                    Expanded(
                      child: TextField(
                        controller: _textController,
                        decoration: InputDecoration(
                          hintText: '메시지 입력...',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(24),
                            borderSide: BorderSide.none,
                          ),
                          filled: true,
                          fillColor:
                              theme.colorScheme.surfaceContainerHighest,
                          contentPadding: const EdgeInsets.symmetric(
                              horizontal: 16, vertical: 10),
                          isDense: true,
                        ),
                        textInputAction: TextInputAction.send,
                        onSubmitted: (_) => _sendTextMessage(),
                        maxLines: 4,
                        minLines: 1,
                        onChanged: (text) {
                          if (text.isNotEmpty) {
                            final auth = context.read<AuthService>();
                            auth.socket.sendTyping(
                              widget.roomId,
                              auth.currentUser?['name'] ?? '',
                              true,
                            );
                          }
                        },
                      ),
                    ),

                    const SizedBox(width: 4),

                    // 전송 버튼
                    IconButton(
                      icon: Icon(Icons.send_rounded,
                          color: theme.colorScheme.primary),
                      onPressed: _isSending ? null : _sendTextMessage,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // 음성 파일 검색 다이얼로그
  // ============================================================
  void _showAudioSearch() {
    final phoneCtrl = TextEditingController();
    final dateFromCtrl = TextEditingController();
    final dateToCtrl = TextEditingController();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (_, scrollCtrl) => _AudioSearchSheet(
          roomId: widget.roomId,
          scrollController: scrollCtrl,
        ),
      ),
    );
  }
}

// ============================================================
// 음성파일 검색 시트
// ============================================================
class _AudioSearchSheet extends StatefulWidget {
  final int roomId;
  final ScrollController scrollController;

  const _AudioSearchSheet({
    required this.roomId,
    required this.scrollController,
  });

  @override
  State<_AudioSearchSheet> createState() => _AudioSearchSheetState();
}

class _AudioSearchSheetState extends State<_AudioSearchSheet> {
  final _phoneCtrl = TextEditingController();
  List<dynamic> _results = [];
  bool _isSearching = false;

  Future<void> _search() async {
    setState(() => _isSearching = true);
    try {
      final api = context.read<ApiService>();
      _results = await api.searchAudio(
        widget.roomId,
        phone: _phoneCtrl.text.isNotEmpty ? _phoneCtrl.text : null,
      );
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('검색 실패: $e')));
    }
    if (mounted) setState(() => _isSearching = false);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.all(16),
      child: ListView(
        controller: widget.scrollController,
        children: [
          Text('음성 파일 검색',
              style: theme.textTheme.titleLarge),
          const SizedBox(height: 16),
          TextField(
            controller: _phoneCtrl,
            decoration: InputDecoration(
              labelText: '전화번호',
              hintText: '010, 1234 등 부분 검색 가능',
              border: const OutlineInputBorder(),
              suffixIcon: IconButton(
                icon: const Icon(Icons.search),
                onPressed: _search,
              ),
            ),
            keyboardType: TextInputType.phone,
            onSubmitted: (_) => _search(),
          ),
          const SizedBox(height: 12),
          if (_isSearching)
            const Center(child: CircularProgressIndicator())
          else if (_results.isEmpty)
            Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Text('검색 결과가 없습니다',
                    style: TextStyle(color: theme.colorScheme.outline)),
              ),
            )
          else
            ..._results.map((audio) => Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: const Icon(Icons.audio_file),
                    title: Text(audio['original_filename'] ?? ''),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (audio['phone_number'] != null)
                          Text('📞 ${audio['phone_number']}'),
                        if (audio['record_date'] != null)
                          Text('📅 ${audio['record_date']}'),
                        if (audio['transcript_text'] != null)
                          Text(
                            audio['transcript_text'],
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 12),
                          ),
                      ],
                    ),
                    isThreeLine: true,
                    trailing: audio['drive_url'] != null
                        ? const Icon(Icons.cloud_done, color: Colors.green)
                        : null,
                  ),
                )),
        ],
      ),
    );
  }
}

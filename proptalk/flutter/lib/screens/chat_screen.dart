import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/gestures.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../services/billing_service.dart';
import '../constants/terms.dart';
import '../theme/app_colors.dart';
import 'audio_picker_screen.dart';
import '../widgets/ad_banner_widget.dart';

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

  static IconData _getFileIcon(dynamic fileType) {
    switch (fileType) {
      case 'image': return Icons.image;
      case 'document': return Icons.description;
      case 'text': return Icons.article;
      case 'archive': return Icons.folder_zip;
      default: return Icons.attach_file;
    }
  }

  static final _urlRegex = RegExp(
    r'https?://[^\s<>\"]+',
    caseSensitive: false,
  );

  TextSpan _buildLinkedText(String text, TextStyle style, {TextStyle? linkStyle}) {
    final matches = _urlRegex.allMatches(text).toList();
    if (matches.isEmpty) {
      return TextSpan(text: text, style: style);
    }
    final spans = <TextSpan>[];
    var lastEnd = 0;
    for (final match in matches) {
      if (match.start > lastEnd) {
        spans.add(TextSpan(text: text.substring(lastEnd, match.start), style: style));
      }
      final url = match.group(0)!;
      spans.add(TextSpan(
        text: url,
        style: linkStyle ?? style.copyWith(color: Colors.blue, decoration: TextDecoration.underline),
        recognizer: TapGestureRecognizer()..onTap = () async {
          final uri = Uri.parse(url);
          await launchUrl(uri, mode: LaunchMode.externalApplication);
        },
      ));
      lastEnd = match.end;
    }
    if (lastEnd < text.length) {
      spans.add(TextSpan(text: text.substring(lastEnd), style: style));
    }
    return TextSpan(children: spans);
  }

  List<dynamic> _messages = [];
  bool _isLoading = true;
  bool _isSending = false;
  bool _isRecording = false;
  bool _isUploadingAudio = false;
  String? _typingUser;
  bool _showScrollToBottom = false;
  bool _hasText = false;

  StreamSubscription? _messageSub;
  StreamSubscription? _audioStatusSub;
  StreamSubscription? _fileStatusSub;
  StreamSubscription? _typingSub;
  StreamSubscription? _reconnectSub;

  // WebSocket 재연결 시 메시지 동기화용
  int? _lastMessageId;

  // 검색 관련
  bool _isSearchMode = false;
  List<dynamic> _searchResults = [];
  int _currentSearchIndex = -1;
  final TextEditingController _searchController = TextEditingController();
  int? _highlightedMessageId;

  // dispose에서 안전하게 사용하기 위해 참조 저장
  late final AuthService _auth;
  late String _roomName;

  @override
  void initState() {
    super.initState();
    _auth = context.read<AuthService>();
    _roomName = widget.roomName;
    _scrollController.addListener(_onScroll);
    _textController.addListener(_onTextChanged);
    _loadMessages();
    _setupWebSocket();
  }

  void _onScroll() {
    final show = _scrollController.hasClients && _scrollController.offset > 200;
    if (show != _showScrollToBottom) {
      setState(() => _showScrollToBottom = show);
    }
  }

  void _onTextChanged() {
    final has = _textController.text.trim().isNotEmpty;
    if (has != _hasText) {
      setState(() => _hasText = has);
    }
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _textController.removeListener(_onTextChanged);
    _messageSub?.cancel();
    _audioStatusSub?.cancel();
    _fileStatusSub?.cancel();
    _typingSub?.cancel();
    _reconnectSub?.cancel();
    _textController.dispose();
    _searchController.dispose();
    _scrollController.dispose();
    _recorder.dispose();

    _auth.socket.leaveRoom(widget.roomId);
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
          // audio 타입 메시지가 오면 임시(optimistic) 메시지 제거
          if (msg['type'] == 'audio') {
            _messages.removeWhere((m) => (m['id'] as int?) != null && (m['id'] as int) < 0);
          }
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
            if (data['drive_url'] != null) 'drive_url': data['drive_url'],
          };
        }
      });
    });

    // 파일 업로드 상태
    _fileStatusSub = socket.onFileStatus.listen((data) {
      if (!mounted) return;
      setState(() {
        final idx =
            _messages.indexWhere((m) => m['id'] == data['message_id']);
        if (idx >= 0) {
          _messages[idx] = {
            ..._messages[idx],
            'file_status': data['status'],
            if (data['drive_url'] != null) 'file_drive_url': data['drive_url'],
          };
        }
      });
    });

    // WebSocket 재연결 시 메시지 동기화 (폴링 대체)
    _reconnectSub = socket.onReconnect.listen((_) {
      if (mounted) _loadMessages();
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
      // 마지막 메시지 ID 저장 (폴링용)
      if (_messages.isNotEmpty) {
        _lastMessageId = _messages.first['id'] as int?;
      }
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
    // 선택 방식 다이얼로그
    final choice = await showModalBottomSheet<String>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.phone_android),
              title: const Text('녹음 파일 (최신순)'),
              subtitle: const Text('통화 녹음 폴더에서 선택'),
              onTap: () => Navigator.pop(ctx, 'recordings'),
            ),
            ListTile(
              leading: const Icon(Icons.folder_open),
              title: const Text('모든 파일'),
              subtitle: const Text('시스템 파일 선택기'),
              onTap: () => Navigator.pop(ctx, 'all'),
            ),
          ],
        ),
      ),
    );

    if (choice == null) return;

    File? selectedFile;

    if (choice == 'recordings') {
      // 커스텀 파일 브라우저
      selectedFile = await Navigator.push<File>(
        context,
        MaterialPageRoute(builder: (_) => const AudioPickerScreen()),
      );
    } else {
      // 기존 시스템 파일 선택기
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: [
          'mp3', 'wav', 'ogg', 'm4a', 'flac', 'webm', 'mp4', 'aac', 'amr', '3gp'
        ],
      );
      if (result != null && result.files.single.path != null) {
        selectedFile = File(result.files.single.path!);
      }
    }

    if (selectedFile != null) {
      await _uploadAudio(selectedFile);
    }
  }

  /// 첫 음성 업로드 시 동의 확인
  Future<bool> _checkAudioConsent() async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool('audio_consent_agreed') == true) return true;

    final agreed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Text('음성 데이터 처리 동의'),
        content: SingleChildScrollView(
          child: Text(
            AppTerms.audioUploadConsent,
            style: const TextStyle(height: 1.6),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('동의'),
          ),
        ],
      ),
    );

    if (agreed == true) {
      await prefs.setBool('audio_consent_agreed', true);
      // 서버에도 동의 기록
      try {
        final api = context.read<ApiService>();
        await api.recordConsent([
          {'type': 'audio_processing', 'version': '2026-03-01'},
        ]);
      } catch (_) {
        // 서버 기록 실패해도 앱 사용은 가능
      }
      return true;
    }
    return false;
  }

  Future<void> _uploadAudio(File file) async {
    // 잔여 시간 확인
    final billing = context.read<BillingService>();
    if (!billing.canTranscribe) {
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

    // 첫 업로드 시 동의 확인
    if (!await _checkAudioConsent()) return;

    setState(() => _isUploadingAudio = true);

    // Optimistic Update: 업로드 시작 즉시 메시지 표시
    final auth = context.read<AuthService>();
    final tempId = -DateTime.now().millisecondsSinceEpoch;
    final fileName = file.path.split('/').last;
    final tempMessage = {
      'id': tempId,
      'type': 'audio',
      'content': '🎙️ $fileName',
      'user_id': auth.currentUser?['id'],
      'user_name': auth.currentUser?['name'] ?? '',
      'audio_status': 'uploading',
      'created_at': DateTime.now().toIso8601String(),
      'replies': [],
    };

    setState(() {
      _messages.insert(0, tempMessage);
    });
    _scrollToBottom();

    try {
      final api = context.read<ApiService>();
      await api.uploadAudio(widget.roomId, file);
      // WebSocket이 실제 메시지로 대체해 줌
      _showError('업로드 완료! 변환 중...');
    } catch (e) {
      // 실패 시 임시 메시지 제거
      setState(() {
        _messages.removeWhere((m) => m['id'] == tempId);
      });
      // 잔액 부족(402) 시 충전 안내 다이얼로그 표시
      if (e is ApiException && e.statusCode == 402) {
        if (mounted) {
          await showDialog<void>(
            context: context,
            builder: (ctx) => AlertDialog(
              title: const Text('잔여 시간 부족'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(e.message),
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
        }
      } else {
        _showError('업로드 실패: $e');
      }
    }
    if (mounted) setState(() => _isUploadingAudio = false);
  }

  // ============================================================
  // Drive 링크 열기
  // ============================================================
  Future<void> _openDriveUrl(String url) async {
    try {
      final uri = Uri.parse(url);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      } else {
        _showError('링크를 열 수 없습니다');
      }
    } catch (e) {
      _showError('링크 열기 실패: $e');
    }
  }

  // ============================================================
  // 음성 파일 다운로드
  // ============================================================
  Future<void> _downloadAudio(int audioId) async {
    try {
      _showError('다운로드 중...');
      final api = context.read<ApiService>();

      // 파일 다운로드
      final bytes = await api.downloadAudio(audioId);

      // 저장 경로 결정 - Download/Proptalk 폴더
      String savePath;
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final fileName = 'proptalk_${audioId}_$timestamp.m4a';

      if (Platform.isAndroid) {
        // Android: Download/Proptalk 폴더
        final proptalkDir = Directory('/storage/emulated/0/Download/Proptalk');
        if (!await proptalkDir.exists()) {
          await proptalkDir.create(recursive: true);
        }
        savePath = '${proptalkDir.path}/$fileName';
      } else {
        // iOS: Documents/Proptalk 폴더
        final dir = await getApplicationDocumentsDirectory();
        final proptalkDir = Directory('${dir.path}/Proptalk');
        if (!await proptalkDir.exists()) {
          await proptalkDir.create(recursive: true);
        }
        savePath = '${proptalkDir.path}/$fileName';
      }

      // 파일 저장
      final file = File(savePath);
      await file.writeAsBytes(bytes);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('저장 완료: Download/Proptalk/$fileName'),
            duration: const Duration(seconds: 3),
          ),
        );
      }
    } catch (e) {
      _showError('다운로드 실패: $e');
    }
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
              leading: Icon(Icons.audio_file, color: Theme.of(context).colorScheme.primary),
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
                color: _isRecording ? Theme.of(context).extension<AppColors>()!.danger : Theme.of(context).extension<AppColors>()!.success,
              ),
              title: Text(_isRecording ? '녹음 중지' : '녹음 시작'),
              subtitle: const Text('직접 녹음하여 업로드'),
              onTap: () {
                Navigator.pop(ctx);
                _toggleRecording();
              },
            ),
            const Divider(height: 1),
            ListTile(
              leading: Icon(Icons.attach_file, color: Theme.of(context).colorScheme.primary),
              title: const Text('파일 전송'),
              subtitle: const Text('사진, 문서, PDF 등 → Drive 저장'),
              onTap: () {
                Navigator.pop(ctx);
                _pickAndUploadFile();
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _pickAndUploadFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: [
          'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp',
          'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
          'txt', 'csv', 'json', 'zip',
        ],
      );

      if (result == null || result.files.isEmpty) return;
      final file = File(result.files.single.path!);
      final fileName = result.files.single.name;

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$fileName 업로드 중...')),
      );

      final api = context.read<ApiService>();
      await api.uploadFile(widget.roomId, file);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('파일 업로드 실패: $e')),
      );
    }
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
      final pendingMembers = data['pending_members'] as List? ?? [];
      final inviteCode = room['invite_code'] ?? '';
      final myId = _auth.currentUser?['id'];
      final isAdmin = members.any((m) => m['id'] == myId && m['role'] == 'admin');

      if (!mounted) return;
      final nameController = TextEditingController(text: _roomName);
      bool isEditingName = false;
      final currentPending = List<dynamic>.from(pendingMembers);

      showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        builder: (ctx) => StatefulBuilder(
          builder: (ctx, setSheetState) {
            return SafeArea(
              child: SizedBox(
              height: MediaQuery.of(context).size.height * 0.9,
              child: Scaffold(
                appBar: AppBar(
                  leading: IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(ctx),
                  ),
                  title: const Text('채팅방 설정'),
                  automaticallyImplyLeading: false,
                ),
                body: ListView(
                  padding: const EdgeInsets.all(20),
                  children: [
                    // 채팅방 이름 (admin이면 수정 가능)
                    StatefulBuilder(
                      builder: (context, setNameState) {
                        if (isEditingName && isAdmin) {
                          return Row(
                            children: [
                              Expanded(
                                child: TextField(
                                  controller: nameController,
                                  autofocus: true,
                                  decoration: const InputDecoration(
                                    border: OutlineInputBorder(),
                                    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                  ),
                                  onSubmitted: (value) async {
                                    final newName = value.trim();
                                    if (newName.isEmpty || newName == _roomName) {
                                      setNameState(() => isEditingName = false);
                                      return;
                                    }
                                    try {
                                      await api.renameRoom(widget.roomId, newName);
                                      if (mounted) {
                                        setState(() => _roomName = newName);
                                        setNameState(() => isEditingName = false);
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          SnackBar(content: Text('이름이 "$newName"(으)로 변경되었습니다.')),
                                        );
                                      }
                                    } catch (e) {
                                      if (context.mounted) {
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          SnackBar(content: Text('이름 변경 실패: $e')),
                                        );
                                      }
                                    }
                                  },
                                ),
                              ),
                              const SizedBox(width: 8),
                              IconButton(
                                icon: const Icon(Icons.check),
                                onPressed: () async {
                                  final newName = nameController.text.trim();
                                  if (newName.isEmpty || newName == _roomName) {
                                    setNameState(() => isEditingName = false);
                                    return;
                                  }
                                  try {
                                    await api.renameRoom(widget.roomId, newName);
                                    if (mounted) {
                                      setState(() => _roomName = newName);
                                      setNameState(() => isEditingName = false);
                                      ScaffoldMessenger.of(context).showSnackBar(
                                        SnackBar(content: Text('이름이 "$newName"(으)로 변경되었습니다.')),
                                      );
                                    }
                                  } catch (e) {
                                    if (context.mounted) {
                                      ScaffoldMessenger.of(context).showSnackBar(
                                        SnackBar(content: Text('이름 변경 실패: $e')),
                                      );
                                    }
                                  }
                                },
                              ),
                              IconButton(
                                icon: const Icon(Icons.close),
                                onPressed: () => setNameState(() => isEditingName = false),
                              ),
                            ],
                          );
                        }
                        return Row(
                          children: [
                            Expanded(
                              child: Text(_roomName,
                                style: Theme.of(context).textTheme.headlineSmall),
                            ),
                            if (isAdmin)
                              IconButton(
                                icon: const Icon(Icons.edit, size: 20),
                                tooltip: '이름 변경',
                                onPressed: () {
                                  nameController.text = _roomName;
                                  setNameState(() => isEditingName = true);
                                },
                              ),
                          ],
                        );
                      },
                    ),
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

                    // Drive/Sheets 설정 (admin만 변경 가능)
                    if (isAdmin) ...[
                      const SizedBox(height: 12),
                      Card(
                        child: Column(
                          children: [
                            SwitchListTile(
                              title: const Text('Drive 자동 저장'),
                              subtitle: const Text('음성파일을 Google Drive에 백업'),
                              value: room['enable_drive_backup'] ?? true,
                              onChanged: (v) async {
                                try {
                                  await api.updateRoomSettings(widget.roomId, enableDriveBackup: v);
                                  setSheetState(() => room['enable_drive_backup'] = v);
                                } catch (e) {
                                  if (ctx.mounted) {
                                    ScaffoldMessenger.of(ctx).showSnackBar(
                                      SnackBar(content: Text('설정 변경 실패: $e')),
                                    );
                                  }
                                }
                              },
                            ),
                            SwitchListTile(
                              title: const Text('시트 기록'),
                              subtitle: const Text('변환 결과를 Google Sheets에 기록'),
                              value: room['enable_sheets_logging'] ?? true,
                              onChanged: (v) async {
                                try {
                                  await api.updateRoomSettings(widget.roomId, enableSheetsLogging: v);
                                  setSheetState(() => room['enable_sheets_logging'] = v);
                                } catch (e) {
                                  if (ctx.mounted) {
                                    ScaffoldMessenger.of(ctx).showSnackBar(
                                      SnackBar(content: Text('설정 변경 실패: $e')),
                                    );
                                  }
                                }
                              },
                            ),
                          ],
                        ),
                      ),
                    ],

                    // 승인 대기 섹션 (admin에게만 표시)
                    if (currentPending.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Icon(Icons.hourglass_top, size: 20, color: Theme.of(context).extension<AppColors>()!.warning),
                          const SizedBox(width: 4),
                          Text('승인 대기 (${currentPending.length}명)',
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                color: Theme.of(context).extension<AppColors>()!.warning,
                              )),
                        ],
                      ),
                      const SizedBox(height: 8),
                      ...currentPending.map((m) => Card(
                            color: Theme.of(context).extension<AppColors>()!.warningContainer.withValues(alpha: 0.3),
                            child: ListTile(
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
                              trailing: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  IconButton(
                                    icon: Icon(Icons.check_circle, color: Theme.of(context).extension<AppColors>()!.success),
                                    tooltip: '승인',
                                    onPressed: () async {
                                      try {
                                        await api.approveMember(widget.roomId, m['id']);
                                        setSheetState(() => currentPending.remove(m));
                                        if (context.mounted) {
                                          ScaffoldMessenger.of(context).showSnackBar(
                                            SnackBar(content: Text('${m['name']}님을 승인했습니다.')),
                                          );
                                        }
                                      } catch (e) {
                                        if (context.mounted) {
                                          ScaffoldMessenger.of(context).showSnackBar(
                                            SnackBar(content: Text('승인 실패: $e')),
                                          );
                                        }
                                      }
                                    },
                                  ),
                                  IconButton(
                                    icon: Icon(Icons.cancel, color: Theme.of(context).extension<AppColors>()!.danger),
                                    tooltip: '거절',
                                    onPressed: () async {
                                      try {
                                        await api.rejectMember(widget.roomId, m['id']);
                                        setSheetState(() => currentPending.remove(m));
                                        if (context.mounted) {
                                          ScaffoldMessenger.of(context).showSnackBar(
                                            SnackBar(content: Text('${m['name']}님을 거절했습니다.')),
                                          );
                                        }
                                      } catch (e) {
                                        if (context.mounted) {
                                          ScaffoldMessenger.of(context).showSnackBar(
                                            SnackBar(content: Text('거절 실패: $e')),
                                          );
                                        }
                                      }
                                    },
                                  ),
                                ],
                              ),
                            ),
                          )),
                    ],

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

                    // 관리 섹션
                    const SizedBox(height: 16),
                    const Divider(),
                    ListTile(
                      leading: Icon(Icons.exit_to_app, color: Theme.of(context).extension<AppColors>()!.warning),
                      title: Text('채팅방 나가기',
                        style: TextStyle(color: Theme.of(context).extension<AppColors>()!.warning)),
                      onTap: () {
                        Navigator.pop(ctx);
                        _showLeaveConfirmation();
                      },
                    ),
                    if (isAdmin)
                      ListTile(
                        leading: Icon(Icons.delete_forever, color: Theme.of(context).colorScheme.error),
                        title: Text('채팅방 삭제',
                          style: TextStyle(color: Theme.of(context).colorScheme.error)),
                        subtitle: const Text('모든 메시지가 영구 삭제됩니다'),
                        onTap: () {
                          Navigator.pop(ctx);
                          _showDeleteConfirmation();
                        },
                      ),
                  ],
                ),
              ),
            ),
            );
          },
        ),
      );
    } catch (e) {
      _showError('정보 로딩 실패: $e');
    }
  }

  void _showLeaveConfirmation() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('채팅방 나가기'),
        content: const Text('정말 이 채팅방을 나가시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Theme.of(context).extension<AppColors>()!.warning),
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                final api = context.read<ApiService>();
                await api.leaveRoom(widget.roomId);
                if (mounted) Navigator.pop(context);
              } catch (e) {
                _showError('나가기 실패: $e');
              }
            },
            child: const Text('나가기'),
          ),
        ],
      ),
    );
  }

  void _showDeleteConfirmation() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('채팅방 삭제'),
        content: const Text(
          '채팅방을 삭제하면 모든 메시지와 파일이 영구 삭제됩니다.\n이 작업은 되돌릴 수 없습니다.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Theme.of(context).colorScheme.error),
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                final api = context.read<ApiService>();
                await api.deleteRoom(widget.roomId);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('채팅방이 삭제되었습니다.')),
                  );
                  Navigator.pop(context);
                }
              } catch (e) {
                _showError('삭제 실패: $e');
              }
            },
            child: const Text('삭제'),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // 날짜 관련 헬퍼
  // ============================================================
  DateTime? _parseDate(dynamic dateStr) {
    if (dateStr == null) return null;
    try {
      return DateTime.parse(dateStr.toString()).toLocal();
    } catch (_) {
      return null;
    }
  }

  bool _isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  static const _weekdays = ['월', '화', '수', '목', '금', '토', '일'];

  Widget _buildDateSeparator(DateTime date, ThemeData theme) {
    final weekday = _weekdays[date.weekday - 1];
    final label = '${date.year}년 ${date.month}월 ${date.day}일 ${weekday}요일';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        children: [
          Expanded(child: Divider(color: theme.colorScheme.outlineVariant)),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.outline,
                fontSize: 11,
              ),
            ),
          ),
          Expanded(child: Divider(color: theme.colorScheme.outlineVariant)),
        ],
      ),
    );
  }

  // ============================================================
  // 메시지 위젯 빌더
  // ============================================================
  Widget _buildMessageItem(Map<String, dynamic> msg, {bool showName = true}) {
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
            color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text.rich(
              _buildLinkedText(
                msg['content'] ?? '',
                theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline) ?? const TextStyle(),
              )),
        ),
      );
    }

    final replies = msg['replies'] as List? ?? [];

    return GestureDetector(
      onLongPress: () {
        String textToCopy = msg['content'] ?? '';
        if (type == 'audio' && replies.isNotEmpty) {
          final replyTexts = replies.map((r) => r['content'] ?? '').where((s) => s.isNotEmpty).join('\n\n');
          if (replyTexts.isNotEmpty) {
            textToCopy = textToCopy.isNotEmpty ? '$textToCopy\n\n$replyTexts' : replyTexts;
          }
        }
        if (textToCopy.isNotEmpty) {
          Clipboard.setData(ClipboardData(text: textToCopy));
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('메시지가 복사되었습니다'), duration: Duration(seconds: 1)),
          );
        }
      },
      child: Container(
      color: _highlightedMessageId == msg['id']
          ? theme.colorScheme.primaryContainer.withValues(alpha: 0.4)
          : null,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: Column(
        crossAxisAlignment:
            isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          // 사용자 이름 (그룹 첫 메시지만 표시)
          if (!isMe && showName)
            Padding(
              padding: const EdgeInsets.only(left: 4, bottom: 2),
              child: Text(msg['user_name'] ?? '',
                  style: theme.textTheme.bodySmall
                      ?.copyWith(fontWeight: FontWeight.w600)),
            ),

          // 메시지 버블
          Align(
            alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.75,
            ),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: isMe
                  ? theme.colorScheme.primaryContainer
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
                              isMe ? theme.colorScheme.onPrimaryContainer.withValues(alpha: 0.7) : theme.colorScheme.primary),
                      const SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          msg['content'] ?? '',
                          style: TextStyle(
                            color: isMe ? theme.colorScheme.onPrimaryContainer : null,
                          ),
                        ),
                      ),
                    ],
                  ),
                  // 변환 상태 표시
                  if (msg['audio_status'] == 'transcribing' ||
                      msg['audio_status'] == 'summarizing')
                    Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          SizedBox(
                            width: 14, height: 14,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: isMe ? theme.colorScheme.onPrimaryContainer.withValues(alpha: 0.7) : theme.colorScheme.primary,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                              msg['audio_status'] == 'summarizing'
                                  ? '요약 생성 중...'
                                  : '텍스트 변환 중...',
                              style: TextStyle(
                                fontSize: 12,
                                color: isMe ? theme.colorScheme.onPrimaryContainer.withValues(alpha: 0.6) : theme.colorScheme.outline,
                              )),
                        ],
                      ),
                    ),
                  // Drive 열기 또는 다운로드 버튼
                  if (msg['audio_id'] != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: InkWell(
                        onTap: () {
                          final driveUrl = msg['drive_url'] as String?;
                          if (driveUrl != null && driveUrl.isNotEmpty) {
                            _openDriveUrl(driveUrl);
                          } else {
                            _downloadAudio(msg['audio_id']);
                          }
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                            color: isMe
                                ? theme.colorScheme.onPrimaryContainer.withValues(alpha: 0.15)
                                : theme.colorScheme.primaryContainer,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                  msg['drive_url'] != null ? Icons.open_in_new : Icons.download,
                                  size: 16,
                                  color: isMe
                                      ? theme.colorScheme.onPrimaryContainer
                                      : theme.colorScheme.primary),
                              const SizedBox(width: 4),
                              Text(msg['drive_url'] != null ? 'Drive에서 열기' : '다운로드',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w500,
                                    color: isMe
                                        ? theme.colorScheme.onPrimaryContainer
                                        : theme.colorScheme.primary,
                                  )),
                            ],
                          ),
                        ),
                      ),
                    ),
                ] else if (type == 'file') ...[
                  // 파일 메시지
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(_getFileIcon(msg['file_type']),
                          size: 18,
                          color: isMe ? theme.colorScheme.onPrimaryContainer.withValues(alpha: 0.7) : theme.colorScheme.primary),
                      const SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          msg['file_name'] ?? msg['content'] ?? '',
                          style: TextStyle(
                            color: isMe ? theme.colorScheme.onPrimaryContainer : null,
                          ),
                        ),
                      ),
                    ],
                  ),
                  if (msg['file_status'] == 'uploading' && (msg['file_drive_url'] == null || (msg['file_drive_url'] as String).isEmpty))
                    Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          SizedBox(
                            width: 14, height: 14,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: isMe ? theme.colorScheme.onPrimaryContainer.withValues(alpha: 0.7) : theme.colorScheme.primary,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text('Drive 업로드 중...',
                              style: TextStyle(
                                fontSize: 12,
                                color: isMe ? theme.colorScheme.onPrimaryContainer.withValues(alpha: 0.6) : theme.colorScheme.outline,
                              )),
                        ],
                      ),
                    ),
                  if (msg['file_drive_url'] != null && (msg['file_drive_url'] as String).isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: InkWell(
                        onTap: () async {
                          final uri = Uri.parse(msg['file_drive_url']);
                          await launchUrl(uri, mode: LaunchMode.externalApplication);
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: (isMe ? theme.colorScheme.onPrimaryContainer : theme.colorScheme.primary).withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.open_in_new,
                                  size: 16,
                                  color: isMe
                                      ? theme.colorScheme.onPrimaryContainer
                                      : theme.colorScheme.primary),
                              const SizedBox(width: 4),
                              Text('Drive에서 열기',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w500,
                                    color: isMe
                                        ? theme.colorScheme.onPrimaryContainer
                                        : theme.colorScheme.primary,
                                  )),
                            ],
                          ),
                        ),
                      ),
                    ),
                ] else ...[
                  // 일반 텍스트 또는 변환 결과
                  Text.rich(
                    _buildLinkedText(
                      msg['content'] ?? '',
                      TextStyle(
                        color: isMe ? theme.colorScheme.onPrimaryContainer : null,
                        height: 1.4,
                      ),
                      linkStyle: TextStyle(
                        color: isMe ? Colors.lightBlueAccent : Colors.blue,
                        decoration: TextDecoration.underline,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],
              ],
            ),
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

          // 댓글 (replies) — 파일정보 + 요약 텍스트가 여기에 표시됨
          if (replies.isNotEmpty) ...[
            const SizedBox(height: 4),
            Container(
              margin: EdgeInsets.only(left: isMe ? 0 : 20, right: isMe ? 20 : 0),
              padding: const EdgeInsets.only(left: 12, top: 10, right: 10, bottom: 10),
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerLow,
                borderRadius: BorderRadius.circular(12),
                border: Border(
                  left: BorderSide(
                    color: theme.colorScheme.primary,
                    width: 3,
                  ),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 모든 reply 내용 표시
                  ...replies.map<Widget>((reply) => Padding(
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
                        if (reply['type'] == 'transcript')
                          MarkdownBody(
                            data: reply['content'] ?? '',
                            styleSheet: MarkdownStyleSheet(
                              p: const TextStyle(fontSize: 14, height: 1.5),
                              h3: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: theme.colorScheme.primary),
                              listBullet: const TextStyle(fontSize: 14),
                              blockSpacing: 8,
                            ),
                            shrinkWrap: true,
                          )
                        else
                          Text.rich(
                            _buildLinkedText(
                              reply['content'] ?? '',
                              const TextStyle(height: 1.4),
                            ),
                          ),
                      ],
                    ),
                  )),
                  // 하단에 버튼 영역 (음성 저장 + 전체 복사)
                  if (msg['audio_id'] != null || replies.any((r) => r['type'] == 'transcript'))
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          // 음성 저장 또는 Drive 열기 버튼
                          if (msg['audio_id'] != null)
                            InkWell(
                              onTap: () {
                                final driveUrl = msg['drive_url'] as String?;
                                if (driveUrl != null && driveUrl.isNotEmpty) {
                                  _openDriveUrl(driveUrl);
                                } else {
                                  _downloadAudio(msg['audio_id']);
                                }
                              },
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                decoration: BoxDecoration(
                                  color: theme.colorScheme.primaryContainer,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(msg['drive_url'] != null ? Icons.open_in_new : Icons.download, size: 16, color: theme.colorScheme.primary),
                                    const SizedBox(width: 4),
                                    Text(msg['drive_url'] != null ? 'Drive에서 열기' : '음성 저장', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: theme.colorScheme.primary)),
                                  ],
                                ),
                              ),
                            ),
                          if (msg['audio_id'] != null)
                            const SizedBox(width: 8),
                          // 전체 복사 버튼 (파일정보 + 요약)
                          InkWell(
                            onTap: () {
                              final allContent = replies.map((r) => r['content'] ?? '').join('\n\n');
                              Clipboard.setData(ClipboardData(text: allContent));
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('전체 내용이 복사되었습니다')),
                              );
                            },
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                              decoration: BoxDecoration(
                                color: theme.colorScheme.secondaryContainer,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.copy, size: 16, color: theme.colorScheme.secondary),
                                  const SizedBox(width: 4),
                                  Text('전체 복사', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: theme.colorScheme.secondary)),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ],
        ],
      ),
    ),
    );
  }

  // ============================================================
  // 검색 기능
  // ============================================================
  void _performSearch(String query) async {
    if (query.trim().isEmpty) return;
    try {
      final api = context.read<ApiService>();
      final results = await api.searchMessages(widget.roomId, query.trim());
      setState(() {
        _searchResults = results;
        _currentSearchIndex = results.isNotEmpty ? 0 : -1;
        if (results.isNotEmpty) {
          _highlightedMessageId = results[0]['id'];
          _scrollToMessage(results[0]['id']);
        } else {
          _highlightedMessageId = null;
        }
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('검색 실패: $e'), duration: const Duration(seconds: 1)),
        );
      }
    }
  }

  void _nextSearchResult() {
    if (_searchResults.isEmpty) return;
    setState(() {
      _currentSearchIndex = (_currentSearchIndex + 1) % _searchResults.length;
      _highlightedMessageId = _searchResults[_currentSearchIndex]['id'];
      _scrollToMessage(_highlightedMessageId!);
    });
  }

  void _prevSearchResult() {
    if (_searchResults.isEmpty) return;
    setState(() {
      _currentSearchIndex = (_currentSearchIndex - 1 + _searchResults.length) % _searchResults.length;
      _highlightedMessageId = _searchResults[_currentSearchIndex]['id'];
      _scrollToMessage(_highlightedMessageId!);
    });
  }

  void _scrollToMessage(int messageId) {
    // ValueKey로 해당 메시지의 BuildContext를 찾아 스크롤
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final key = ValueKey<int>(messageId);
      final elementFinder = _findElementByKey(context, key);
      if (elementFinder != null) {
        Scrollable.ensureVisible(
          elementFinder,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
          alignment: 0.4, // 화면 40% 위치에 표시
        );
      }
    });
  }

  BuildContext? _findElementByKey(BuildContext context, ValueKey<int> key) {
    BuildContext? result;
    void visitor(Element element) {
      if (element.widget.key == key) {
        result = element;
        return;
      }
      element.visitChildren(visitor);
    }
    (context as Element).visitChildren(visitor);
    return result;
  }

  void _exitSearch() {
    setState(() {
      _isSearchMode = false;
      _searchResults = [];
      _currentSearchIndex = -1;
      _highlightedMessageId = null;
      _searchController.clear();
    });
  }

  String _formatTime(dynamic dateStr) {
    if (dateStr == null) return '';
    try {
      final dt = DateTime.parse(dateStr.toString()).toLocal();
      final now = DateTime.now();
      final hour = dt.hour.toString().padLeft(2, '0');
      final min = dt.minute.toString().padLeft(2, '0');
      final time = '$hour:$min';

      if (dt.year == now.year && dt.month == now.month && dt.day == now.day) {
        return time;
      } else if (dt.year != now.year) {
        return '${dt.year}.${dt.month.toString().padLeft(2, '0')}.${dt.day.toString().padLeft(2, '0')} $time';
      } else {
        return '${dt.month.toString().padLeft(2, '0')}/${dt.day.toString().padLeft(2, '0')} $time';
      }
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
      appBar: _isSearchMode
        ? AppBar(
            leading: IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: _exitSearch,
            ),
            title: TextField(
              controller: _searchController,
              autofocus: true,
              decoration: const InputDecoration(
                hintText: '메시지 검색...',
                border: InputBorder.none,
              ),
              onSubmitted: _performSearch,
            ),
            actions: [
              if (_searchResults.isNotEmpty)
                Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: Text(
                      '${_currentSearchIndex + 1}/${_searchResults.length}',
                      style: theme.textTheme.bodySmall,
                    ),
                  ),
                ),
              IconButton(
                icon: const Icon(Icons.keyboard_arrow_up),
                onPressed: _prevSearchResult,
              ),
              IconButton(
                icon: const Icon(Icons.keyboard_arrow_down),
                onPressed: _nextSearchResult,
              ),
            ],
          )
        : AppBar(
        title: Column(
          children: [
            Text(_roomName, style: const TextStyle(fontSize: 16)),
            if (_typingUser != null)
              Text('$_typingUser 입력 중...',
                  style: TextStyle(
                      fontSize: 11, color: theme.colorScheme.primary)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            tooltip: '메시지 검색',
            onPressed: () => setState(() => _isSearchMode = true),
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: '채팅방 설정',
            onPressed: _showRoomInfo,
          ),
        ],
      ),
      body: Column(
        children: [
          // 녹음 중 표시
          AnimatedSize(
            duration: const Duration(milliseconds: 200),
            child: _isRecording
                ? Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    decoration: BoxDecoration(
                      color: theme.extension<AppColors>()!.dangerContainer,
                      border: Border(
                        bottom: BorderSide(
                          color: theme.extension<AppColors>()!.danger.withValues(alpha: 0.3),
                        ),
                      ),
                    ),
                    child: Row(
                      children: [
                        _PulsingDot(color: theme.extension<AppColors>()!.danger),
                        const SizedBox(width: 10),
                        Text('녹음 중...', style: TextStyle(
                          color: theme.extension<AppColors>()!.danger,
                          fontWeight: FontWeight.w500,
                        )),
                        const Spacer(),
                        FilledButton.tonal(
                          onPressed: _toggleRecording,
                          style: FilledButton.styleFrom(
                            backgroundColor: theme.extension<AppColors>()!.danger,
                            foregroundColor: theme.extension<AppColors>()!.onDanger,
                            padding: const EdgeInsets.symmetric(horizontal: 16),
                          ),
                          child: const Text('중지 및 업로드'),
                        ),
                      ],
                    ),
                  )
                : const SizedBox.shrink(),
          ),

          // 업로드 중 표시
          if (_isUploadingAudio)
            const LinearProgressIndicator(),

          // 메시지 리스트
          Expanded(
            child: Stack(
              children: [
                _isLoading
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
                    : RawScrollbar(
                        controller: _scrollController,
                        thumbVisibility: false,
                        thickness: 6,
                        radius: const Radius.circular(3),
                        fadeDuration: const Duration(milliseconds: 300),
                        timeToFade: const Duration(seconds: 2),
                        padding: const EdgeInsets.only(right: 2),
                        child: ListView.builder(
                        controller: _scrollController,
                        reverse: true,
                        padding: const EdgeInsets.only(top: 8, bottom: 8),
                        itemCount: _messages.length,
                        itemBuilder: (ctx, i) {
                          final msg = Map<String, dynamic>.from(_messages[i]);

                          // 날짜 구분선: 다음 메시지(reverse이므로 i+1)와 날짜 비교
                          Widget? dateSeparator;
                          if (i < _messages.length - 1) {
                            final nextMsg = _messages[i + 1];
                            final curDate = _parseDate(msg['created_at']);
                            final nextDate = _parseDate(nextMsg['created_at']);
                            if (curDate != null && nextDate != null && !_isSameDay(curDate, nextDate)) {
                              dateSeparator = _buildDateSeparator(curDate, theme);
                            }
                          } else if (i == _messages.length - 1) {
                            final curDate = _parseDate(msg['created_at']);
                            if (curDate != null) {
                              dateSeparator = _buildDateSeparator(curDate, theme);
                            }
                          }

                          // 메시지 그룹핑: 같은 발신자 연속이면 이름 숨김
                          bool showName = true;
                          if (i < _messages.length - 1) {
                            final prevMsg = _messages[i + 1]; // reverse이므로 i+1이 "이전"
                            if (prevMsg['user_id'] == msg['user_id'] &&
                                prevMsg['type'] != 'system' &&
                                msg['type'] != 'system') {
                              final curDate = _parseDate(msg['created_at']);
                              final prevDate = _parseDate(prevMsg['created_at']);
                              if (curDate != null && prevDate != null && _isSameDay(curDate, prevDate)) {
                                showName = false;
                              }
                            }
                          }

                          return Column(
                            key: ValueKey<int>(msg['id'] ?? i),
                            children: [
                              if (dateSeparator != null) dateSeparator,
                              _buildMessageItem(msg, showName: showName),
                            ],
                          );
                        },
                      ),
                      ),
                // Scroll-to-bottom FAB
                if (_showScrollToBottom)
                  Positioned(
                    bottom: 12,
                    right: 12,
                    child: FloatingActionButton.small(
                      onPressed: _scrollToBottom,
                      heroTag: 'scrollToBottom',
                      elevation: 2,
                      child: const Icon(Icons.keyboard_arrow_down),
                    ),
                  ),
              ],
            ),
          ),

          // 배너 광고 (무료 사용자만)
          const AdBannerWidget(),

          // 입력 영역
          Container(
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.05),
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
                        color: _isRecording ? theme.extension<AppColors>()!.danger : theme.colorScheme.primary,
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

                    // 전송 버튼 (AnimatedSwitcher)
                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 200),
                      transitionBuilder: (child, anim) =>
                          ScaleTransition(scale: anim, child: child),
                      child: _hasText
                          ? IconButton(
                              key: const ValueKey('send'),
                              icon: Container(
                                width: 36,
                                height: 36,
                                decoration: BoxDecoration(
                                  color: theme.colorScheme.primary,
                                  shape: BoxShape.circle,
                                ),
                                child: Icon(Icons.arrow_upward_rounded,
                                    color: theme.colorScheme.onPrimary, size: 20),
                              ),
                              onPressed: _isSending ? null : _sendTextMessage,
                            )
                          : IconButton(
                              key: const ValueKey('mic'),
                              icon: Icon(Icons.mic_outlined,
                                  color: theme.colorScheme.outline),
                              onPressed: _showAttachMenu,
                            ),
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
                        ? Icon(Icons.cloud_done, color: Theme.of(context).extension<AppColors>()!.success)
                        : null,
                  ),
                )),
        ],
      ),
    );
  }
}

// ============================================================
// 녹음 중 펄스 점
// ============================================================
class _PulsingDot extends StatefulWidget {
  final Color color;
  const _PulsingDot({required this.color});

  @override
  State<_PulsingDot> createState() => _PulsingDotState();
}

class _PulsingDotState extends State<_PulsingDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: Tween<double>(begin: 0.3, end: 1.0).animate(_ctrl),
      child: Container(
        width: 10,
        height: 10,
        decoration: BoxDecoration(
          color: widget.color,
          shape: BoxShape.circle,
        ),
      ),
    );
  }
}

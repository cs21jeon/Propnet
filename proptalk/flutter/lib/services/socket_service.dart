import 'dart:async';
import 'package:socket_io_client/socket_io_client.dart' as IO;
import 'api_service.dart';

/// WebSocket 실시간 메시지 서비스
class SocketService {
  IO.Socket? _socket;
  final ApiService _api;
  
  // 이벤트 스트림
  final _messageController = StreamController<Map<String, dynamic>>.broadcast();
  final _audioStatusController = StreamController<Map<String, dynamic>>.broadcast();
  final _fileStatusController = StreamController<Map<String, dynamic>>.broadcast();
  final _typingController = StreamController<Map<String, dynamic>>.broadcast();
  final _userJoinedController = StreamController<Map<String, dynamic>>.broadcast();
  final _reconnectController = StreamController<void>.broadcast();

  Stream<Map<String, dynamic>> get onMessage => _messageController.stream;
  Stream<Map<String, dynamic>> get onAudioStatus => _audioStatusController.stream;
  Stream<Map<String, dynamic>> get onFileStatus => _fileStatusController.stream;
  Stream<Map<String, dynamic>> get onTyping => _typingController.stream;
  Stream<Map<String, dynamic>> get onUserJoined => _userJoinedController.stream;
  Stream<void> get onReconnect => _reconnectController.stream;
  
  bool get isConnected => _socket?.connected ?? false;
  
  SocketService(this._api);
  
  /// WebSocket 연결
  void connect() {
    if (_api.token == null) return;

    // baseUrl에서 /voiceroom을 제거하고 path로 설정
    const wsBaseUrl = 'https://goldenrabbit.biz';

    _socket = IO.io(
      wsBaseUrl,
      IO.OptionBuilder()
        .setTransports(['websocket'])
        .setPath('/voiceroom/socket.io/')
        .setAuth({'token': _api.token})
        .enableAutoConnect()
        .enableReconnection()
        .setReconnectionDelay(1000)
        .setReconnectionAttempts(10)
        .build(),
    );
    
    _socket!.onConnect((_) {
      print('[WS] 연결됨');
      _reconnectController.add(null);
    });
    
    _socket!.onDisconnect((_) {
      print('[WS] 연결 해제');
    });
    
    _socket!.onConnectError((error) {
      print('[WS] 연결 오류: $error');
    });
    
    // 새 메시지
    _socket!.on('new_message', (data) {
      _messageController.add(Map<String, dynamic>.from(data['message'] ?? data));
    });
    
    // 음성 파일 상태 변경
    _socket!.on('audio_status', (data) {
      _audioStatusController.add(Map<String, dynamic>.from(data));
    });
    
    // 파일 업로드 상태 변경
    _socket!.on('file_status', (data) {
      _fileStatusController.add(Map<String, dynamic>.from(data));
    });

    // 타이핑 표시
    _socket!.on('user_typing', (data) {
      _typingController.add(Map<String, dynamic>.from(data));
    });
    
    // 사용자 입장
    _socket!.on('user_joined', (data) {
      _userJoinedController.add(Map<String, dynamic>.from(data));
    });
  }
  
  /// 채팅방 입장
  void joinRoom(int roomId) {
    _socket?.emit('join_room', {
      'token': _api.token,
      'room_id': roomId,
    });
  }
  
  /// 채팅방 퇴장
  void leaveRoom(int roomId) {
    _socket?.emit('leave_room', {'room_id': roomId});
  }
  
  /// 타이핑 알림
  void sendTyping(int roomId, String userName, bool isTyping) {
    _socket?.emit('typing', {
      'room_id': roomId,
      'user_name': userName,
      'is_typing': isTyping,
    });
  }
  
  /// 연결 해제
  void disconnect() {
    _socket?.disconnect();
    _socket?.dispose();
    _socket = null;
  }
  
  void dispose() {
    disconnect();
    _messageController.close();
    _audioStatusController.close();
    _fileStatusController.close();
    _typingController.close();
    _userJoinedController.close();
    _reconnectController.close();
  }
}

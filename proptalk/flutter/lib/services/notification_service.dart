import 'dart:convert';
import 'dart:io';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'api_service.dart';

/// 백그라운드 메시지 핸들러 (top-level 함수 필수)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  // 백그라운드에서 수신된 메시지 — 시스템이 자동으로 알림 표시
}

/// FCM 푸시 알림 서비스
class NotificationService {
  static final NotificationService _instance = NotificationService._();
  factory NotificationService() => _instance;
  NotificationService._();

  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  String? _fcmToken;
  String? get fcmToken => _fcmToken;

  /// 알림 탭 콜백 (room_id 전달)
  void Function(int roomId)? onNotificationTap;

  /// 초기화
  Future<void> initialize() async {
    // 백그라운드 핸들러 등록
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

    // 알림 권한 요청 (Android 13+)
    final settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    if (settings.authorizationStatus == AuthorizationStatus.denied) {
      return;
    }

    // 로컬 알림 채널 설정 (Android)
    const androidChannel = AndroidNotificationChannel(
      'proptalk_messages',
      'Proptalk 메시지',
      description: '톡방 새 메시지 알림',
      importance: Importance.high,
    );

    await _localNotifications
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(androidChannel);

    // 로컬 알림 초기화
    const androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidSettings);

    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onNotificationTap,
    );

    // FCM 토큰 가져오기
    _fcmToken = await _messaging.getToken();

    // 토큰 갱신 리스너
    _messaging.onTokenRefresh.listen((newToken) {
      _fcmToken = newToken;
      // 서버에 갱신된 토큰 자동 등록은 ApiService 참조 없이 불가
      // auth_service에서 처리
    });

    // 포그라운드 메시지 수신 시 로컬 알림 표시
    FirebaseMessaging.onMessage.listen(_showLocalNotification);

    // 알림 탭으로 앱이 열린 경우 (terminated → opened)
    final initialMessage = await _messaging.getInitialMessage();
    if (initialMessage != null) {
      _handleMessageTap(initialMessage);
    }

    // 백그라운드 → 포그라운드 전환 시 알림 탭
    FirebaseMessaging.onMessageOpenedApp.listen(_handleMessageTap);
  }

  /// 포그라운드에서 수신된 메시지 → 로컬 알림 표시
  void _showLocalNotification(RemoteMessage message) {
    final notification = message.notification;
    if (notification == null) return;

    final roomId = message.data['room_id'];

    _localNotifications.show(
      notification.hashCode,
      notification.title,
      notification.body,
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'proptalk_messages',
          'Proptalk 메시지',
          channelDescription: '톡방 새 메시지 알림',
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
        ),
      ),
      payload: roomId != null ? jsonEncode({'room_id': roomId}) : null,
    );
  }

  /// 로컬 알림 탭 처리
  void _onNotificationTap(NotificationResponse response) {
    if (response.payload == null) return;
    try {
      final data = jsonDecode(response.payload!);
      final roomId = int.tryParse(data['room_id'].toString());
      if (roomId != null) {
        onNotificationTap?.call(roomId);
      }
    } catch (_) {}
  }

  /// FCM 메시지 탭 처리
  void _handleMessageTap(RemoteMessage message) {
    final roomId = int.tryParse(message.data['room_id']?.toString() ?? '');
    if (roomId != null) {
      onNotificationTap?.call(roomId);
    }
  }

  /// 서버에 FCM 토큰 등록
  Future<void> registerToken(ApiService api) async {
    if (_fcmToken == null) return;
    try {
      await api.registerDeviceToken(
        _fcmToken!,
        Platform.isAndroid ? 'android' : 'ios',
      );
    } catch (e) {
      // 실패해도 앱 동작에 영향 없음
    }
  }

  /// 서버에서 FCM 토큰 해제
  Future<void> unregisterToken(ApiService api) async {
    if (_fcmToken == null) return;
    try {
      await api.unregisterDeviceToken(_fcmToken!);
    } catch (_) {}
  }
}

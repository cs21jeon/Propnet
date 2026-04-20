import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'services/api_service.dart';
import 'services/auth_service.dart';
import 'services/billing_service.dart';
import 'services/ad_service.dart';
import 'services/notification_service.dart';
import 'screens/login_screen.dart';
import 'screens/main_screen.dart';
import 'screens/consent_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/share_room_picker_screen.dart';
import 'theme/app_theme.dart';
import 'theme/theme_provider.dart';
import 'widgets/propnet_footer.dart';

/// 전역 네비게이터 키 (알림 탭 시 화면 이동용)
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Firebase 초기화
  await Firebase.initializeApp();

  // 푸시 알림 초기화
  await NotificationService().initialize();

  // AdMob 초기화
  AdService().initialize();

  // 앱 버전 로드
  await PropnetFooter.loadVersion();

  final apiService = ApiService();
  final authService = AuthService(apiService);
  final billingService = BillingService(apiService);

  // 알림 탭 → 해당 채팅방으로 이동
  NotificationService().onNotificationTap = (roomId, roomName) {
    final navigator = navigatorKey.currentState;
    if (navigator != null) {
      navigator.push(
        MaterialPageRoute(
          builder: (_) => ChatScreen(roomId: roomId, roomName: roomName),
        ),
      );
    }
  };

  runApp(
    MultiProvider(
      providers: [
        Provider<ApiService>.value(value: apiService),
        ChangeNotifierProvider<AuthService>.value(value: authService),
        ChangeNotifierProvider<BillingService>.value(value: billingService),
        ChangeNotifierProvider<ThemeProvider>(create: (_) => ThemeProvider()),
      ],
      child: const VoiceRoomApp(),
    ),
  );
}

class VoiceRoomApp extends StatefulWidget {
  const VoiceRoomApp({super.key});

  @override
  State<VoiceRoomApp> createState() => _VoiceRoomAppState();
}

class _VoiceRoomAppState extends State<VoiceRoomApp> {
  static const _shareChannel = MethodChannel('biz.goldenrabbit.proptalk/share');

  /// 외부 공유로 받은 파일 (처리 대기 중)
  List<File>? _pendingSharedFiles;
  List<File>? _pendingSharedGeneralFiles;

  static const _audioExts = {
    'mp3', 'wav', 'ogg', 'm4a', 'flac', 'webm', 'mp4', 'aac', 'amr', '3gp',
  };

  @override
  void initState() {
    super.initState();

    // 자동 로그인 시도
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AuthService>().tryAutoLogin();
    });

    // 앱이 꺼져있을 때 공유로 시작된 경우 (초기 인텐트)
    _checkInitialSharedFiles();

    // 앱이 이미 실행 중일 때 공유 수신 (네이티브에서 호출)
    _shareChannel.setMethodCallHandler((call) async {
      if (call.method == 'onSharedFiles') {
        final paths = List<String>.from(call.arguments as List);
        _handleSharedPaths(paths);
      }
    });
  }

  Future<void> _checkInitialSharedFiles() async {
    try {
      final result = await _shareChannel.invokeMethod<List<dynamic>>('getSharedFiles');
      if (result != null && result.isNotEmpty) {
        _handleSharedPaths(result.cast<String>());
      }
    } catch (_) {
      // 공유 인텐트 없이 일반 실행
    }
  }

  /// 공유받은 파일 경로 처리 — 오디오와 일반 파일을 분기
  void _handleSharedPaths(List<String> paths) {
    final validFiles = paths
        .map((p) => File(p))
        .where((f) => f.existsSync())
        .toList();

    if (validFiles.isEmpty) return;

    final audioFiles = <File>[];
    final generalFiles = <File>[];

    for (final f in validFiles) {
      final ext = f.path.split('.').last.toLowerCase();
      if (_audioExts.contains(ext)) {
        audioFiles.add(f);
      } else {
        generalFiles.add(f);
      }
    }

    final auth = context.read<AuthService>();
    if (auth.isLoggedIn && !auth.consentRequired) {
      if (audioFiles.isNotEmpty) _navigateToRoomPicker(audioFiles, isAudio: true);
      if (generalFiles.isNotEmpty) _navigateToRoomPicker(generalFiles, isAudio: false);
    } else {
      setState(() {
        if (audioFiles.isNotEmpty) _pendingSharedFiles = audioFiles;
        if (generalFiles.isNotEmpty) _pendingSharedGeneralFiles = generalFiles;
      });
    }
  }

  /// 방 선택 화면으로 이동
  void _navigateToRoomPicker(List<File> files, {bool isAudio = true}) {
    final navigator = navigatorKey.currentState;
    if (navigator != null) {
      navigator.push(
        MaterialPageRoute(
          builder: (_) => ShareRoomPickerScreen(
            sharedFiles: files,
            isAudio: isAudio,
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeProvider = context.watch<ThemeProvider>();

    return MaterialApp(
      navigatorKey: navigatorKey,
      title: 'Proptalk',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: themeProvider.themeMode,
      home: Consumer<AuthService>(
        builder: (context, auth, _) {
          if (auth.isLoading) {
            return const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            );
          }
          if (!auth.isLoggedIn) {
            return const LoginScreen();
          }
          if (auth.consentRequired) {
            return const ConsentScreen();
          }
          // 로그인 완료 후 과금 상태 로드 (빌드 완료 후 실행)
          WidgetsBinding.instance.addPostFrameCallback((_) {
            context.read<BillingService>().loadBillingStatus();
          });
          // 대기 중인 공유 파일이 있으면 방 선택 화면으로 이동
          if (_pendingSharedFiles != null) {
            final files = _pendingSharedFiles!;
            _pendingSharedFiles = null;
            WidgetsBinding.instance.addPostFrameCallback((_) {
              _navigateToRoomPicker(files, isAudio: true);
            });
          }
          if (_pendingSharedGeneralFiles != null) {
            final files = _pendingSharedGeneralFiles!;
            _pendingSharedGeneralFiles = null;
            WidgetsBinding.instance.addPostFrameCallback((_) {
              _navigateToRoomPicker(files, isAudio: false);
            });
          }
          return const MainScreen();
        },
      ),
    );
  }
}

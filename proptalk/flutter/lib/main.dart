import 'package:flutter/material.dart';
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
    navigatorKey.currentState?.push(
      MaterialPageRoute(
        builder: (_) => ChatScreen(roomId: roomId, roomName: roomName),
      ),
    );
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
  @override
  void initState() {
    super.initState();
    // 자동 로그인 시도
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AuthService>().tryAutoLogin();
    });
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
          return const MainScreen();
        },
      ),
    );
  }
}

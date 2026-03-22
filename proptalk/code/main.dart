import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/api_service.dart';
import 'services/auth_service.dart';
import 'screens/login_screen.dart';
import 'screens/rooms_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  
  final apiService = ApiService();
  final authService = AuthService(apiService);
  
  runApp(
    MultiProvider(
      providers: [
        Provider<ApiService>.value(value: apiService),
        ChangeNotifierProvider<AuthService>.value(value: authService),
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
    return MaterialApp(
      title: 'VoiceRoom',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1A73E8),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        fontFamily: 'Pretendard',
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
        ),
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1A73E8),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
        fontFamily: 'Pretendard',
      ),
      themeMode: ThemeMode.system,
      home: Consumer<AuthService>(
        builder: (context, auth, _) {
          if (auth.isLoading) {
            return const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            );
          }
          return auth.isLoggedIn ? const RoomsScreen() : const LoginScreen();
        },
      ),
    );
  }
}

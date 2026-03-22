import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:propedia/core/router/app_router.dart';
import 'package:propedia/presentation/providers/theme_provider.dart';
import 'package:propedia/shared/theme/app_theme.dart';

class PropediaApp extends ConsumerWidget {
  const PropediaApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    final themeMode = ref.watch(themeModeProvider);

    return MaterialApp.router(
      title: 'Proppedia 부동산백과',
      debugShowCheckedModeBanner: false,

      // 테마 설정
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeMode,

      // go_router 설정
      routerConfig: router,
    );
  }
}

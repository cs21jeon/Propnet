import 'dart:io';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:propedia/presentation/widgets/common/app_drawer.dart';

/// 부동산매물지도 (propnet.kr/propmap/ 통합 매물지도 WebView)
///
/// 드로어 메뉴 "부동산매물지도" 선택 시 진입한다. PropMap은 이미 모바일
/// 반응형(지도 + 하단 바텀시트)으로 구현되어 있어 그대로 WebView로 임베드한다.
class PropMapWebScreen extends StatefulWidget {
  const PropMapWebScreen({super.key});

  @override
  State<PropMapWebScreen> createState() => _PropMapWebScreenState();
}

class _PropMapWebScreenState extends State<PropMapWebScreen> {
  static const String _propmapBase = 'https://propnet.kr/propmap/';
  static const String _prefKeyCenter = 'propmap_last_center';
  static const String _prefKeyLevel = 'propmap_last_level';

  /// Kakao Maps SDK가 WebView("wv" UA)를 감지하면 건물 레이블 디버그 레이어가
  /// 렌더링되는 문제가 있어 표준 모바일 Chrome UA로 위장한다.
  static const String _mobileChromeUa =
      'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36';

  late final WebViewController _controller;
  int _progress = 0;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _initWebView();
  }

  Future<void> _initWebView() async {
    final prefs = await SharedPreferences.getInstance();
    final lastCenter = prefs.getString(_prefKeyCenter);
    final lastLevel = prefs.getInt(_prefKeyLevel);

    // 현재 GPS 위치를 빠르게 가져와서 URL 파라미터로 전달
    String? myLoc;
    try {
      final pos = await Geolocator.getLastKnownPosition();
      if (pos != null) {
        myLoc = '${pos.latitude},${pos.longitude}';
      }
    } catch (_) {}

    // URL 구성: autoloc=1 + 내 위치 + 마지막 위치
    var url = '$_propmapBase?autoloc=1&inapp=1';
    if (myLoc != null) {
      url += '&myloc=$myLoc';
    }
    if (lastCenter != null) {
      url += '&center=$lastCenter';
      if (lastLevel != null) url += '&level=$lastLevel';
    }

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setUserAgent(_mobileChromeUa)
      ..setBackgroundColor(const Color(0xFFF8FAFC))
      ..setNavigationDelegate(
        NavigationDelegate(
          onProgress: (int progress) {
            if (!mounted) return;
            setState(() {
              _progress = progress;
              _isLoading = progress < 100;
            });
          },
          onPageStarted: (_) {
            if (!mounted) return;
            setState(() {
              _isLoading = true;
              _progress = 0;
            });
          },
          onPageFinished: (_) {
            if (!mounted) return;
            setState(() {
              _isLoading = false;
              _progress = 100;
            });
          },
        ),
      )
      ..loadRequest(Uri.parse(url));

    // Android: WebView 위치 권한 자동 승인
    if (Platform.isAndroid) {
      final androidController = _controller.platform as AndroidWebViewController;
      androidController.setGeolocationPermissionsPromptCallbacks(
        onShowPrompt: (request) async {
          return const GeolocationPermissionsResponse(allow: true, retain: true);
        },
      );
    }

    if (mounted) setState(() {});
  }

  /// 현재 지도 위치를 JS로 가져와 SharedPreferences에 저장
  Future<void> _saveLastPosition() async {
    try {
      final result = await _controller.runJavaScriptReturningResult('''
        (function() {
          try {
            var iframe = document.getElementById('mapIframe');
            if (iframe && iframe.contentWindow && iframe.contentWindow._kakaoMap) {
              var m = iframe.contentWindow._kakaoMap;
              var c = m.getCenter();
              var l = m.getLevel();
              return JSON.stringify({lat: c.getLat(), lng: c.getLng(), level: l});
            }
          } catch(e) {}
          return '{}';
        })()
      ''');
      final json = result.toString().replaceAll('"', '').replaceAll("'", '');
      if (json.contains('lat')) {
        // 간단 파싱
        final latMatch = RegExp(r'lat:([\d.]+)').firstMatch(json);
        final lngMatch = RegExp(r'lng:([\d.]+)').firstMatch(json);
        final levelMatch = RegExp(r'level:(\d+)').firstMatch(json);
        if (latMatch != null && lngMatch != null) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString(_prefKeyCenter, '${latMatch.group(1)},${lngMatch.group(1)}');
          if (levelMatch != null) {
            await prefs.setInt(_prefKeyLevel, int.parse(levelMatch.group(1)!));
          }
        }
      }
    } catch (_) {}
  }

  Future<void> _reload() async {
    await _controller.reload();
  }


  Future<bool> _handleBack() async {
    await _saveLastPosition();
    if (await _controller.canGoBack()) {
      await _controller.goBack();
      return false;
    }
    return true;
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (didPop) return;
        final shouldPop = await _handleBack();
        if (!shouldPop) return;
        if (!context.mounted) return;
        if (context.canPop()) {
          context.pop();
        } else {
          context.go('/home');
        }
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('부동산매물지도 PropMap'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () async {
              await _saveLastPosition();
              if (!context.mounted) return;
              if (context.canPop()) {
                context.pop();
              } else {
                context.go('/home');
              }
            },
          ),
          actions: [
            IconButton(
              tooltip: '새로고침',
              icon: const Icon(Icons.refresh),
              onPressed: _reload,
            ),
          ],
        ),
        drawer: const AppDrawer(currentApp: AppType.propmap),
        body: Stack(
          children: [
            WebViewWidget(controller: _controller),
            if (_isLoading)
              LinearProgressIndicator(
                value: _progress / 100.0,
                minHeight: 2,
              ),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:webview_flutter/webview_flutter.dart';
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
  static const String _propmapUrl = 'https://propnet.kr/propmap/';

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
      ..loadRequest(Uri.parse(_propmapUrl));
  }

  Future<void> _reload() async {
    await _controller.reload();
  }

  Future<bool> _handleBack() async {
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
        // 드로어에서 진입했을 수 있으므로 홈으로 이동
        if (context.canPop()) {
          context.pop();
        } else {
          context.go('/home');
        }
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('부동산매물지도'),
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

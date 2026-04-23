import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:propedia/presentation/widgets/common/app_drawer.dart';
import 'package:propedia/core/storage/token_storage.dart';
import 'package:propedia/presentation/providers/auth_provider.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// 부동산매물지도 (propnet.kr/propmap/ 통합 매물지도 WebView)
///
/// 드로어 메뉴 "부동산매물지도" 선택 시 진입한다. PropMap은 이미 모바일
/// 반응형(지도 + 하단 바텀시트)으로 구현되어 있어 그대로 WebView로 임베드한다.
class PropMapWebScreen extends ConsumerStatefulWidget {
  const PropMapWebScreen({super.key});

  @override
  ConsumerState<PropMapWebScreen> createState() => _PropMapWebScreenState();
}

class _PropMapWebScreenState extends ConsumerState<PropMapWebScreen> {
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
  String? _userName;
  String? _userEmail;

  @override
  void initState() {
    super.initState();
    _loadUserInfo();
    _initWebView();
  }

  Future<void> _loadUserInfo() async {
    try {
      final tokenStorage = TokenStorage();
      final token = await tokenStorage.getAccessToken();
      if (token != null && token.isNotEmpty) {
        final payload = _extractPayloadFromJwt(token);
        if (payload != null && mounted) {
          setState(() {
            _userName = payload['name'] as String?;
            _userEmail = payload['email'] as String?;
          });
        }
      }
    } catch (_) {}
  }

  static Map<String, dynamic>? _extractPayloadFromJwt(String jwt) {
    try {
      final parts = jwt.split('.');
      if (parts.length != 3) return null;
      final normalized = base64Url.normalize(parts[1]);
      final payloadStr = utf8.decode(base64Url.decode(normalized));
      return jsonDecode(payloadStr) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
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

    // propnet_token + propnet_uid 쿠키 주입 (앱 JWT → WebView 쿠키)
    // PropMap auth-ui.js가 propnet_uid로 로그인 상태 감지,
    // AI 패널/상세보기 API가 propnet_token으로 인증
    try {
      final tokenStorage = TokenStorage();
      final accessToken = await tokenStorage.getAccessToken();
      if (accessToken != null && accessToken.isNotEmpty) {
        final cookieManager = WebViewCookieManager();
        // HttpOnly 쿠키 (서버 API 인증용)
        await cookieManager.setCookie(
          WebViewCookie(
            name: 'propnet_token',
            value: accessToken,
            domain: 'propnet.kr',
            path: '/',
          ),
        );
        // JS 읽기용 쿠키 (auth-ui.js 로그인 상태 감지)
        // JWT payload에서 sub(=propnet_user_id) 추출
        final uid = _extractUidFromJwt(accessToken);
        if (uid != null) {
          await cookieManager.setCookie(
            WebViewCookie(
              name: 'propnet_uid',
              value: uid,
              domain: 'propnet.kr',
              path: '/',
            ),
          );
        }
      }
    } catch (e) {
      debugPrint('[PropMap] Cookie injection failed: $e');
    }

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

  /// JWT payload에서 sub(propnet_user_id) 추출
  static String? _extractUidFromJwt(String jwt) {
    try {
      final parts = jwt.split('.');
      if (parts.length != 3) return null;
      final normalized = base64Url.normalize(parts[1]);
      final payloadStr = utf8.decode(base64Url.decode(normalized));
      final payload = jsonDecode(payloadStr) as Map<String, dynamic>;
      final sub = payload['sub'];
      return sub?.toString();
    } catch (_) {
      return null;
    }
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

  bool get _isLoggedIn => _userName != null || _userEmail != null;

  Future<void> _goLogin() async {
    await _saveLastPosition();
    if (!mounted) return;
    // Proppedia 로그인 화면으로 이동, 완료 후 PropMap으로 복귀
    context.push('/login').then((_) {
      // 로그인 완료 후 유저 정보 재로드 + 쿠키 재주입 + WebView 새로고침
      _loadUserInfo().then((_) => _reinjectCookiesAndReload());
    });
  }

  Future<void> _doLogout() async {
    await ref.read(authProvider.notifier).logout();
    // 쿠키 삭제
    try {
      final cookieManager = WebViewCookieManager();
      await cookieManager.setCookie(WebViewCookie(name: 'propnet_token', value: '', domain: 'propnet.kr', path: '/'));
      await cookieManager.setCookie(WebViewCookie(name: 'propnet_uid', value: '', domain: 'propnet.kr', path: '/'));
    } catch (_) {}
    if (mounted) {
      setState(() {
        _userName = null;
        _userEmail = null;
      });
      _controller.reload();
    }
  }

  Future<void> _reinjectCookiesAndReload() async {
    try {
      final tokenStorage = TokenStorage();
      final accessToken = await tokenStorage.getAccessToken();
      if (accessToken != null && accessToken.isNotEmpty) {
        final cookieManager = WebViewCookieManager();
        await cookieManager.setCookie(WebViewCookie(name: 'propnet_token', value: accessToken, domain: 'propnet.kr', path: '/'));
        final uid = _extractUidFromJwt(accessToken);
        if (uid != null) {
          await cookieManager.setCookie(WebViewCookie(name: 'propnet_uid', value: uid, domain: 'propnet.kr', path: '/'));
        }
      }
    } catch (_) {}
    _controller.reload();
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
          title: const Text('매물지도 PropMap'),
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
            if (_isLoggedIn)
              PopupMenuButton<String>(
                offset: const Offset(0, 48),
                onSelected: (value) {
                  if (value == 'service') {
                    _controller.loadRequest(Uri.parse('https://propnet.kr/propsheet/'));
                  } else if (value == 'billing') {
                    _controller.loadRequest(Uri.parse('https://propnet.kr/billing/'));
                  } else if (value == 'logout') {
                    _doLogout();
                  }
                },
                itemBuilder: (context) => [
                  PopupMenuItem(
                    enabled: false,
                    child: Text(
                      _userName ?? _userEmail ?? '',
                      style: const TextStyle(fontWeight: FontWeight.w600, color: Colors.black87),
                    ),
                  ),
                  const PopupMenuDivider(),
                  const PopupMenuItem(value: 'service', child: Text('내 서비스')),
                  const PopupMenuItem(value: 'billing', child: Text('요금제')),
                  const PopupMenuItem(
                    value: 'logout',
                    child: Text('로그아웃', style: TextStyle(color: Colors.red)),
                  ),
                ],
                child: CircleAvatar(
                  radius: 16,
                  backgroundColor: const Color(0xFF3B82F6),
                  child: Text(
                    (_userName ?? _userEmail ?? 'U').characters.first.toUpperCase(),
                    style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600),
                  ),
                ),
              )
            else
              TextButton.icon(
                onPressed: _goLogin,
                icon: const Icon(Icons.login, size: 18),
                label: const Text('로그인'),
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

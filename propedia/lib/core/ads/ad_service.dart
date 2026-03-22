import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

/// AdMob 광고 서비스
class AdService {
  static final AdService _instance = AdService._internal();
  factory AdService() => _instance;
  AdService._internal();

  bool _isInitialized = false;

  /// 광고 초기화
  Future<void> initialize() async {
    if (_isInitialized) return;

    await MobileAds.instance.initialize();
    _isInitialized = true;

    if (kDebugMode) {
      print('AdMob initialized');
    }
  }

  /// 배너 광고 단위 ID
  /// 개발 중에는 테스트 ID 사용, 릴리즈에서는 실제 ID 사용
  String get bannerAdUnitId {
    if (kDebugMode) {
      // 테스트 광고 ID
      if (Platform.isAndroid) {
        return 'ca-app-pub-3940256099942544/6300978111';
      } else if (Platform.isIOS) {
        return 'ca-app-pub-3940256099942544/2934735716';
      }
    }

    // 실제 광고 ID
    if (Platform.isAndroid) {
      return 'ca-app-pub-3478991909223100/1393451919';
    } else if (Platform.isIOS) {
      // iOS 광고 단위 ID (추후 설정)
      return 'ca-app-pub-3940256099942544/2934735716';
    }

    return '';
  }

  /// 배너 광고 생성
  BannerAd createBannerAd({
    required void Function(Ad) onAdLoaded,
    required void Function(Ad, LoadAdError) onAdFailedToLoad,
  }) {
    return BannerAd(
      adUnitId: bannerAdUnitId,
      size: AdSize.banner,
      request: const AdRequest(),
      listener: BannerAdListener(
        onAdLoaded: onAdLoaded,
        onAdFailedToLoad: onAdFailedToLoad,
        onAdOpened: (ad) {
          if (kDebugMode) print('Ad opened');
        },
        onAdClosed: (ad) {
          if (kDebugMode) print('Ad closed');
        },
      ),
    );
  }
}

/// 전역 AdService 인스턴스
final adService = AdService();

import 'package:flutter/foundation.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

class AdService {
  static final AdService _instance = AdService._();
  factory AdService() => _instance;
  AdService._();

  bool _initialized = false;

  // 배너 Ad Unit ID (proptalk_banner_rooms)
  static const String bannerAdUnitId = 'ca-app-pub-3478991909223100/4866424920';

  Future<void> initialize() async {
    if (_initialized) return;
    await MobileAds.instance.initialize();

    // 테스트 기기 등록 (logcat에서 기기 ID 확인 후 추가)
    // 테스트 기기에서는 테스트 광고가 표시되어 무효 트래픽 방지
    MobileAds.instance.updateRequestConfiguration(
      RequestConfiguration(testDeviceIds: [
        // 'YOUR_TEST_DEVICE_ID', // logcat에서 확인한 기기 ID 추가
      ]),
    );

    _initialized = true;
    debugPrint('[AdService] AdMob initialized');
  }

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
      ),
    );
  }
}

import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:in_app_update/in_app_update.dart';
import 'package:logger/logger.dart';

/// Google Play In-App Update 서비스
///
/// Flexible 모드로 업데이트를 수행합니다.
/// - Android + Play Store 설치 앱에서만 동작
/// - 개발 환경에서는 에러가 발생하므로 graceful 하게 무시
class InAppUpdateService {
  static final _logger = Logger();

  /// 업데이트 가용 여부를 확인합니다.
  /// 업데이트가 가능하면 true를 반환합니다.
  static Future<bool> checkForUpdate() async {
    if (!_isSupported) return false;

    try {
      final info = await InAppUpdate.checkForUpdate();
      return info.updateAvailability == UpdateAvailability.updateAvailable &&
          info.flexibleUpdateAllowed == true;
    } catch (e) {
      // Play Store 미연결(개발 빌드), 에뮬레이터 등에서 발생
      _logger.d('In-app update check skipped: $e');
      return false;
    }
  }

  /// Flexible 업데이트를 시작합니다.
  /// 다운로드 완료 시 true를 반환합니다.
  static Future<bool> startFlexibleUpdate() async {
    if (!_isSupported) return false;

    try {
      final result = await InAppUpdate.startFlexibleUpdate();
      return result == AppUpdateResult.success;
    } catch (e) {
      _logger.w('Flexible update failed: $e');
      return false;
    }
  }

  /// 다운로드 완료된 업데이트를 설치합니다.
  /// 앱이 재시작됩니다.
  static Future<void> completeFlexibleUpdate() async {
    if (!_isSupported) return;

    try {
      await InAppUpdate.completeFlexibleUpdate();
    } catch (e) {
      _logger.w('Complete flexible update failed: $e');
    }
  }

  /// Android + 비웹 환경인지 확인
  static bool get _isSupported {
    if (kIsWeb) return false;
    try {
      return Platform.isAndroid;
    } catch (_) {
      return false;
    }
  }
}

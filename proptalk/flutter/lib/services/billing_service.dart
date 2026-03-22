import 'package:flutter/material.dart';
import 'api_service.dart';

/// 과금 상태 관리
class BillingService extends ChangeNotifier {
  final ApiService api;

  double _remainingSeconds = 600; // 10분 기본
  String _subscriptionStatus = 'free';
  String _planCode = 'free';
  String _planName = '무료 체험';
  String? _subscriptionExpiresAt;
  bool _autoRenew = false;
  bool _isLoading = false;

  double get remainingSeconds => _remainingSeconds;
  String get subscriptionStatus => _subscriptionStatus;
  String get planCode => _planCode;
  String get planName => _planName;
  String? get subscriptionExpiresAt => _subscriptionExpiresAt;
  bool get autoRenew => _autoRenew;
  bool get isLoading => _isLoading;

  /// STT 가능 여부
  bool get canTranscribe => _remainingSeconds > 0;

  /// 잔여 시간 포맷 (예: "2시간 30분")
  String get remainingTimeFormatted {
    final totalMinutes = (_remainingSeconds / 60).floor();
    if (totalMinutes <= 0) return '0분';
    final hours = totalMinutes ~/ 60;
    final mins = totalMinutes % 60;
    if (hours > 0 && mins > 0) return '$hours시간 $mins분';
    if (hours > 0) return '$hours시간';
    return '$mins분';
  }

  /// 무료 플랜 여부
  bool get isFree => _planCode == 'free';

  BillingService(this.api);

  /// 과금 상태 로드
  Future<void> loadBillingStatus() async {
    _isLoading = true;
    notifyListeners();

    try {
      final data = await api.getBillingStatus();
      _remainingSeconds = (data['remaining_seconds'] as num?)?.toDouble() ?? 600;
      _subscriptionStatus = data['subscription_status'] ?? 'free';
      _subscriptionExpiresAt = data['subscription_expires_at'];
      _autoRenew = data['auto_renew'] == true;

      final plan = data['plan'];
      if (plan != null) {
        _planCode = plan['code'] ?? 'free';
        _planName = plan['name'] ?? '무료 체험';
      }
    } catch (e) {
      debugPrint('[BillingService] 과금 상태 로드 실패: $e');
    }

    _isLoading = false;
    notifyListeners();
  }

  /// 결제 웹 URL (사용자가 직접 브라우저에서 접속)
  static const String billingWebUrl = 'https://goldenrabbit.biz/proptalk/billing/';

  /// 구독 해지
  Future<bool> cancelSubscription() async {
    try {
      final result = await api.cancelSubscription();
      if (result['success'] == true) {
        await loadBillingStatus();
        return true;
      }
    } catch (e) {
      debugPrint('[BillingService] 구독 해지 실패: $e');
    }
    return false;
  }

  /// 사용 후 잔여 시간 즉시 업데이트 (로컬)
  void onUsageDeducted(double secondsUsed) {
    _remainingSeconds -= secondsUsed;
    if (_remainingSeconds < 0) _remainingSeconds = 0;
    notifyListeners();
  }
}

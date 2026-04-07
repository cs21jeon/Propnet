import 'package:flutter/material.dart';

@immutable
class AppColors extends ThemeExtension<AppColors> {
  final Color warning;
  final Color onWarning;
  final Color warningContainer;
  final Color onWarningContainer;
  final Color danger;
  final Color onDanger;
  final Color dangerContainer;
  final Color success;
  final Color onSuccess;
  final Color successContainer;
  final Color chatBackground;
  final Color cardSurface;
  final Color myBubble;
  final Color onMyBubble;

  const AppColors({
    required this.warning,
    required this.onWarning,
    required this.warningContainer,
    required this.onWarningContainer,
    required this.danger,
    required this.onDanger,
    required this.dangerContainer,
    required this.success,
    required this.onSuccess,
    required this.successContainer,
    required this.chatBackground,
    required this.cardSurface,
    required this.myBubble,
    required this.onMyBubble,
  });

  static const light = AppColors(
    warning: Color(0xFFF59E0B),
    onWarning: Colors.white,
    warningContainer: Color(0xFFFEF3C7),
    onWarningContainer: Color(0xFF78350F),
    danger: Color(0xFFEF4444),
    onDanger: Colors.white,
    dangerContainer: Color(0xFFFEE2E2),
    success: Color(0xFF22C55E),
    onSuccess: Colors.white,
    successContainer: Color(0xFFDCFCE7),
    chatBackground: Color(0xFFE0E4E8),
    cardSurface: Color(0xFFFFFFFF),
    myBubble: Color(0xFF1A73E8),
    onMyBubble: Color(0xFFFFFFFF),
  );

  static const dark = AppColors(
    warning: Color(0xFFFBBF24),
    onWarning: Color(0xFF78350F),
    warningContainer: Color(0xFF451A03),
    onWarningContainer: Color(0xFFFEF3C7),
    danger: Color(0xFFF87171),
    onDanger: Color(0xFF450A0A),
    dangerContainer: Color(0xFF7F1D1D),
    success: Color(0xFF4ADE80),
    onSuccess: Color(0xFF052E16),
    successContainer: Color(0xFF14532D),
    chatBackground: Color(0xFF121218),
    cardSurface: Color(0xFF22222E),
    myBubble: Color(0xFF1A5FAA),
    onMyBubble: Color(0xFFFFFFFF),
  );

  @override
  AppColors copyWith({
    Color? warning,
    Color? onWarning,
    Color? warningContainer,
    Color? onWarningContainer,
    Color? danger,
    Color? onDanger,
    Color? dangerContainer,
    Color? success,
    Color? onSuccess,
    Color? successContainer,
    Color? chatBackground,
    Color? cardSurface,
    Color? myBubble,
    Color? onMyBubble,
  }) {
    return AppColors(
      warning: warning ?? this.warning,
      onWarning: onWarning ?? this.onWarning,
      warningContainer: warningContainer ?? this.warningContainer,
      onWarningContainer: onWarningContainer ?? this.onWarningContainer,
      danger: danger ?? this.danger,
      onDanger: onDanger ?? this.onDanger,
      dangerContainer: dangerContainer ?? this.dangerContainer,
      success: success ?? this.success,
      onSuccess: onSuccess ?? this.onSuccess,
      successContainer: successContainer ?? this.successContainer,
      chatBackground: chatBackground ?? this.chatBackground,
      cardSurface: cardSurface ?? this.cardSurface,
      myBubble: myBubble ?? this.myBubble,
      onMyBubble: onMyBubble ?? this.onMyBubble,
    );
  }

  @override
  AppColors lerp(AppColors? other, double t) {
    if (other is! AppColors) return this;
    return AppColors(
      warning: Color.lerp(warning, other.warning, t)!,
      onWarning: Color.lerp(onWarning, other.onWarning, t)!,
      warningContainer: Color.lerp(warningContainer, other.warningContainer, t)!,
      onWarningContainer: Color.lerp(onWarningContainer, other.onWarningContainer, t)!,
      danger: Color.lerp(danger, other.danger, t)!,
      onDanger: Color.lerp(onDanger, other.onDanger, t)!,
      dangerContainer: Color.lerp(dangerContainer, other.dangerContainer, t)!,
      success: Color.lerp(success, other.success, t)!,
      onSuccess: Color.lerp(onSuccess, other.onSuccess, t)!,
      successContainer: Color.lerp(successContainer, other.successContainer, t)!,
      chatBackground: Color.lerp(chatBackground, other.chatBackground, t)!,
      cardSurface: Color.lerp(cardSurface, other.cardSurface, t)!,
      myBubble: Color.lerp(myBubble, other.myBubble, t)!,
      onMyBubble: Color.lerp(onMyBubble, other.onMyBubble, t)!,
    );
  }
}

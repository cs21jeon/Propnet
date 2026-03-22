import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:package_info_plus/package_info_plus.dart';

/// 앱 버전 정보 Provider
/// pubspec.yaml의 version을 자동으로 읽어옴
final appInfoProvider = FutureProvider<PackageInfo>((ref) async {
  return await PackageInfo.fromPlatform();
});

/// 앱 버전 문자열 (예: "1.0.2+10")
final appVersionProvider = Provider<String>((ref) {
  final info = ref.watch(appInfoProvider);
  return info.when(
    data: (info) => '${info.version}+${info.buildNumber}',
    loading: () => '',
    error: (_, __) => '',
  );
});

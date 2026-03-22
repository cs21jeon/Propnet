import 'package:propedia/core/utils/jibun_address_parser.dart';

void main() {
  final testCases = [
    // 기본 형식
    '사당동 272-26',
    '사당동 1044-23',
    '사당동 318-107',
    // 띄어쓰기 없음
    '사당동272-26',
    '사당동1044-23',
    // 구/시 포함
    '동작구 사당동 272-26',
    '서울시 동작구 사당동 272-26',
    // 부번 없음
    '사당동 1154',
    '사당동 280',
    // 임야(산) 형식
    '산 32-77',
    '사당동 산 32-77',
    '사당동 산32-77',
    '사당동산32-77',
    '사당동산 32-77',  // 버그 수정 테스트
  ];

  print('=== 지번 파싱 테스트 ===\n');
  
  for (final input in testCases) {
    final result = JibunAddressParser.parse(input);
    print('입력: "$input"');
    print('  -> addressQuery: ${result.addressQuery}');
    print('  -> bun: ${result.bun}, ji: ${result.ji}');
    print('  -> isMountain: ${result.isMountain}');
    if (result.error != null) print('  -> ERROR: ${result.error}');
    print('');
  }
}

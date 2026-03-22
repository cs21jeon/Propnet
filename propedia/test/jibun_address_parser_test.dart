import 'package:propedia/core/utils/jibun_address_parser.dart';

void main() {
  print('=' * 70);
  print('JibunAddressParser 테스트');
  print('=' * 70);

  final testCases = <(String, List<String>)>[
    // 1. 기본 형식
    ('1. 기본 형식', [
      '사당동 272-26',
      '사당동 1044-23',
      '사당동 318-107',
    ]),
    // 2. 띄어쓰기 없음
    ('2. 띄어쓰기 없음', [
      '사당동272-26',
      '사당동1044-23',
    ]),
    // 3. 구/시 포함
    ('3. 구/시 포함', [
      '동작구 사당동 272-26',
      '서울시 동작구 사당동 272-26',
    ]),
    // 4. 부번 없음
    ('4. 부번 없음', [
      '사당동 1154',
      '사당동 280',
    ]),
    // 5. 임야(산) 형식
    ('5. 임야(산) 형식', [
      '산 32-77',
      '사당동 산 32-77',
      '사당동 산32-77',
      '사당동산32-77',
      '사당동산 32-77',
    ]),
  ];

  for (final testCase in testCases) {
    final category = testCase.$1;
    final inputs = testCase.$2;
    
    print('\n$category');
    print('-' * 70);
    
    for (final input in inputs) {
      final result = JibunAddressParser.parse(input);
      
      print('입력: "$input"');
      if (result.error != null) {
        print('  -> ERROR: ${result.error}');
      } else {
        final addrQuery = result.addressQuery ?? '(null)';
        print('  -> addressQuery: "$addrQuery"');
        print('     bun: ${result.bun}, ji: ${result.ji}');
        print('     isMountain: ${result.isMountain}');
      }
      print('');
    }
  }
  
  print('=' * 70);
  print('테스트 완료');
  print('=' * 70);
}

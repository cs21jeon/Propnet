/// 지번 주소 파싱 유틸리티
///
/// 사용자가 입력한 자유 형식의 지번 주소를 파싱하여
/// 법정동 검색어, 본번, 부번으로 분리합니다.
///
/// 지원 형식:
/// - "사당동 272-26"
/// - "동작구 사당동 272"
/// - "서울시 동작구 사당동 272-26"
/// - "산 123-45" (임야)
/// - "사당동 산 123-45" (임야)
class JibunAddressParser {
  /// 입력 문자열을 파싱하여 JibunParseResult 반환
  static JibunParseResult parse(String input) {
    final trimmed = input.trim();

    if (trimmed.isEmpty) {
      return JibunParseResult(error: '주소를 입력해주세요');
    }

    // 1. "산" 접두어 감지 (여러 위치에서 가능)
    bool isMountain = false;
    String working = trimmed;

    // "산 123-45" 또는 "산123-45" 형태 (맨 앞에 산)
    if (RegExp(r'^산\s*\d').hasMatch(working)) {
      isMountain = true;
      working = working.replaceFirst(RegExp(r'^산\s*'), '');
    }
    // "사당동 산 123-45" 형태 (공백+산+공백+숫자)
    else if (RegExp(r'\s산\s+\d').hasMatch(working)) {
      isMountain = true;
      working = working.replaceFirst(' 산 ', ' ');
    }
    // "사당동 산123-45" 형태 (공백+산+숫자, 산 뒤 공백 없음)
    else if (RegExp(r'\s산\d').hasMatch(working)) {
      isMountain = true;
      working = working.replaceFirst(' 산', ' ');
    }
    // "사당동산123-45" 형태 (공백 없이 동/리/읍/면 바로 뒤에 산+숫자)
    else if (RegExp(r'[동리읍면]산\d').hasMatch(working)) {
      isMountain = true;
      // 동/리/읍/면 뒤의 "산"을 공백으로 대체
      working = working.replaceFirstMapped(
        RegExp(r'([동리읍면])산(\d)'),
        (match) => '${match.group(1)} ${match.group(2)}',
      );
    }
    // "사당동산 32-77" 형태 (동/리/읍/면+산+공백+숫자)
    else if (RegExp(r'[동리읍면]산\s+\d').hasMatch(working)) {
      isMountain = true;
      // 동/리/읍/면 뒤의 "산 "을 공백으로 대체
      working = working.replaceFirstMapped(
        RegExp(r'([동리읍면])산\s+'),
        (match) => '${match.group(1)} ',
      );
    }

    // 2. 끝에서 번지 추출 (숫자-숫자 또는 숫자만)
    // 패턴: 1-4자리 숫자, 선택적으로 -와 1-4자리 숫자
    final lotPattern = RegExp(r'(\d{1,4})(?:\s*-\s*(\d{1,4}))?$');
    final match = lotPattern.firstMatch(working);

    if (match == null) {
      return JibunParseResult(error: '번지를 찾을 수 없습니다');
    }

    final bun = match.group(1)!;
    final ji = match.group(2) ?? '0';

    // 번지 앞부분은 주소 쿼리
    final addressQuery = working.substring(0, match.start).trim();

    return JibunParseResult(
      addressQuery: addressQuery.isEmpty ? null : addressQuery,
      bun: bun,
      ji: ji,
      isMountain: isMountain,
    );
  }

  /// 본번-부번 문자열만 파싱 (기존 하이브리드 방식 지원)
  static (String bun, String ji) parseLotNumber(String input) {
    final trimmed = input.trim();
    if (trimmed.contains('-')) {
      final parts = trimmed.split('-');
      final bun = parts[0].trim();
      final ji = parts.length > 1 ? parts[1].trim() : '0';
      return (bun, ji.isEmpty ? '0' : ji);
    }
    return (trimmed, '0');
  }
}

/// 지번 파싱 결과
class JibunParseResult {
  /// 법정동 검색 쿼리 (예: "사당동", "동작구 사당동")
  final String? addressQuery;

  /// 본번 (예: "272")
  final String? bun;

  /// 부번 (예: "26", 없으면 "0")
  final String? ji;

  /// 임야 여부 ("산" 접두어 감지)
  final bool isMountain;

  /// 에러 메시지 (파싱 실패 시)
  final String? error;

  JibunParseResult({
    this.addressQuery,
    this.bun,
    this.ji,
    this.isMountain = false,
    this.error,
  });

  /// 파싱 성공 여부
  bool get isValid => error == null && bun != null;

  /// 번지가 있는지 여부
  bool get hasLotNumber => bun != null && bun!.isNotEmpty;

  /// 법정동 쿼리가 있는지 여부
  bool get hasAddressQuery => addressQuery != null && addressQuery!.isNotEmpty;

  /// 토지 구분 코드 반환 ('1'=대지, '2'=임야)
  String get landType => isMountain ? '2' : '1';

  /// 부번 반환 (API 호출용, 기본값 '0')
  String get jiForApi => (ji == null || ji!.isEmpty) ? '0' : ji!;

  @override
  String toString() {
    if (error != null) return 'JibunParseResult(error: $error)';
    return 'JibunParseResult(addressQuery: $addressQuery, bun: $bun, ji: $ji, isMountain: $isMountain)';
  }
}

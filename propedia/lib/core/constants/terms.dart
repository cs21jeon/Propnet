/// PropNet 이용약관 및 개인정보처리방침 상수
/// 통합 법적 문서: https://propnet.kr/legal/*
/// Proptalk 법적 문서: https://propnet.kr/proptalk/terms, /privacy

class Terms {
  Terms._();

  /// 약관 버전 (PropNet 통합 인증 시스템)
  static const String currentVersion = '2026-04-03';

  // --- 통합 법적 문서 URL ---
  static const String termsUrl = 'https://propnet.kr/proptalk/terms';
  static const String privacyUrl = 'https://propnet.kr/proptalk/privacy';
  static const String overseasTransferUrl =
      'https://propnet.kr/legal/overseas-transfer.html';

  /// 동의 타입별 전문 텍스트 매핑
  static String? getFullTextForType(String type) {
    switch (type) {
      case 'terms':
        return termsOfService;
      case 'privacy':
        return privacyPolicy;
      case 'overseas_transfer':
        return overseasTransfer;
      default:
        return null;
    }
  }

  /// 동의 타입별 웹 URL 매핑
  static String? getWebUrlForType(String type) {
    switch (type) {
      case 'terms':
        return termsUrl;
      case 'privacy':
        return privacyUrl;
      case 'overseas_transfer':
        return overseasTransferUrl;
      default:
        return null;
    }
  }

  /// 서비스 이용약관
  static const String termsOfService = '''
PropNet 서비스 이용약관

시행일: 2026년 4월 3일

제1조 (목적)
이 약관은 프롭넷(이하 "회사")이 제공하는 PropNet 서비스(이하 "서비스")의 이용과 관련하여 회사와 이용자 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.

제2조 (정의)
1. "서비스"란 회사가 PropNet 브랜드로 제공하는 다음의 서비스를 포함한 모든 기능을 말합니다.
   - Proppedia: 건축물대장, 토지대장, 공시가격 등 부동산 정보 조회 서비스
   - Proptalk: 음성-텍스트 변환(STT), AI 요약, 팀 채팅 서비스
   - Propsheet: 부동산 데이터베이스 관리 서비스
   - PropMap: 중개사별 매물 지도 및 홈페이지 서비스
2. "회원"이란 서비스에 가입하여 이용 계약을 체결한 자를 말합니다.
3. "일반 회원"이란 Google 계정으로 가입한 개인 이용자를 말합니다.
4. "중개사 회원(Agent)"이란 공인중개사 자격을 보유하고, 중개사 인증을 완료한 회원을 말합니다.

제3조 (약관의 효력 및 변경)
1. 이 약관은 서비스 화면에 게시하거나 공지함으로써 효력이 발생합니다.
2. 회사는 관련 법령을 위배하지 않는 범위에서 약관을 개정할 수 있으며, 변경 시 7일 전부터 공지합니다.
3. 이용자가 변경된 약관에 동의하지 않을 경우 탈퇴할 수 있습니다.

제4조 (서비스의 제공)
1. Proppedia: 건축물/토지/공시가격 조회, 검색, 즐겨찾기, PDF 저장 (무료)
2. Proptalk: 음성-텍스트 변환(STT), AI 요약, 채팅방, Google Drive 백업
3. Propsheet: 부동산 매물 데이터베이스 관리 (Agent 요금제 포함)
4. PropMap: 중개사별 매물 지도 홈페이지 (Agent 요금제 포함)
서비스는 연중무휴 24시간 제공을 원칙으로 하나, 시스템 점검 등의 사유로 일시 중단될 수 있습니다.

제5조 (회원가입 및 회원 유형)
1. 이용자는 Google 계정을 통해 회원 가입할 수 있습니다.
2. 중개사 회원 가입 시 사무소명, 중개사등록번호, 사업자등록번호, 대표자명, 소재지를 추가 제공해야 합니다.
3. 허위 정보 기재 시 중개사 자격 취소 및 서비스 이용이 제한됩니다.
4. 회원은 언제든지 탈퇴할 수 있으며, 탈퇴 시 모든 정보가 즉시 삭제됩니다.

제6조 (회원의 의무)
1. 관계 법령, 본 약관을 준수하여야 합니다.
2. 자신의 계정을 관리할 책임이 있으며, 타인에게 양도/공유할 수 없습니다.
3. 서비스를 이용하여 얻은 정보를 무단으로 상업적 목적에 이용하거나 제3자에게 제공할 수 없습니다.
4. 중개사 회원은 사무소 정보의 정확성을 유지하고, PropMap 매물 정보의 정확성에 대한 책임이 있습니다.

제7조 (서비스 이용의 제한)
타인 정보 도용, 서비스 운영 방해, 관련 법령/약관 위반, 불법 콘텐츠 업로드, 중개사 허위 정보/자격 상실 시 이용을 제한할 수 있습니다.

제8조 (면책조항)
1. 천재지변, 불가항력 등으로 인한 서비스 중단에 대해 책임을 지지 않습니다.
2. 부동산 정보는 공공데이터를 기반으로 하며 참고 목적으로만 제공됩니다. 법적 효력이 없으므로 중요한 의사결정 시 관할 관청의 공식 서류를 확인하시기 바랍니다.
3. STT 결과 및 AI 요약의 정확성을 보장하지 않습니다.
4. PropMap 매물 정보의 정확성 책임은 해당 중개사 회원에게 있습니다.

제9조 (분쟁해결)
대한민국 법률을 준거법으로 하며, 합의 불가 시 관할 법원에 제소합니다.

부칙
이 약관은 2026년 4월 3일부터 시행됩니다.
2026년 2월 1일자 이전 약관은 이 약관으로 대체됩니다.
''';

  /// 개인정보 수집/이용 동의
  static const String privacyPolicy = '''
개인정보 처리방침

시행일: 2026년 4월 3일

프롭넷(이하 "회사")은 PropNet 서비스(Proppedia, Proptalk, Propsheet, PropMap 등 회사가 운영하는 모든 서비스를 포함하며, 이하 "서비스")를 운영함에 있어 「개인정보 보호법」 및 관련 법령을 준수하며, 이용자의 개인정보를 보호합니다.

1. 수집하는 개인정보 항목

[전체 회원 - 필수]
- 이메일 주소, 이름, 프로필 사진 (Google 계정 연동)
- 자동 수집: 기기 정보, IP 주소, 접속 일시, 앱 버전

[중개사(Agent) 회원 - 추가 필수]
- 사무소명(상호), 중개사등록번호, 사업자등록번호, 대표자명, 사무소 소재지
- 선택: 사무소 전화번호
수집 목적: 중개사 자격 확인, Propsheet/PropMap 서비스 제공

[서비스별 수집]
- Proppedia: 검색 기록, 즐겨찾기 → 탈퇴 시까지
- Proptalk: 음성 파일, STT 결과, AI 요약, 채팅 → 24시간 후 자동 삭제
- Propsheet: 매물 데이터 → 서비스 해지 또는 탈퇴 시까지
- PropMap: 매물 게시 정보 → 서비스 해지 또는 탈퇴 시까지

2. 수집 및 이용 목적
- 회원 관리 및 서비스 제공
- 중개사 인증 및 Agent 서비스 제공
- 서비스 개선 및 통계 분석
- 요금 결제 처리

3. 제3자 제공
- OpenAI (미국): 음성 파일 → Whisper API (STT 변환)
- Anthropic (미국): 변환 텍스트 → Claude API (AI 요약)
- Google (미국): 계정 인증, Google Drive 백업
- 토스페이먼츠 (한국): 결제 처리

4. 보관 기간
- 회원 정보: 탈퇴 시까지 (즉시 삭제)
- 중개사 추가 정보: Agent 해지 또는 탈퇴 시까지
- Proptalk 음성/STT/요약: 24시간 후 자동 삭제
- 결제 기록: 5년 (전자상거래법)
- 접속 로그: 3개월 (통신비밀보호법)

5. 이용자 권리
- 개인정보 열람, 정정/삭제, 처리 정지 요구 가능
- 회원 탈퇴 시 모든 정보 즉시 삭제

6. 안전성 확보
- 인증 토큰 암호화, HTTPS 전송, 접근 권한 최소화

7. 개인정보 보호 책임자
- 운영자: 프롭넷 (PropNet)
- 이메일: cs21.jeon@gmail.com

8. 권익 침해 구제
- 개인정보침해 신고센터: 118 / privacy.kisa.or.kr
- 개인정보 분쟁조정위원회: 1833-6972 / kopico.go.kr

본 방침은 2026년 4월 3일부터 적용됩니다.
''';

  /// 개인정보 수집 항목 요약 (회원가입 화면용)
  static const String privacySummary = '''
[수집하는 개인정보]
- 필수: 이메일, 이름, 프로필 사진 (Google 계정)
- 중개사 추가: 사무소명, 등록번호, 사업자번호, 대표자명, 소재지

[수집 목적]
- 회원 식별 및 서비스 제공
- 검색 기록/즐겨찾기 관리
- 중개사 인증 및 Agent 서비스 제공

[보유 기간]
- 회원 탈퇴 시까지 (즉시 삭제)
- 중개사 정보: Agent 해지 또는 탈퇴 시까지
''';

  /// 개인정보 국외 이전 동의
  static const String overseasTransfer = '''
개인정보 국외 이전 동의

PropNet 서비스 제공을 위해 아래와 같이 개인정보를 국외로 이전합니다.

1. Google LLC (미국)
   - 이전 항목: OAuth 인증 정보
   - 이전 목적: Google 계정 로그인 인증
   - 보유 기간: Google 개인정보 처리방침에 따름

2. 공공데이터 포털 (한국)
   - 이전 항목: 조회 요청 주소 정보
   - 이전 목적: 건축물대장, 토지대장 정보 조회
   - 보유 기간: API 호출 시 즉시 처리

3. OpenAI, Inc. (미국) - Proptalk 이용 시
   - 이전 항목: 음성 파일
   - 이전 목적: Whisper API를 통한 음성-텍스트 변환(STT)
   - 보유 기간: 처리 즉시 삭제

4. Anthropic, PBC (미국) - Proptalk 이용 시
   - 이전 항목: STT 변환 텍스트
   - 이전 목적: Claude API를 통한 AI 요약
   - 보유 기간: 처리 즉시 삭제

위 업체들은 각각의 보안 체계(TLS 암호화, 접근 통제 등)를 통해 데이터를 보호합니다.

동의를 거부하실 수 있으나, 거부 시 해당 기능의 이용이 제한됩니다.

문의: cs21.jeon@gmail.com
''';
}

/// PropNet 법적 문서 (앱 내장용)
/// 웹 버전: https://propnet.kr/proptalk/privacy
/// 웹 버전: https://propnet.kr/proptalk/terms
/// 통합 법적 문서: https://propnet.kr/legal/*

class AppTerms {
  /// 약관 버전 (통합 인증 시스템 적용)
  static const String currentVersion = '2026-04-03';

  // --- PropNet 통합 URL ---
  static const String privacyPolicyUrl =
      'https://propnet.kr/proptalk/privacy';
  static const String termsOfServiceUrl =
      'https://propnet.kr/proptalk/terms';
  static const String billingTermsUrl =
      'https://propnet.kr/proptalk/payment-terms';

  // --- 통합 법적 문서 URL ---
  static const String legalTermsUrl =
      'https://propnet.kr/legal/terms';
  static const String legalPrivacyUrl =
      'https://propnet.kr/legal/privacy';
  static const String legalOverseasUrl =
      'https://propnet.kr/legal/overseas-transfer';

  /// 동의 타입별 웹 URL 매핑
  static String? getWebUrlForType(String type) {
    switch (type) {
      case 'terms':
        return termsOfServiceUrl;
      case 'privacy':
        return privacyPolicyUrl;
      case 'overseas_transfer':
        return legalOverseasUrl;
      default:
        return null;
    }
  }

  /// 동의 타입별 전문 텍스트 매핑
  static String? getFullTextForType(String type) {
    switch (type) {
      case 'terms':
        return termsOfServiceFull;
      case 'privacy':
        return privacyPolicyFull;
      case 'overseas_transfer':
        return overseasTransferFull;
      case 'proptalk_voice_data':
        return audioUploadConsent;
      default:
        return null;
    }
  }

  /// 동의 타입별 부제 텍스트
  static String? getSubtitleForType(String type) {
    switch (type) {
      case 'privacy':
        return '음성 파일, STT 변환 텍스트, AI 요약 결과 등';
      case 'overseas_transfer':
        return 'OpenAI(미국), Anthropic(미국), Google(미국)에 데이터 전송';
      case 'proptalk_voice_data':
        return '음성 파일 업로드, STT 변환, AI 요약 처리';
      default:
        return null;
    }
  }

  // ── 개인정보 처리방침 (요약) ──

  static const String privacyPolicySummary = '''
[개인정보 수집 및 이용 동의]

1. 수집 항목
 - 필수: 이메일, 이름, 프로필 사진 (Google 계정 연동)
 - Google OAuth 인증 토큰 (Google Drive 백업 연동용)
 - Proptalk 이용 시: 음성 파일, STT 변환 텍스트, AI 요약 결과, 파일명 내 메타데이터
 - 중개사(Agent) 추가: 사무소명, 중개사등록번호, 사업자등록번호, 대표자명, 소재지
 - 자동 수집: 기기 정보, IP 주소, 접속 일시

2. 수집 목적
 - 회원 식별 및 서비스 제공
 - Proptalk: 음성-텍스트 변환(STT) 및 AI 요약
 - Propsheet: 부동산 데이터베이스 관리
 - PropMap: 중개사 홈페이지 및 매물 지도
 - 중개사 인증 및 Agent 서비스 제공

3. 제3자 제공
 - OpenAI (미국): 음성 파일 → Whisper API (STT 변환)
 - Anthropic (미국): 변환 텍스트 → Claude API (AI 요약)
 - Google (미국): 계정 인증, Google Drive 음성 파일 백업
 - 토스페이먼츠 (한국): 결제 처리

4. 보관 기간
 - 회원 정보: 탈퇴 시까지
 - 중개사 추가 정보: Agent 해지 또는 탈퇴 시까지
 - 음성 파일/STT/요약: 업로드 후 24시간 자동 삭제
 - Propsheet 매물 데이터: 서비스 해지 또는 탈퇴 시까지

5. 이용자 권리
 - 개인정보 열람, 정정, 삭제, 처리 정지 요구 가능
 - 회원 탈퇴 시 모든 정보 즉시 삭제

문의: cs21.jeon@gmail.com
전문: $privacyPolicyUrl
''';

  // ── 이용약관 (요약) ──

  static const String termsOfServiceSummary = '''
[PropNet 서비스 이용약관 요약]

1. 서비스 내용
 - Proppedia: 건축물대장, 토지대장, 공시가격 조회 (무료)
 - Proptalk: 음성-텍스트 변환(STT), AI 요약, 팀 채팅
 - Propsheet: 부동산 데이터베이스 관리 (Agent 요금제 포함)
 - PropMap: 중개사 매물 지도 홈페이지 (Agent 요금제 포함)

2. 이용 요금
 - 무료 체험: 최초 가입 시 10분 무료 (계정당 1회)
 - 시간팩: 1시간 4,900원 / 10시간 19,900원 (만료 없음)
 - 월정액: Basic 29,900원 / Pro 79,900원 (매월 자동 결제)
 - Agent: Regular 9,900원 / Basic 29,900원 / Pro 79,900원 (Propsheet+PropMap 포함)

3. 회원 유형
 - 일반 회원: Google 계정으로 가입
 - 중개사 회원(Agent): 사무소명, 등록번호, 사업자번호 등 추가 제공

4. 회원의 의무
 - 적법하게 녹음된 음성 파일만 업로드
 - 중개사 정보 정확성 유지 및 매물 정보 책임

5. 면책 사항
 - STT 및 AI 요약의 정확성 미보장
 - 부동산 정보는 참고 목적 (법적 효력 없음)
 - 24시간 후 삭제된 데이터 복구 불가

문의: cs21.jeon@gmail.com
전문: $termsOfServiceUrl
''';

  // ── 개인정보 처리방침 (전문) ──

  static const String privacyPolicyFull = '''
개인정보 처리방침

시행일: 2026년 4월 3일

프롭넷(이하 "회사")은 PropNet 서비스(Proppedia, Proptalk, Propsheet, PropMap 등 회사가 운영하는 모든 서비스를 포함하며, 이하 "서비스")를 운영함에 있어 「개인정보 보호법」 및 관련 법령을 준수하며, 이용자의 개인정보를 보호하기 위해 다음과 같이 개인정보 처리방침을 수립합니다.

제1조 (수집하는 개인정보 항목)

1. 회원가입 시 수집 항목 (전체 회원)
 - 필수: 이메일 주소, 이름, 프로필 사진 (Google 계정 연동)
 - Google OAuth 인증 토큰 (Google Drive 백업 연동용)
 - 자동 수집: 기기 정보, IP 주소, 접속 일시, 앱 버전

2. 중개사(Agent) 회원 추가 수집 항목
 - 필수: 사무소명(상호), 중개사등록번호, 사업자등록번호, 대표자명, 사무소 소재지
 - 선택: 사무소 전화번호
 수집 목적: 중개사 자격 확인, Propsheet/PropMap 서비스 제공, 홈페이지 생성

3. 서비스 이용 과정에서 수집되는 항목
 - Proptalk: 음성 파일, STT 변환 결과, AI 요약, 채팅 메시지 → 24시간 후 자동 삭제
 - Proptalk: Google Drive 저장 파일 → 이용자가 직접 삭제 시까지
 - Proppedia: 부동산 검색 기록, 즐겨찾기 → 회원 탈퇴 시까지
 - Propsheet: 매물 데이터 → 서비스 해지 또는 탈퇴 시까지
 - PropMap: 매물 게시 정보 → 서비스 해지 또는 탈퇴 시까지

제2조 (개인정보의 수집 및 이용 목적)

 1) 회원 관리: 회원 식별, 로그인 인증, 서비스 이용 자격 확인
 2) 서비스 제공: Proppedia 부동산 조회, Proptalk STT/AI 요약/채팅, Propsheet 데이터 관리, PropMap 홈페이지
 3) 중개사 인증: 공인중개사 자격 확인 및 Agent 서비스 제공
 4) 서비스 개선: 이용 통계 분석, 서비스 품질 향상
 5) 고객 지원: 문의 대응, 공지사항 전달
 6) 요금 결제: 유료 서비스 이용 시 결제 처리 및 환불

제3조 (개인정보의 제3자 제공)

 - OpenAI, Inc. (미국): 음성 파일 → Whisper API를 통한 음성-텍스트 변환
 - Anthropic, PBC (미국): 변환 텍스트 → Claude API를 통한 대화 내용 요약
 - Google LLC (미국): OAuth 인증, Google Drive 음성 파일 백업 (OAuth 인증 토큰 저장)
 - 주식회사 토스페이먼츠 (한국): 결제 처리 (카드번호는 당사 서버에 저장하지 않음)
 - 국토교통부 VWorld API (한국): 주소 → 좌표 변환 (지오코딩)

이 외에 이용자의 개인정보를 제3자에게 제공하지 않습니다.
단, 이용자 사전 동의, 법령 요구, 수사 목적의 적법한 요청은 예외입니다.

제4조 (개인정보의 보유 및 이용 기간)

 - 회원 정보: 회원 탈퇴 시까지 (탈퇴 즉시 삭제)
 - 중개사 추가 정보: Agent 해지 또는 탈퇴 시까지
 - 음성 파일, STT 결과, AI 요약, 채팅: 24시간 후 자동 삭제 (복구 불가)
 - Propsheet 매물 데이터: 서비스 해지 또는 탈퇴 시까지
 - 결제 기록: 5년 (전자상거래법)
 - 접속 로그: 3개월 (통신비밀보호법)

제5조 (개인정보의 파기)

 - 전자적 파일: 복구 불가능한 방법으로 영구 삭제
 - Proptalk 음성 파일: 서버에서 24시간 자동 삭제 스케줄에 의해 완전 삭제

제6조 (이용자의 권리)

 1) 개인정보 열람, 정정/삭제, 처리 정지 요구 가능
 2) 회원 탈퇴 시 모든 정보 즉시 삭제

권리 행사: cs21.jeon@gmail.com

제7조 (안전성 확보 조치)

 1) 인증 토큰 암호화 저장
 2) HTTPS(TLS) 전송 암호화
 3) 접근 권한 최소화
 4) Proptalk 음성 데이터 24시간 후 자동 삭제

제8조 (국외 이전)

 - OpenAI, Inc. → 미국 (음성 파일, STT 변환)
 - Anthropic, PBC → 미국 (변환 텍스트, AI 요약)
 - Google LLC → 미국 (인증, Drive 백업)

제9조 (개인정보 보호 책임자)

 - 운영자: 프롭넷 (PropNet)
 - 이메일: cs21.jeon@gmail.com

제10조 (처리방침 변경)

법령, 정책 또는 서비스 변경 시 수정될 수 있으며, 변경 시 앱 내 공지합니다.

제11조 (권익 침해 구제)

 - 개인정보침해 신고센터: 118 / privacy.kisa.or.kr
 - 개인정보 분쟁조정위원회: 1833-6972 / kopico.go.kr
 - 대검찰청 사이버수사과: 1301 / spo.go.kr
 - 경찰청 사이버수사국: 182 / ecrm.police.go.kr
''';

  // ── 이용약관 (전문) ──

  static const String termsOfServiceFull = '''
서비스 이용약관

시행일: 2026년 4월 3일

제1조 (목적)

이 약관은 프롭넷(이하 "회사")이 제공하는 PropNet 서비스(이하 "서비스")의 이용과 관련하여 회사와 이용자 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.

제2조 (정의)

 1) "서비스"란 회사가 PropNet 브랜드로 제공하는 다음의 서비스를 포함한 모든 기능을 말합니다.
    - Proppedia: 건축물대장, 토지대장, 공시가격 등 부동산 정보 조회 서비스
    - Proptalk: 음성-텍스트 변환(STT), AI 요약, 팀 채팅 서비스
    - Propsheet: 부동산 데이터베이스 관리 서비스
    - PropMap: 중개사별 매물 지도 및 홈페이지 서비스
 2) "회원"이란 서비스에 가입하여 이용 계약을 체결한 자를 말합니다.
 3) "일반 회원"이란 Google 계정으로 가입한 개인 이용자를 말합니다.
 4) "중개사 회원(Agent)"이란 공인중개사 자격을 보유하고 중개사 인증을 완료한 회원을 말합니다.
 5) "음성 파일"이란 이용자가 Proptalk에 업로드하는 통화 녹음, 음성 메모 등 오디오 파일을 말합니다.

제3조 (약관의 효력 및 변경)

 1) 이 약관은 서비스 화면에 게시하거나 공지함으로써 효력이 발생합니다.
 2) 회사는 관련 법령을 위배하지 않는 범위에서 약관을 개정할 수 있으며, 변경 시 7일 전부터 공지합니다.
 3) 이용자가 변경된 약관에 동의하지 않을 경우 서비스 이용을 중단하고 탈퇴할 수 있습니다.

제4조 (서비스의 내용)

 - Proppedia: 건축물/토지/공시가격 조회, 검색, 즐겨찾기, PDF 저장 (무료)
 - Proptalk: 음성-텍스트 변환(STT), AI 요약, 채팅방, Google Drive 백업, 24시간 자동 삭제
 - Propsheet: 매물 데이터베이스 관리, 뷰/필터, CSV, 권한 관리 (Agent 요금제 포함)
 - PropMap: 중개사별 매물 지도 홈페이지, 매물 검색, 공유 링크 (Agent 요금제 포함)

제5조 (이용 요금 및 결제)

1. 일반 사용자 요금제
 - 무료 체험: 10분 (계정당 1회)
 - 1시간 팩: 4,900원 (일회성, 만료 없음)
 - 10시간 팩: 19,900원 (일회성, 만료 없음)
 - Basic 30시간: 29,900원/월 (초과 시 12원/분)
 - Pro 90시간: 79,900원/월 (초과 시 12원/분)

2. 중개사(Agent) 요금제 — Proptalk + Propsheet + PropMap 포함
 - Agent Regular: 9,900원/월 (60분, 초과 시 12원/분)
 - Agent Basic: 29,900원/월 (1,800분, 초과 시 12원/분)
 - Agent Pro: 79,900원/월 (5,400분, 초과 시 12원/분)

3. 결제 및 환불
 - 결제: 토스페이먼츠를 통한 웹 결제 (신용/체크카드)
 - 환불: 미이용 시 7일 이내 전액 환불, 일부 이용 시 잔여분 환불
 - 환불 요청: cs21.jeon@gmail.com

제6조 (회원 가입 및 회원 유형)

 1) 이용자는 Google 계정을 통해 가입할 수 있습니다.
 2) 중개사 회원 가입 시 사무소명, 중개사등록번호, 사업자등록번호, 대표자명, 소재지를 추가 제공해야 합니다.
 3) 허위 정보 기재 시 중개사 자격이 취소되고 서비스 이용이 제한됩니다.
 4) 회원은 언제든지 탈퇴할 수 있으며, 탈퇴 시 모든 정보가 즉시 삭제됩니다.

제7조 (회원의 의무)

 [중요] 적법하게 녹음된 음성 파일만 업로드해야 합니다. 불법 녹음물 업로드의 법적 책임은 이용자에게 있습니다.

 1) 「통신비밀보호법」 등 관련 법령 준수
 2) 타인의 개인정보, 프라이버시, 저작권 침해 금지
 3) 중개사 회원은 사무소 정보 정확성 유지 및 매물 정보 책임
 4) 계정 양도/공유 금지

제8조 (면책 조항)

 1) STT 결과 및 AI 요약의 정확성 미보장
 2) 부동산 정보는 공공데이터 기반 참고 자료 (법적 효력 없음)
 3) 24시간 자동 삭제된 데이터 복구 불가
 4) PropMap 매물 정보의 정확성 책임은 해당 중개사 회원에게 있음
 5) 외부 서비스(OpenAI, Anthropic, Google 등) 장애에 대해 책임 없음

제9조 (분쟁 해결)

 대한민국 법률을 준거법으로 하며, 합의 불가 시 관할 법원에 제소합니다.

부칙
이 약관은 2026년 4월 3일부터 시행됩니다.
2026년 3월 1일자 이전 약관은 이 약관으로 대체됩니다.
''';

  // ── 결제 약관 요약 ──

  static const String billingTermsSummary = '''
[PropNet 결제 및 환불 안내]

1. 일반 요금제
 - 무료 체험: 계정당 10분 (평생)
 - 1시간 팩: 4,900원 (만료 없음)
 - 10시간 팩: 19,900원 (만료 없음)
 - Basic 30시간: 29,900원/월 (자동결제)
 - Pro 90시간: 79,900원/월 (자동결제)

2. 중개사(Agent) 요금제 — Propsheet + PropMap 포함
 - Agent Regular: 9,900원/월
 - Agent Basic: 29,900원/월
 - Agent Pro: 79,900원/월

3. 결제 방법
 - 토스페이먼츠를 통한 신용/체크카드 결제
 - 월정액 상품은 등록된 카드로 매월 자동 결제

4. 환불 정책
 - 미이용 시 결제일로부터 7일 이내 전액 환불
 - 일부 이용 시 잔여분 환불
 - 환불 요청: cs21.jeon@gmail.com
''';

  // ── 음성 데이터 동의 (첫 업로드 시 표시) ──

  static const String audioUploadConsent = '''
[음성 데이터 처리 동의]

업로드하신 음성 파일은 다음과 같이 처리됩니다:

1. 음성 파일이 OpenAI 서버(미국)로 전송되어 텍스트로 변환됩니다.
2. 변환된 텍스트가 Anthropic 서버(미국)로 전송되어 AI 요약이 생성됩니다.
3. 음성 파일이 채팅방 방장의 Google Drive에 백업 저장됩니다.
4. 서버의 음성 파일, 변환 텍스트, AI 요약은 업로드 후 24시간 이내에 자동 삭제됩니다.

[중요] 적법하게 녹음된 파일만 업로드해 주세요. 불법 녹음물 업로드의 법적 책임은 이용자에게 있습니다.

동의하시면 '동의' 버튼을 눌러주세요.
''';

  // ── 국외 이전 동의 (전문) ──

  static const String overseasTransferFull = '''
개인정보 국외 이전 동의

PropNet 서비스 제공을 위해 아래와 같이 개인정보를 국외로 이전합니다.

1. OpenAI, Inc. (미국)
   - 이전 항목: 음성 파일
   - 이전 목적: Whisper API를 통한 음성-텍스트 변환(STT)
   - 보유 기간: 처리 즉시 삭제 (OpenAI는 API 데이터를 학습에 사용하지 않음)

2. Anthropic, PBC (미국)
   - 이전 항목: STT 변환 텍스트
   - 이전 목적: Claude API를 통한 대화 내용 AI 요약
   - 보유 기간: 처리 즉시 삭제

3. Google LLC (미국)
   - 이전 항목: 인증 정보, 음성 파일 (Drive 백업 시)
   - 이전 목적: OAuth 로그인 인증, Google Drive 파일 백업
   - 보유 기간: Drive 백업 파일은 사용자가 직접 관리

위 업체들은 각각의 보안 체계(TLS 암호화, 접근 통제 등)를 통해 데이터를 보호합니다.

동의를 거부하실 수 있으나, 거부 시 음성 변환 및 AI 요약 기능을 이용할 수 없습니다.

문의: cs21.jeon@gmail.com
''';
}

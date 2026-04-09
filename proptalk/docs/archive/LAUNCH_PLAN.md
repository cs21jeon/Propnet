# Proptalk 앱 출시 계획

> 최종 업데이트: 2026-03-04 (결제 시스템 구현 완료)

## 앱 개요

| 항목 | 내용 |
|------|------|
| 앱 이름 | Proptalk |
| 패키지 ID | `biz.goldenrabbit.proptalk` |
| 버전 | 1.0.0+1 |
| 슬로건 | "세상 쉬운 업무 공유" |
| 핵심 기능 | 통화 녹음 업로드 → Whisper STT → Claude 요약 → 자동 댓글 |
| 타겟 사용자 | 부동산 중개사, 보험 설계사, 영업직 등 통화 녹음 관리가 필요한 직군 |
| 수익 모델 | 프리미엄 (무료 10분 → 시간팩/월구독, 토스페이먼츠 웹결제) |
| 운영 주체 | 금토끼부동산 (cs21.jeon@gmail.com) |
| 서버 | goldenrabbit.biz (Cafe24) |
| GitHub | https://github.com/cs21jeon/Proptalk |

---

## 진행현황

### Phase 1: 법적 문서 ✅ 완료

| 항목 | 상태 | 파일 경로 | 비고 |
|------|------|-----------|------|
| 개인정보 처리방침 (HTML) | ✅ | `marketing/proptalk/privacy-policy.html` | 웹 배포용 |
| 이용약관 (HTML) | ✅ | `marketing/proptalk/terms-of-service.html` | 웹 배포용 |
| Flutter 앱 내장 (terms.dart) | ✅ | `flutter/lib/constants/terms.dart` | 요약 + 전문 + 음성 동의 |
| 서버 배포 | 🔲 | → `goldenrabbit.biz/proptalk/privacy-policy.html` | 서버 업로드 필요 |
| 서버 배포 | 🔲 | → `goldenrabbit.biz/proptalk/terms-of-service.html` | 서버 업로드 필요 |

#### 반영된 법적 조항

- 통신비밀보호법: 적법 녹음물만 업로드 의무, 면책 조항
- 개인정보보호법: 수집 항목, 이용 목적, 보관 기간, 이용자 권리
- 제3자 제공: OpenAI (Whisper STT), Anthropic (Claude 요약), Google (OAuth, Drive)
- 국외 이전: 미국 서버 전송 고지
- 24시간 자동 삭제: 서버 데이터 보관 정책
- Google Drive 백업: Drive 소유자 직접 관리 책임
- 프리미엄 모델: 무료 10분 + 시간팩/월구독, 결제/환불 조항
- 결제/환불 약관: billing-terms.html (토스페이먼츠, 자동결제, 환불 정책)
- 전자상거래법: 결제 전 가격(VAT) 명시, 7일 청약철회, 결제 로그 5년 보관
- 토스페이먼츠 제3자 제공: 개인정보처리방침에 고지 완료
- 음성 데이터 동의서: 첫 업로드 시 표시 (`audioUploadConsent`)

---

### Phase 2: 앱 완성도 🔄 진행중

| 항목 | 상태 | 비고 |
|------|------|------|
| 전체 플로우 테스트 | ✅ | 업로드 → STT → 요약 → 댓글 (서버 테스트 완료) |
| Google Drive 연동 구현 | ✅ | 코드 완료, 앱 테스트 진행 중 |
| 3GP/AMR 포맷 자동 변환 | ✅ | ffprobe + ffmpeg |
| 마크다운 요약 렌더링 | ✅ | flutter_markdown |
| MANAGE_EXTERNAL_STORAGE 권한 | ✅ | AndroidManifest + 권한 요청 UI |
| **서비스 동의 화면** | ✅ | **약관/개인정보/국외이전 3항목 필수 동의** |
| **음성 데이터 동의 팝업** | ✅ | **첫 업로드 시 표시, DB + SharedPreferences** |
| **접속기록 감사 로그** | ✅ | **access_logs, 3개월 보관 자동 삭제** |
| **RBAC 권한 강화** | ✅ | **admin/member 역할 데코레이터 적용** |
| **회원 탈퇴 + 동의 철회** | ✅ | **설정 화면에서 가능, CASCADE 삭제** |
| **앱 내 법적 문서 열람** | ✅ | **로그인 화면 + 설정 화면 링크** |
| **설정 화면** | ✅ | **법적 문서, 동의 관리, 계정 삭제, 로그아웃** |
| **결제 시스템 (토스페이먼츠)** | ✅ | **서버+앱+웹 전체 구현 완료 (2026-03-04)** |
| **결제 DB + API 9개** | ✅ | **billing_plans/user_billing/payment_transactions/usage_logs** |
| **결제 웹페이지 5개** | ✅ | **요금제/결제/성공/실패/구독관리 + Nginx 프록시** |
| **자동결제 크론** | ✅ | **구독갱신(03:00)/만료처리(04:00)/주문정리(매시간)** |
| **Flutter 결제 UI** | ✅ | **BillingService + BillingScreen + 잔액확인 다이얼로그** |
| **결제 약관** | ✅ | **billing-terms.html + 이용약관/처리방침 업데이트** |
| 토스 테스트 키 연동 | 🔲 | 사업자등록 → 토스 가입 → 테스트 키 발급 |
| 결제 전체 플로우 테스트 | 🔲 | 요금제 선택 → 결제 → 시간 충전 → 업로드 차감 |
| 에러 핸들링 강화 | 🔲 | |
| Google OAuth 동의화면 프로덕션 전환 | 🔲 | 현재 테스트 모드 (100명 제한) |
| `MANAGE_EXTERNAL_STORAGE` Google Play 심사 | 🔲 | Google Play 정책 별도 심사 |
| 앱 아이콘/스플래시 스크린 최종화 | 🔲 | |

---

### Phase 3: 랜딩페이지 🔲

| 항목 | 상태 | 비고 |
|------|------|------|
| 필요 자료 수집 | 🔲 | 아래 "필요 자료" 참고 |
| 랜딩페이지 HTML 제작 | 🔲 | `marketing/proptalk/index.html` |
| 서버 배포 | 🔲 | `goldenrabbit.biz/proptalk/` |
| OG 이미지 제작 (1200x630) | 🔲 | 소셜 공유용 |
| SEO 설정 | 🔲 | canonical, OG, Schema.org |
| sitemap.xml 업데이트 | 🔲 | proptalk 경로 추가 |
| robots.txt 업데이트 | 🔲 | |
| Google Search Console 등록 | 🔲 | |
| 네이버 서치어드바이저 등록 | 🔲 | |

#### 필요 자료

| 카테고리 | 항목 | 상태 |
|----------|------|------|
| 브랜딩 | 앱 아이콘 (고해상도 512x512) | ✅ 있음 |
| 브랜딩 | 로고 이미지 | 확인 필요 |
| 브랜딩 | 슬로건 "세상 쉬운 업무 공유" | ✅ 있음 |
| 브랜딩 | 브랜드 컬러 #1A73E8 | ✅ 있음 |
| 스크린샷 | 로그인 화면 | 🔲 촬영 필요 |
| 스크린샷 | 채팅방 목록 | 🔲 촬영 필요 |
| 스크린샷 | 음성 업로드 과정 | 🔲 촬영 필요 |
| 스크린샷 | STT 변환 결과 (자동 댓글) | 🔲 촬영 필요 |
| 스크린샷 | Claude 요약 결과 | 🔲 촬영 필요 |
| 텍스트 | 기능 소개 문구 (3~5개) | 🔲 작성 필요 |
| 텍스트 | FAQ | 🔲 작성 필요 |
| 배포 | OG 이미지 (1200x630) | 🔲 제작 필요 |
| 배포 | Favicon | 확인 필요 |

#### 랜딩페이지 섹션 구성 (안)

```
1. Hero Section
   - 메인 카피: "통화 녹음, 올리면 끝"
   - 서브 카피: "AI가 알아서 텍스트로 바꾸고, 요약까지"
   - CTA: Google Play 다운로드 버튼
   - 폰 목업 이미지

2. Pain Point Section
   - "이런 불편, 겪어보셨나요?"
   - 녹음 파일 쌓여만 가는 문제
   - 일일이 다시 듣는 시간 낭비
   - 팀원과 공유가 어려운 문제

3. Solution / Features Section (핵심 3가지)
   - 음성→텍스트 자동 변환 (Whisper)
   - AI 자동 요약 (Claude)
   - 팀 채팅방 공유

4. How it Works (사용 플로우)
   - Step 1: 채팅방 만들기
   - Step 2: 녹음 파일 업로드
   - Step 3: AI가 자동으로 텍스트 변환 + 요약
   - Step 4: 팀원과 즉시 공유

5. Screenshots Section
   - 실제 앱 스크린샷 캐러셀

6. Security & Privacy Section
   - 24시간 자동 삭제
   - 암호화 전송
   - Google 계정 인증

7. CTA Section
   - 다운로드 버튼
   - "지금 무료로 시작하세요"

8. Footer
   - 개인정보 처리방침 / 이용약관 링크
   - 문의: cs21.jeon@gmail.com
   - © 금토끼부동산
```

---

### Phase 4: Google Play 등록 🔲

| 항목 | 상태 | 비고 |
|------|------|------|
| Google Play Console 등록 | 🔲 | $25 일회성 (기존 계정 있으면 생략) |
| 앱 스크린샷 5~8장 | 🔲 | 폰 스크린샷 |
| Feature Graphic (1024x500) | 🔲 | 스토어 상단 배너 |
| 앱 설명문 (한국어) | 🔲 | 간략 설명 + 상세 설명 |
| Data Safety 섹션 작성 | 🔲 | 수집 데이터 상세 기입 |
| 개인정보 처리방침 URL 등록 | 🔲 | goldenrabbit.biz/proptalk/privacy-policy.html |
| 앱 카테고리 선택 | 🔲 | 비즈니스 또는 생산성 |
| 콘텐츠 등급 설문 작성 | 🔲 | |
| `MANAGE_EXTERNAL_STORAGE` 별도 심사 | 🔲 | Google Play 정책 |
| Release APK/AAB 업로드 | 🔲 | AAB(App Bundle) 권장 |
| 내부 테스트 → 비공개 → 프로덕션 | 🔲 | 단계별 출시 |

#### Data Safety 섹션 작성 가이드

| 데이터 유형 | 수집 여부 | 공유 여부 | 용도 |
|-------------|-----------|-----------|------|
| 이메일 주소 | 예 | 아니오 | 계정 관리 |
| 이름 | 예 | 아니오 | 앱 기능 |
| 프로필 사진 | 예 | 아니오 | 앱 기능 |
| 음성/오디오 파일 | 예 | 예 (OpenAI, Google Drive) | 앱 기능 |
| 기기 정보 | 예 | 아니오 | 분석 |

---

### Phase 5: 마케팅 🔲

| 항목 | 상태 | 비고 |
|------|------|------|
| 블로그 SEO 콘텐츠 | 🔲 | 키워드: "통화 녹음 텍스트 변환", "부동산 상담 녹음 관리" |
| 네이버 카페 홍보 | 🔲 | 부동산 중개사 커뮤니티 |
| Google Play ASO | 🔲 | 스토어 키워드 최적화 |
| 인스타그램/SNS | 🔲 | 사용 시나리오 릴스/카드뉴스 |

#### 타겟 사용자

| 순위 | 타겟 | 이유 |
|------|------|------|
| 1 | 부동산 중개사 | 상담 통화 녹음이 핵심 업무 |
| 2 | 보험 설계사 | 고객 상담 녹음 관리 필요 |
| 3 | 영업/세일즈 직군 | 통화 기록 관리 니즈 |
| 4 | 소규모 팀/사무실 | 팀 내 음성 기록 공유 |

---

## 법적 고려사항 요약

### 통신비밀보호법 (핵심 리스크)

| 쟁점 | 대응 |
|------|------|
| 녹음 동의 | 약관에 "적법 녹음물만 업로드" 의무 + 면책 조항 |
| 제3자 공유 | 채팅방 공유 시 경고 문구 + 약관 명시 |
| 서버 저장 | 24시간 자동 삭제 정책 고지 |

### 개인정보보호법 (PIPA)

| 항목 | 조치 |
|------|------|
| Google 계정 정보 | 개인정보 처리방침에 수집 항목 명시 ✅ |
| 음성 파일 | 별도 동의 화면 (audioUploadConsent) ✅ 구현 |
| 전화번호 (파일명 파싱) | 개인정보 처리 고지 ✅ |
| OpenAI/Anthropic 전송 | 제3자 제공 + 국외 이전 동의 ✅ consent_screen |
| 동의 이력 DB 저장 | user_consents 테이블 ✅ 구현 |
| 접속기록 감사 로그 | access_logs 테이블 (3개월 보관) ✅ 구현 |
| RBAC 권한 강화 | admin/member 데코레이터 ✅ 구현 |
| 회원 탈퇴 | CASCADE 삭제 + 설정 화면 ✅ 구현 |
| 동의 철회 | 설정 화면에서 개별 철회 ✅ 구현 |

### 앱 스토어 정책

| 플랫폼 | 주의 사항 |
|--------|-----------|
| Google Play | `MANAGE_EXTERNAL_STORAGE` 별도 심사, Data Safety 상세 작성, 개인정보 처리방침 URL 필수 |
| App Store | 녹음 관련 앱 심사 엄격, App Privacy Labels, IDFA 고지 |

### 제3자 API 이용약관

| API | 확인 사항 |
|-----|-----------|
| OpenAI | 음성 데이터 전송 시 사용자 동의 확보, 비즈니스 약관 준수 |
| Anthropic | Claude API 상업적 사용 가능 여부, 출력물 표시 가이드라인 |
| Google OAuth | 사용자 100명 초과 시 앱 인증 검수 필요 |

---

## 추천 실행 일정

| 주차 | 작업 | 산출물 |
|------|------|--------|
| **1주차** | ~~법적 문서 작성~~ ✅ + ~~법적 컴플라이언스 구현~~ ✅ + ~~결제 시스템 구현~~ ✅ | 동의, RBAC, 결제, 약관 |
| **2주차** | 토스 테스트 키 연동 + 결제 실테스트 + 스크린샷 + 랜딩페이지 | 결제 검증 + 랜딩페이지 |
| **3주차** | Google Play Console 등록 + 심사 제출 | APK/AAB 심사 제출 |
| **4주차** | SEO/ASO + 커뮤니티 초기 마케팅 | 출시 + 초기 사용자 확보 |

---

## 파일 구조

```
Proptalk/
├── docs/
│   ├── ARCHITECTURE.md          # 시스템 아키텍처
│   ├── SETUP_GUIDE.md           # 설치 가이드
│   ├── PROGRESS.md              # 개발 진행 현황
│   └── LAUNCH_PLAN.md           # 출시 계획 (이 파일)
│
├── marketing/
│   └── proptalk/
│       ├── privacy-policy.html  # 개인정보 처리방침 (웹)
│       ├── terms-of-service.html # 이용약관 (웹)
│       ├── billing-terms.html   # 결제/환불 약관 (웹) ✅ 신규
│       └── index.html           # 랜딩페이지 (예정)
│
├── flutter/
│   └── lib/
│       └── constants/
│           └── terms.dart       # 법적 문서 (앱 내장)
│
└── server/
    └── ...
```

---

## 서버 배포 명령어 (법적 문서)

```bash
# 디렉토리 생성
ssh root@175.119.224.71 "mkdir -p /home/webapp/goldenrabbit/frontend/public/proptalk"

# 파일 업로드
scp marketing/proptalk/privacy-policy.html root@175.119.224.71:/home/webapp/goldenrabbit/frontend/public/proptalk/
scp marketing/proptalk/terms-of-service.html root@175.119.224.71:/home/webapp/goldenrabbit/frontend/public/proptalk/

# 권한 설정
ssh root@175.119.224.71 "chown -R www-data:www-data /home/webapp/goldenrabbit/frontend/public/proptalk && chmod -R 755 /home/webapp/goldenrabbit/frontend/public/proptalk"

# 확인
curl https://goldenrabbit.biz/proptalk/privacy-policy.html
curl https://goldenrabbit.biz/proptalk/terms-of-service.html
```

---

## 참고 자료

- Proppedia 마케팅 이력: `C:\Users\ant19\projects\propedia\docs\marketing-deployment.md`
- Proppedia 랜딩페이지: https://goldenrabbit.biz/proppedia/
- 기존 사이트: https://goldenrabbit.biz/

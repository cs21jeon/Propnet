# Google Play Store 및 AdMob 설정 기록

## 설정 일자: 2026-02-18 ~ 02-20

---

## 1. Google Play Console 설정

### 계정 정보
- **계정 생성**: 완료
- **등록비 결제**: $25 완료
- **앱 이름**: 부동산백과

### 앱 정보
- **패키지 이름**: `com.proppedia.app`
- **최신 버전**: 1.0.2+8 (버전 코드 8)

### 앱 등록 상태
- [x] Play Console 계정 생성
- [x] 앱 생성 (Proppedia)
- [x] 스토어 등록정보 작성
- [x] 앱 설정 완료
- [x] 비공개 테스트 트랙 생성
- [x] AAB 업로드 완료
- [x] 테스터 20명 모집
- [x] 테스터 초대 및 옵트인
- [x] 14일간 테스트 진행
- [x] 프로덕션 출시 (2026-03-08)

---

## 2. AdMob 설정

### 계정 정보
- **AdMob 계정**: 등록 완료
- **앱 이름**: Proppedia

### 광고 단위

| 항목 | 값 |
|------|-----|
| 광고 단위 이름 | Ad_Proppedia |
| 광고 형식 | 배너 |
| 광고 단위 ID | `ca-app-pub-3478991909223100/1393451919` |

### AdMob App ID
- **앱 ID**: `ca-app-pub-3478991909223100~4421163836`

### app-ads.txt 설정 (2026-03-10)
- **파일 위치**: `marketing/app-ads.txt`
- **서버 경로**: `/home/webapp/goldenrabbit/frontend/public/app-ads.txt`
- **URL**: `https://goldenrabbit.biz/app-ads.txt`
- **내용**: `google.com, pub-3478991909223100, DIRECT, f08c47fec0942fa0`
- **배포**: ✅ 완료 (2026-03-10)

### AdMob 앱 인증 상태 (2026-03-10)
- [x] Google Play Store 연결 (스토어 추가)
- [x] app-ads.txt 파일 생성 및 서버 배포
- [ ] AdMob 앱 인증 완료 (app-ads.txt 크롤링 후 자동 처리, 최대 24시간)
- [ ] 광고 게재 제한 해제

---

## 3. Flutter 앱 연동 상태

- [x] google_mobile_ads 패키지 추가
- [x] AndroidManifest.xml에 AdMob App ID 추가
- [x] 배너 광고 위젯 구현 (`lib/presentation/widgets/ads/banner_ad_widget.dart`)
- [x] 광고 서비스 구현 (`lib/core/ads/ad_service.dart`)
- [x] 홈 화면에 배너 광고 추가
- [x] 결과 화면에 배너 광고 추가
- [x] 즐겨찾기 화면에 배너 광고 추가
- [x] 검색기록 화면에 배너 광고 추가
- [x] 테스트 광고 확인 완료
- [x] 릴리즈 빌드 시 실제 광고 ID 자동 적용

---

## 4. 앱 설정 완료 항목

### 개인정보처리방침
- **URL**: `https://goldenrabbit.biz/privacy-policy.html`

### 앱 액세스 권한 (테스트 계정)
- **이메일**: `review@proppedia.com`
- **비밀번호**: `ReviewTest2026!`
- **이름**: Test User

### 데이터 보안
- 필수 데이터 수집: 예
- 암호화 전송: 예 (HTTPS)
- 계정 생성 방법: Google 로그인 (2026-03-08부터 이메일/비밀번호 제거)
- 계정 삭제 URL: `https://goldenrabbit.biz/privacy-policy.html`

### 콘텐츠 등급
- 설문지 작성 완료

### 타겟층
- 설정 완료

---

## 5. 빌드 파일

### 릴리즈 AAB
- **패키지 이름**: `com.proppedia.app`
- **파일 위치**: `build/app/outputs/bundle/release/app-release.aab`
- **파일 크기**: 61.3MB
- **최신 버전**: 1.0.2+8 (버전 코드 8)
- **빌드 일자**: 2026-03-08

### 업데이트 내역
| 버전 | 날짜 | 변경사항 |
|-----|------|---------|
| 1.0.0+1 | 2026-02-19 | 최초 업로드 |
| 1.0.1+2 | 2026-02-20 | 앱 아이콘 변경, 앱 이름 "부동산백과"로 변경 |
| 1.0.2+3 | 2026-02-23 | 대규모 아파트 지원, 대지지분 속도 개선 |
| 1.0.2+4 | 2026-02-24 | VWorld 캐싱, 신규 행정구역 수정 |
| 1.0.2+5 | 2026-02-25 | API 병렬 호출, TTL 캐싱 |
| 1.0.2+6 | 2026-02-26 | 스켈레톤 로딩 UI, 단계별 메시지 |
| 1.0.2+7 | 2026-03-01 | 신규 행정구역 토지정보 조회 |
| 1.0.2+8 | 2026-03-08 | Google 로그인 전환, 프로덕션 출시 |

### 키스토어
- **파일 위치**: `android/app/propedia-release-key.jks`
- **키 설정**: `android/key.properties`

---

## 6. 스토어 등록정보

### 앱 이름
```
부동산백과
```

### 간단한 설명 (80자)
```
건축물대장, 토지대장, 공시지가를 한눈에! 도로명/지번/지도로 부동산 정보를 무료로 조회하세요.
```

### 자세한 설명
```
🏠 Proppedia(부동산백과)는 대한민국 모든 부동산 정보를 한눈에 조회할 수 있는 무료 앱입니다.

📋 주요 기능

▶ 건축물 정보 조회
• 건축물대장 기반의 정확한 건물 정보
• 대지면적, 건축면적, 연면적, 용적률, 건폐율
• 층수, 구조, 주용도, 사용승인일
• 공동주택(아파트, 다세대) 동/호별 전용면적, 공급면적

▶ 토지 정보 조회
• 토지대장 기반의 토지 정보
• 지목, 토지면적, 용도지역
• 공시지가 (기준년도 포함)

▶ 공시가격 조회
• 개별주택가격 (단독주택)
• 공동주택가격 (아파트, 다세대)
• 개별공시지가

▶ 3가지 검색 방식
• 도로명 주소 검색
• 지번 주소 검색
• 지도에서 위치 선택 검색

▶ 편의 기능
• 즐겨찾기 - 관심 부동산 저장
• 검색기록 - 최근 조회 내역 확인
• PDF 저장/공유 - 조회 결과를 PDF로 저장

📍 이런 분들께 추천합니다
• 부동산 투자를 검토하시는 분
• 이사할 집을 알아보시는 분
• 공인중개사, 부동산 관련 종사자
• 건축, 인테리어 관련 업무 종사자
• 부동산 공부를 시작하시는 분

💡 데이터 출처
• 국토교통부 건축물대장
• 국토교통부 토지대장
• 한국부동산원 부동산공시가격
• 공공데이터포털, VWorld

📞 문의
• 이메일: ant1975@hanmail.net
• 제작: 금토끼부동산 (https://goldenrabbit.biz)

※ 본 앱의 정보는 참고용이며, 정확한 내용은 관할 관청의 공적장부를 확인하시기 바랍니다.
```

### 출시노트

**v1.0.2 (8) - 프로덕션 출시 (2026-03-08)**
```
- Google 계정으로 간편 로그인 지원
- 로그인 시 즐겨찾기, 검색기록 자동 동기화
- 스켈레톤 로딩 UI 및 단계별 진행 메시지 추가
- 화성시 등 신규 행정구역 토지정보 조회 지원
- 앱 브랜딩 및 안정성 개선
```

**v1.0.1 (2) - 비공개 테스트 (2026-02-20)**
```
Proppedia 부동산백과 첫 번째 버전입니다.

주요 기능:
• 건축물대장 정보 조회
• 토지대장 정보 조회
• 공시지가/공시가격 조회
• 도로명/지번/지도 검색
• 즐겨찾기 및 검색기록 관리
• PDF 저장 및 공유
```

---

## 7. 스크린샷 및 이미지

### 저장 위치
`C:\Users\ant19\projects\propedia\screenshots\`

### 앱 아이콘
- **원본**: `assets/images/proppedia_logo.png`
- **스토어용**: `screenshots/icon_512x512.png`
- **설정 도구**: `flutter_launcher_icons` 패키지
- **배경색**: 흰색 (#FFFFFF)

### 특성 그래픽 (1024x500)
- `Feature Graphic_proppedia.png`

### 휴대전화 스크린샷 (1080x2340)
| 파일 | 화면 |
|-----|------|
| 01_home.png | 홈 화면 |
| 02_road_search.png | 도로명 검색 |
| 03_jibun_search.png | 지번 검색 |
| 04_result_1.png | 검색 결과 (기본/토지) |
| 05_result_2.png | 검색 결과 (동호/지도) |
| 06_map_search.png | 지도 검색 |
| 07_history.png | 검색기록 |
| 08_favorites.png | 즐겨찾기 |

### 7인치 태블릿 스크린샷 (1200x1920)
- `tablet_7inch/01_home.png`
- `tablet_7inch/02_road_search.png`
- `tablet_7inch/04_result_1.png`
- `tablet_7inch/06_map_search.png`

### 10인치 태블릿 스크린샷 (1600x2560)
- `tablet_10inch/01_home.png`
- `tablet_10inch/02_road_search.png`
- `tablet_10inch/04_result_1.png`
- `tablet_10inch/06_map_search.png`

---

## 8. 비공개 테스트 진행 현황

### Google Play 정책 요구사항
| 항목 | 요구사항 | 현황 |
|-----|---------|------|
| 테스트 유형 | 비공개 테스트 (Closed Testing) | ✅ 트랙 생성 완료 |
| AAB 업로드 | app-release.aab | ✅ 업로드 완료 |
| 테스트 기간 | 최소 **14일** 이상 | ⏳ 대기 중 |
| 테스터 수 | 최소 **20명** | ⏳ 모집 필요 |
| 테스터 활동 | 14일 동안 지속적으로 옵트인 | ⏳ 대기 중 |

### 비공개테스트 진행
유료테스트 진행 요청 (개발자 상부상조 카페 통해) : 2026.02.20.

### 다음 단계 (TODO)
1. [x] **테스터 20명 모집** (가족, 친구, 지인, 커뮤니티)
2. [x] **테스터 이메일 목록 등록** (Play Console → 비공개 테스트 → 테스터)
3. [x] **테스터 초대 링크 전송**
4. [x] **테스터 옵트인 확인** (20명 이상)
5. [x] **14일간 테스트 진행**
6. [x] **프로덕션 출시** (2026-03-08)

---

## 10. 테스트 기간 작업 계획 (14일)

### 테스트 시작일
- **시작일**: 2026-02-20 (테스터 초대 완료)
- **종료 예정**: 2026-03-06 (14일 후)
- **프로덕션 출시 가능일**: 2026-03-07 이후

### 필수 작업 (테스트 기간 중)

| 작업 | 설명 | 상태 |
|-----|------|------|
| 옵트인 모니터링 | Play Console에서 20명 이상 옵트인 확인 | ✅ |
| 피드백 수집 | 테스터 피드백 확인 및 버그 리포트 수집 | ✅ |
| 버그 수정 | 발견된 버그 수정 후 새 버전 업로드 | ✅ (v1.0.2+3~8) |
| 크래시 모니터링 | Play Console > Android vitals 확인 | ✅ |

### 권장 작업 (테스트 기간 활용)

#### 1. Flutter Web 배포 (Phase 9) ✅ 완료 (2026-02-20)
```bash
# 빌드 (base-href 설정 포함)
flutter build web --release --base-href "/proppedia-app/"

# 서버 배포
scp -r build/web/* root@175.119.224.71:/home/webapp/goldenrabbit/frontend/public/proppedia-app/
```
- [x] Flutter Web 빌드
- [x] 서버 배포
- [x] https://goldenrabbit.biz/proppedia-app/ 접속 확인

**배포 완료 URL**:
- 앱 소개 랜딩 페이지: https://goldenrabbit.biz/proppedia/
- Flutter Web 앱: https://goldenrabbit.biz/proppedia-app/

#### 2. iOS 앱 준비 (Phase 10)
- [ ] Apple Developer Program 가입 ($99/년)
- [ ] App Store Connect 앱 등록
- [ ] 프로비저닝 프로파일 생성
- [ ] IPA 빌드 및 업로드

#### 3. 남은 기능 개선
개발 계획(calm-forging-simon.md)에서 미완료 항목:
- [ ] 매물 즐겨찾기 기능 연동
- [ ] 홈 화면 매물 섹션 추가

### 홍보/마케팅 작업 (2026-02-20 완료)

| 작업 | 상태 |
|-----|------|
| 앱 소개 랜딩 페이지 제작 | ✅ 완료 |
| SEO 메타 태그 설정 | ✅ 완료 |
| robots.txt / sitemap.xml 배포 | ✅ 완료 |
| nginx 설정 업데이트 | ✅ 완료 |
| 블로그 콘텐츠 초안 작성 | ✅ 완료 |

### 선택 작업

| 작업 | 우선순위 |
|-----|---------|
| 유닛 테스트 작성 | 낮음 |
| 위젯 테스트 작성 | 낮음 |
| 성능 최적화 | 중간 |
| 오프라인 지원 강화 | 낮음 |

### 프로덕션 출시 체크리스트

- [x] 모든 크래시 이슈 해결
- [x] 테스터 피드백 반영 완료
- [x] 스토어 등록정보 최종 검토
- [x] 출시 노트 작성
- [x] 최종 AAB 빌드 및 업로드
- [x] 프로덕션 출시 (2026-03-08)

---

## 9. 중요 ID 정리

```
# 패키지 이름
com.proppedia.app

# AdMob App ID
ca-app-pub-3478991909223100~4421163836

# AdMob 광고 단위 ID (배너) - 실제
ca-app-pub-3478991909223100/1393451919

# AdMob 테스트용 배너 광고 ID (개발 중 사용)
ca-app-pub-3940256099942544/6300978111
```

---

## 11. Google OAuth 설정

### Google Cloud 프로젝트
- **프로젝트 번호**: `846392940969`

### OAuth Client IDs

| 용도 | Client ID | 비고 |
|------|-----------|------|
| Proptalk Web (서버 검증용) | `...a7k37gkon1p451mlnhp0oj9qaok1d8o1` | Proptalk/Propedia 모바일 serverClientId |
| Proppedia Web | `...sv2936v0tm85j8hvdn3srcmtei1kk25e` | PWA/Flutter Web 로그인, Dashboard OAuth |
| Propsheet Web | `...h70f1cqg6o97s526upn7gb5mqcnqmdsb` | Propsheet 웹 로그인 |
| Android Debug | `...g2afoiuc6m7kp64vp4fdo48rp2iqkt30` | 로컬 디버그 빌드용 |
| Android Release | `...1sdp4mc01gbsq2dgne4h8mnuvobi5644` | Play Store 배포용 |
| Proptalk Android | `...ro1j...` | Proptalk 앱용 |

### Android 서명 키 & SHA-1

| 키 종류 | SHA-1 | 용도 |
|--------|-------|------|
| 업로드 키 | `A2:E8:12:01:77:14:2E:E9:9B:13:7A:F0:B4:BB:66:92:D8:08:87:74` | 개발자가 AAB 서명 시 사용 |
| Play App Signing 키 | `37:3F:EA:3D:4E:D6:2A:A2:A6:AC:7C:7F:11:E1:D1:77:FB:A3:F0:74` | Google Play가 APK 배포 시 재서명 |

> **중요**: Play Store에서 다운로드한 앱은 **Play App Signing 키**로 서명됩니다.
> Google Cloud Console의 Android Release Client ID에는 **Play App Signing 키의 SHA-1**을 등록해야 합니다.
> 업로드 키의 SHA-1만 등록하면 Play Store 배포 앱에서 Google 로그인이 실패합니다.
>
> **SHA-1 확인 방법**:
> - Play App Signing 키: Google Play Console → 앱 선택 → **앱 무결성** → 앱 서명 탭
> - 업로드 키: `keytool -keystore android/app/propedia-release-key.jks -list -v`
>
> **인증서 지문 종류** (같은 키에서 해시 알고리즘만 다름):
> - MD5: 128비트 (거의 미사용)
> - SHA-1: 160비트 (**Google Cloud Console에서 사용**)
> - SHA-256: 256비트 (앱 링크 등에서 사용)

### OAuth 동의 화면
- **앱 이름**: Proppedia 부동산백과
- **스코프**: `email`, `profile` (민감하지 않음, 검토 불필요)
- **게시 상태**: 프로덕션 (2026-03-08 전환)

### 인증 플로우
```
[모바일 앱] Google Sign-In SDK → id_token → 서버 검증 (GOOGLE_CLIENT_IDS) → JWT 발급
[PWA 웹]   Google Identity Services → id_token → 서버 검증 → JWT 발급
[Dashboard] Google OAuth 웹 플로우 (리다이렉트) → 세션 로그인 (관리자만)
[JWT] access_token (24h) + refresh_token (30d)
```

### 서버 환경변수 (.env)
```
# Propsheet Web OAuth
GOOGLE_OAUTH_CLIENT_ID=846392940969-h70f...
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-Bhca...

# Proppedia Web OAuth (Dashboard)
PROPPEDIA_OAUTH_CLIENT_ID=846392940969-sv29...
PROPPEDIA_OAUTH_CLIENT_SECRET=GOCSPX-B8vj...
```

### 신규 앱 출시 시 Google 로그인 체크리스트
1. Google Cloud 프로젝트에서 Android Client ID 생성 (패키지명 + 업로드 키 SHA-1)
2. 비공개 테스트 진행 (업로드 키로 서명되므로 로그인 정상)
3. **프로덕션 출시 후**: Play Console → 앱 무결성 → Play App Signing 키 SHA-1 확인
4. Google Cloud Console → Android Release Client ID의 SHA-1을 **Play App Signing 키로 변경**
5. 적용까지 최대 수 시간 소요

---

## 참고 링크

- [Google Play Console](https://play.google.com/console)
- [AdMob Console](https://admob.google.com)
- [google_mobile_ads 패키지](https://pub.dev/packages/google_mobile_ads)
- [개인정보처리방침](https://goldenrabbit.biz/privacy-policy.html)

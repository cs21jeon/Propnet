# SEO 도메인 마이그레이션 진행현황

> 최종 업데이트: 2026-04-02

## 개요

goldenrabbit.biz → propnet.kr 도메인 변경에 따른 SEO 파일 전체 업데이트.
robots.txt, sitemap.xml, 메타태그(canonical, OG, Schema.org) 등을 propnet.kr 기준으로 변경.

## 진행 상태

| 단계 | 작업 | 상태 | 날짜 |
|------|------|------|------|
| 1 | robots.txt 업데이트 (propnet.kr + 신규 경로) | ✅ 완료 | 2026-04-02 |
| 2 | sitemap.xml 전면 재작성 (7개 URL) | ✅ 완료 | 2026-04-02 |
| 3 | Proppedia 랜딩 메타태그 (9곳) | ✅ 완료 | 2026-04-02 |
| 4 | Proppedia 가이드 메타태그 (3곳) | ✅ 완료 | 2026-04-02 |
| 5 | Proptalk 랜딩 메타태그 (5곳) | ✅ 완료 | 2026-04-02 |
| 6 | 법적 문서 canonical (5개 파일) | ✅ 완료 | 2026-04-02 |
| 7 | 문서 업데이트 (marketing-deployment.md, migration-plan.md) | ✅ 완료 | 2026-04-02 |
| 8 | 서버 배포 (10개 파일 + Nginx 수정) | ✅ 완료 | 2026-04-02 |
| 9-1 | Google Search Console: propnet.kr 속성 추가 | ✅ 완료 | 2026-04-02 |
| 9-2 | Google Search Console: sitemap.xml 제출 | ✅ 완료 | 2026-04-02 |
| 9-3 | Google Search Console: 색인 생성 요청 | ⏳ 대기 | 크롤링 수일 소요 |
| 9-4 | 네이버 서치어드바이저: propnet.kr 소유확인 | ✅ 완료 | 2026-04-02 |
| 9-5 | 네이버 서치어드바이저: sitemap 제출 | ✅ 완료 | 2026-04-02 |
| 9-6 | 네이버 서치어드바이저: robots.txt 검증 | ✅ 완료 | 2026-04-02 |

## 수정된 파일 목록

### SEO 파일 (서버 배포 완료)
| # | 로컬 파일 | 서버 경로 | 변경 내용 |
|---|----------|-----------|----------|
| 1 | `propedia/marketing/robots.txt` | `/frontend/public/robots.txt` | URL + 경로 추가 |
| 2 | `propedia/marketing/sitemap.xml` | `/frontend/public/sitemap.xml` | 전면 재작성 (7개 URL) |
| 3 | `propedia/marketing/proppedia/index.html` | `/frontend/public/proppedia/index.html` | canonical, OG, Schema.org, Footer |
| 4 | `propedia/marketing/proppedia/guide/index.html` | `/frontend/public/proppedia/guide/index.html` | canonical, OG |
| 5 | `proptalk/marketing/proptalk/index.html` | `/chat_stt/marketing/proptalk/index.html` | canonical, OG, Schema.org |
| 6 | `scripts/legal/terms-of-service.html` | `/frontend/public/legal/terms-of-service.html` | canonical |
| 7 | `scripts/legal/privacy-policy.html` | `/frontend/public/legal/privacy-policy.html` | canonical |
| 8 | `scripts/legal/overseas-transfer.html` | `/frontend/public/legal/overseas-transfer.html` | canonical |
| 9 | `scripts/legal/service-specific/proptalk-voice.html` | `/frontend/public/legal/service-specific/proptalk-voice.html` | canonical |
| 10 | `scripts/legal/service-specific/propsheet-property.html` | `/frontend/public/legal/service-specific/propsheet-property.html` | canonical |

### 문서
| 파일 | 변경 내용 |
|------|----------|
| `propedia/docs/marketing-deployment.md` | URL → propnet.kr, 5차 수정 기록, 검증 체크리스트 |
| `docs/propnet-kr-migration-plan.md` | SEO TODO 항목 체크 완료 |

### Nginx 설정
| 파일 | 변경 내용 |
|------|----------|
| `config/nginx/propnet.conf` | `/proppedia/landing/`: `try_files` → `index index.html;` + `^~` 수식자 추가 |

## sitemap.xml URL 구조

| URL | priority | 설명 |
|-----|----------|------|
| `https://propnet.kr/` | 1.0 | PropNet 메인 랜딩 |
| `https://propnet.kr/proppedia/landing/` | 0.9 | Proppedia 앱 소개 |
| `https://propnet.kr/proppedia/` | 0.8 | Proppedia 웹앱 |
| `https://propnet.kr/propmap/goldenrabbit/` | 0.8 | 금토끼부동산 매물지도 |
| `https://propnet.kr/proptalk/landing` | 0.7 | Proptalk 랜딩 |
| `https://propnet.kr/legal/privacy-policy.html` | 0.3 | 개인정보처리방침 |
| `https://propnet.kr/legal/terms-of-service.html` | 0.3 | 이용약관 |

## 검색엔진 등록 정보

### Google Search Console
- 속성: `https://propnet.kr`
- sitemap: `https://propnet.kr/sitemap.xml` (제출 완료, 크롤링 대기 중)
- 상태: "가져올 수 없음" → 크롤링 후 "성공"으로 전환 예정 (1~2일)

### 네이버 서치어드바이저
- 사이트: `https://propnet.kr`
- 소유확인: HTML 파일 방식 (`naver9eaf241a5229668e18f06c536a7231c7.html`)
- sitemap: 제출 완료
- robots.txt: Yeti 수집 허용 확인

## Nginx 404 수정 기록

`/proppedia/landing/` 접근 시 404 발생 → 원인 및 해결:

- **원인**: `alias` + `try_files` 조합에서 `index` 내부 리다이렉트가 regex `~* \.html$` location에 가로채져 `root` 기준으로 파일을 찾아 404 발생
- **해결**: `try_files` → `index index.html;`로 교체 + `^~` 수식자 추가로 regex 매칭 방지

## 향후 확인 사항

- [ ] Google Search Console sitemap 상태 "성공" 확인 (1~2일 후)
- [ ] Google 색인 생성 확인 (`site:propnet.kr` 검색)
- [ ] 네이버 검색 노출 확인 (`site:propnet.kr` 검색)
- [ ] Facebook Sharing Debugger로 OG 태그 검증
- [ ] Google Rich Results Test로 Schema.org 검증

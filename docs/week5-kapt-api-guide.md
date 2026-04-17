# Week 5 — K-apt 및 단지 식별 API 신청 가이드

> 작성일: 2026-04-16
> 작성자: @propnet-coo (총괄), @infra-lead + @propsheet-dev (실무)
> 문서 상태: **오너 검토 대기 (API 신청 액션 필요)**
> 목적: 디스코 수준 단지 통합 UX 구현에 필요한 공공 API 전수 조사 + 신청 절차 안내

---

## 0. Executive Summary (먼저 읽으세요)

오너가 직접 해야 할 액션은 **공공데이터포털 로그인 후 "활용신청" 버튼 3번 클릭**이 전부입니다.
아래 3개 API 전부 **자동승인**이며, 영업일 기준 **최대 1일** 안에 키가 활성화됩니다.

| # | API 정식 명칭 | 제공기관 | 승인 방식 | 일일 한도 | 용도 | 우선순위 |
|---|---|---|---|---|---|---|
| **A** | **공동주택 단지 목록제공 서비스** | 국토교통부 | **자동승인** | 10,000건 | 전국 단지코드(kaptCode) 목록 수집 (약 2만 건) | **필수 1** |
| **B** | **공동주택 기본 정보제공 서비스** | 국토교통부 | **자동승인** | 10,000건 | 단지코드 → 단지명/세대수/동수/준공년도/주소 | **필수 2** |
| **C** | **공동주택 단지 식별정보 조회 서비스** | 한국부동산원 | **개발 자동승인 / 운영 심의** | 40,000건 | **단지 ↔ PNU 매핑 + 단지명 3종 별칭 ← 핵심** | **필수 3 (가장 중요)** |

> **핵심 인사이트**: C(한국부동산원)가 우리 Week 5의 문제를 바로 풉니다.
> - `COMPLEX_PK` (단지고유번호) ↔ `PNU` (필지고유번호, 우리 DB의 pnu와 1:1)
> - `COMPLEX_NM1` (공시가격용 단지명) / `COMPLEX_NM2` (건축물대장용) / `COMPLEX_NM3` (도로명주소용)
>   → 잠실주공 문제("주공/잠실/잠실주공") 해결
> - `DONG_CNT`, `UNIT_CNT` 등 메타데이터도 한 API에서 제공

---

## 1. 사전 준비 (오너 액션)

### 1.1 공공데이터포털 계정 확인
- 이미 계정이 있으면 skip: https://www.data.go.kr → 로그인
- 계정이 없을 경우 회원가입 (약 2분, 휴대폰 본인인증 필요)

### 1.2 마이페이지 위치 확인
- 로그인 후 우측 상단 **"마이페이지"** 클릭
- 좌측 메뉴: **"나의 데이터 > 오픈API > 개발계정 / 운영계정"**
- 신청 완료 후 서비스키는 이곳에서 발급/복사

---

## 2. API A — 공동주택 단지 목록제공 서비스

### 2.1 페이지 이동
- **신청 페이지**: https://www.data.go.kr/data/15057332/openapi.do

### 2.2 신청 절차 (스크린샷 없이도 가능)
1. 해당 페이지 우측 상단 **"활용신청"** 버튼 클릭
2. 신청 폼 작성
   - **활용목적 선택**: "웹 사이트 개발" 체크
   - **상세 용도**: 아래 문장 복사해서 붙여넣기
     ```
     부동산 중개 플랫폼에서 매물 등록 시 공동주택 단지 자동 매핑을 위해
     전국 단지코드(kaptCode) 및 법정동 매핑 정보를 활용합니다.
     자체 DB에 단지 마스터 테이블을 구축하여 지번-단지 변환에 사용합니다.
     ```
   - **라이선스 동의**: "동의합니다" 체크
3. **신청** 버튼 → 자동승인으로 즉시 키 발급
4. **마이페이지 > 개발계정**에서 **일반 인증키(Encoding / Decoding)** 복사

### 2.3 활용할 Operation (4개 중 2개만 사용)
| Operation | 용도 | 우리 사용 여부 |
|---|---|---|
| `getTotalAptList3` | 전국 전체 | 파일럿 후 전국 확장 시 사용 |
| `getSidoAptList3` | 시도별 (예: 서울=11) | 서울 전체 확장 시 |
| `getSigunguAptList3` | 시군구별 (예: 송파구=11710) | **파일럿 단계 핵심** |
| `getLegaldongAptList3` | 법정동별 (bjdCode 10자리) | 미세 조정 시 |

### 2.4 엔드포인트
```
Base: https://apis.data.go.kr/1613000/AptListService3
예: /getSigunguAptList3?serviceKey={KEY}&sigunguCode=11710&pageNo=1&numOfRows=500
```

### 2.5 응답 필드
| 필드 | 설명 | 우리 DB 매핑 |
|---|---|---|
| `kaptCode` | 단지코드 (A+숫자) | `complex_master.kapt_code` |
| `kaptName` | 단지명 | `complex_master.name` (기본값) |
| `as1` | 시도 | (복원용) |
| `as2` | 시군구 | (복원용) |
| `as3` | 읍면동 | (복원용) |
| `as4` | 리 | (복원용) |
| `bjdCode` | 법정동코드 10자리 | (매핑 보조) |

---

## 3. API B — 공동주택 기본 정보제공 서비스

### 3.1 페이지 이동
- **신청 페이지**: https://www.data.go.kr/data/15058453/openapi.do

### 3.2 신청 절차
1. **"활용신청"** 버튼 클릭
2. 신청 폼 작성
   - **활용목적**: "웹 사이트 개발"
   - **상세 용도**:
     ```
     공동주택 단지 마스터 DB 구축을 위해 단지별 기본정보
     (단지명, 세대수, 동수, 준공년도, 주소)를 수집합니다.
     중개 플랫폼 매물 등록 자동완성 및 단지 단위 매물 묶음에 활용합니다.
     ```
3. **신청** → 자동승인

### 3.3 엔드포인트
```
Base: https://apis.data.go.kr/1613000/AptBasisInfoServiceV4
예: /getAphusBassInfoV4?serviceKey={KEY}&kaptCode=A10027875
```

### 3.4 응답 필드
| 필드 | 설명 | 우리 DB 매핑 |
|---|---|---|
| `kaptCode` | 단지코드 | `complex_master.kapt_code` |
| `kaptName` | 단지명 | `complex_master.name` |
| `kaptAddr` | 법정동주소 | `complex_master.address_jibun` |
| `doroJuso` | 도로명주소 | `complex_master.address_road` |
| `kaptdaCnt` | 세대수 | `complex_master.household_count` |
| `kaptDongCnt` | 동수 | `complex_master.dong_count` |
| `kaptUsedate` | 사용승인일 (YYYYMMDD) | `complex_master.completion_year` (YYYY) |
| `codeSaleNm` | 분양형태 | `complex_master.complex_type` (참고) |
| `codeHeatNm` | 난방방식 | (참고용) |

---

## 4. API C — 공동주택 단지 식별정보 조회 서비스 ← **가장 중요**

### 4.1 페이지 이동
- **신청 페이지**: https://www.data.go.kr/data/15106817/openapi.do

### 4.2 신청 절차 (주의: 운영 단계는 심의)
1. **"활용신청"** 버튼 클릭
2. 신청 폼 작성
   - **활용목적**: "웹 사이트 개발"
   - **상세 용도** (조금 더 구체적으로 작성해야 추후 운영 심의 통과 유리):
     ```
     부동산 중개 플랫폼(goldenrabbit.biz, propnet.kr)에서
     지번(PNU)과 공동주택 단지(COMPLEX_PK)의 매핑 정보를 활용하여
     다음 기능을 구현합니다.

     1. 매물 등록 시 지번 입력만으로 단지명·동호 자동완성
     2. 여러 필지에 걸친 대단지(예: 파크리오 5개 지번)의
        단지 단위 통합 표시
     3. 단지명 별칭(공시가격/건축물대장/도로명주소) 3종 동시
        검색 지원 (예: "주공/잠실/잠실주공" 혼용 케이스)

     데이터는 자체 DB(complex_master 테이블)에 적재 후
     서비스에서 활용합니다.
     ```
3. **신청** → **개발계정 자동승인** (운영계정은 활용사례 등록 후 심의)

### 4.3 엔드포인트 (Swagger 기반)
```
Base: https://infuser.odcloud.kr/... (공공데이터포털 신청 후 확인)
응답: JSON / XML
```

### 4.4 Operation 3개
| Operation | 용도 | 주요 파라미터 |
|---|---|---|
| **getAptInfo** | 기본정보 조회 | `cond[COMPLEX_PK::EQ]=xxx` 또는 `cond[ADRES::LIKE]=서울 송파구...` |
| **getDongInfo** | 동정보 조회 | `cond[COMPLEX_PK::EQ]=xxx` |
| **getHistInfo** | 단지명 이력 조회 | `cond[COMPLEX_PK::EQ]=xxx` |

### 4.5 응답 필드 ← **핵심**
#### getAptInfo
| 필드 | 설명 | 우리 DB 매핑 |
|---|---|---|
| `COMPLEX_PK` | 단지고유번호 | `complex_master.kapt_code` 또는 별도 `complex_pk` |
| **`PNU`** | **필지고유번호** | **`complex_master.pnu_list[]` ← 핵심** |
| `ADRES` | 주소 | `complex_master.address_jibun` |
| **`COMPLEX_NM1`** | 공시가격용 단지명 | **`complex_master.aliases[0]`** |
| **`COMPLEX_NM2`** | 건축물대장용 단지명 | **`complex_master.aliases[1]`** |
| **`COMPLEX_NM3`** | 도로명주소용 단지명 | **`complex_master.aliases[2]`** |
| `DONG_CNT` | 동수 | `complex_master.dong_count` |
| `UNIT_CNT` | 세대수 | `complex_master.household_count` |
| `USEAPR_DT` | 사용승인일 | `complex_master.completion_year` |

#### getDongInfo
| 필드 | 설명 | 우리 DB 매핑 |
|---|---|---|
| `COMPLEX_PK` | 단지고유번호 | 연결키 |
| `DONG_NM1` | 공시가격용 동명 | `dong_alias[0]` |
| `DONG_NM2` | 건축물대장용 동명 | `dong_alias[1]` |
| `DONG_NM3` | 도로명주소용 동명 | `dong_alias[2]` |
| `GRND_FLR_CNT` | 지상층수 | 참고용 |

#### getHistInfo (단지명 변경 이력)
- 예: "잠실주공아파트" → "잠실엘스"로 변경된 케이스 추적
- `NM_CHAN_YEAR`, `COMPLEX_EX_NM`, `COMPLEX_PR_NM`

---

## 5. 신청 후 확인 체크리스트

### 5.1 서비스키 수령 확인
- 마이페이지 > 개발계정 > 각 API 상세
- **일반 인증키(Encoding)**: URL 파라미터용 (URL 인코딩된 문자열)
- **일반 인증키(Decoding)**: 원본 문자열 (서버에서 코드로 인코딩 시 사용)
- 일반적으로 우리 Python 코드에서는 **Decoding 키** 사용 후 `requests`가 자동 인코딩

### 5.2 `.env` 등록 (서버 인프라부 처리)
```bash
# /home/webapp/goldenrabbit/backend/.env 에 추가
KAPT_LIST_API_KEY=<API A Decoding 키>
KAPT_BASIS_API_KEY=<API B Decoding 키>
REB_COMPLEX_ID_API_KEY=<API C Decoding 키>
```

> **CRITICAL 준수**: 환경변수로만 보관. 절대 코드/문서에 하드코딩 금지.

### 5.3 간단 sanity test (키 수령 직후)
```bash
# API A: 송파구(11710) 단지 리스트 5건
curl "https://apis.data.go.kr/1613000/AptListService3/getSigunguAptList3?serviceKey=$KAPT_LIST_API_KEY&sigunguCode=11710&numOfRows=5&_type=json"

# API B: 위에서 나온 kaptCode 1개로 기본정보
curl "https://apis.data.go.kr/1613000/AptBasisInfoServiceV4/getAphusBassInfoV4?serviceKey=$KAPT_BASIS_API_KEY&kaptCode=A10027875&_type=json"
```

응답 `resultCode=00` 및 `header.resultMsg=NORMAL SERVICE` 확인하면 정상.

---

## 6. 신청 후 @propnet-coo에게 보고할 것 (3가지)

1. **3개 API 활용신청 완료 여부** (각각 승인 스크린샷 or 승인 시각)
2. **서비스키 3개를 서버 `.env`에 등록 완료 여부**
   - 오너가 키만 전달해도 OK — @infra-lead가 등록
3. **파일럿 지역 선정 확정** (기본값: 송파구 11710 + 동작구 11590 + 관악구 11620)

이 3가지가 완료되면 @propsheet-dev가 `scripts/sync_complex_master_from_kapt.py` 작성 + 파일럿 적재를 시작합니다.

---

## 7. 병행 진행 가능한 작업 (API 키 대기 중 @propnet-coo 분배)

API 키가 아직 안 나왔어도 아래는 선행 가능합니다.

| 작업 | 담당 | 비고 |
|---|---|---|
| `complex_master` DDL 서버 적용 | @infra-lead | 무중단 ALTER, Week 5 Phase 1-2 |
| `/api/complex/lookup` 엔드포인트 스텁 | @propsheet-dev | 빈 응답이라도 라우팅 먼저 |
| Propedia 매물 등록 동 드롭다운 필수화 | @propedia-dev | 클라이언트 밸리데이션 강화 |
| `dong-cluster-renderer.js` complex 레이어 뼈대 | @propmap-dev | Mock 데이터로 UI 먼저 |
| `docs/prd-complex-master-week5.md` 초안 | @pm-lead | 본 가이드 기반 확장 |

---

## 8. 리스크 및 대비책

| 리스크 | 확률 | 영향 | 대비 |
|---|---|---|---|
| API C(한국부동산원) 운영 심의 지연 | 중 | 중 | 파일럿은 개발계정으로 진행. 활용사례 축적 후 신청 |
| 일일 10,000건 한도 초과 (전국 2만 단지 적재) | 상 | 중 | 2일 분산 적재 + 캐싱. 활용사례 등록으로 증가 신청 |
| PNU 매핑이 부분적으로만 제공되는 경우 | 중 | 상 | VWorld 캐시(15,096건)와 교차 검증. 누락분은 카카오 Local 보조 |
| 단지명 별칭(COMPLEX_NM1/2/3) 일부 null | 중 | 저 | 가용한 것만 `aliases[]`에 추가. 우리 DB의 건물명과 퍼지 매칭 보조 |
| 서비스키가 여러 개 필요한 경우(트래픽) | 하 | 저 | 라운드로빈 또는 한도 초과 시 대기 큐 |

---

## 9. 참고 링크 (오너 원클릭용)

- [국토교통부 공동주택 단지 목록제공 서비스 (API A)](https://www.data.go.kr/data/15057332/openapi.do)
- [국토교통부 공동주택 기본 정보제공 서비스 (API B)](https://www.data.go.kr/data/15058453/openapi.do)
- [한국부동산원 공동주택 단지 식별정보 조회 서비스 (API C)](https://www.data.go.kr/data/15106817/openapi.do)
- [K-apt 공동주택관리정보시스템 (일반 조회 사이트)](https://www.k-apt.go.kr/)
- [공공데이터포털 마이페이지](https://www.data.go.kr/iim/api/selectAcountList.do)

---

## 10. 다음 문서 (Phase 1 완료 후 자동 생성 예정)

- `docs/prd-complex-master-week5.md` — PRD (제품기획부)
- `docs/tech-design-complex-master.md` — 기술설계 (@dev-lead + @infra-lead)
- `docs/week5-deployment-guide.md` — 배포 가이드 (@infra-lead)
- `docs/week5-final-qa-report.md` — QA 리포트 (@qa-lead)

---

**작성 완료 — 오너에게 위 3개 API 활용신청을 요청드립니다. 신청 즉시 @propnet-coo에게 알려주세요.**

# Week 5 — 공동주택 단지 마스터 CSV 경로 (방향 전환 최종본)

> 작성일: 2026-04-16
> 작성자: @propnet-coo (총괄), @infra-lead + @propsheet-dev (실무)
> 문서 상태: **확정 — 오너 승인 불필요 (공공데이터, 라이선스 제한 없음)**
> 목적: 디스코 수준 단지 통합 UX를 위한 **공동주택 단지 마스터 DB** 구축.
> 이전 문서: `docs/week5-kapt-api-guide.md` (API 3개 신청 기반) — **이 문서로 대체되며, API 기반은 "필요 시" 옵션으로 전환**

---

## 0. 핵심 요약 (방향 전환 배경)

오너가 직접 조사한 결과 **API 키 없이도 즉시 진행 가능한 경로 확보**:

- **데이터셋**: 한국부동산원 공동주택 단지 식별정보_기본정보 (dataset id 15106861)
- **파일 형식**: CSV (UTF-8 with BOM)
- **규모**: 307,407 레코드 (공공데이터포털 표기 44,628건은 "단지 수" 기준, 실제 CSV는 필지(PNU) 단위)
- **API 키 불필요, 회원가입 불필요, 로그인 불필요**
- **라이선스**: 이용허락범위 제한 없음
- **갱신 주기**: 연간 (차기 등록 2026-11-11 예정)

이전 가이드의 3개 OpenAPI(A=단지 목록, B=단지 기본정보, C=단지 식별정보)는 **실시간 조회가 필요해지는 시점까지 전면 보류**.

---

## 1. 직접 다운로드 경로 (검증 완료 2026-04-16)

### 1-1. 기본정보 (단지 ↔ 필지 ↔ 3종 단지명)
```
POST https://www.data.go.kr/cmm/cmm/fileDownload.do
  atchFileId=FILE_000000003521525
  fileDetailSn=1
Referer: https://www.data.go.kr/data/15106861/fileData.do
```
- 응답: Content-Type `application/octet-stream`, Content-Disposition `attachment; filename="한국부동산원_공동주택 단지 식별정보_기본정보_20250918.csv"`
- 크기: **45,748,054 bytes (약 43.6MB)**
- 건수: **307,407** 레코드

### 1-2. 동정보 (단지 ↔ 동 ↔ 3종 동명 ↔ 지상층수)
- 데이터셋: 15106866
- 건수: 160,020
- 컬럼: 단지고유번호, 동명_공시가격, 동명_건축물대장, 동명_도로명주소, 지상층수
- 다운로드: 15106861과 동일 방식, `atchFileId`만 교체

### 1-3. 단지명 이력정보 (개명 이력)
- 데이터셋: 15106867
- `atchFileId = FILE_000000003521520`, `fileDetailSn = 1`
- 건수: 8,905
- 컬럼: 단지고유번호, 변경년도, 변경전단지명, 변경후단지명

### 1-4. 공통 주의사항
- 응답 헤더에 `JSESSIONID` 쿠키가 내려오지만 **인증 목적 아님**, 저장/전송 불필요
- User-Agent는 일반 브라우저 문자열 권장 (서버 차단 방지)
- Content-Disposition filename은 URL 인코딩된 UTF-8. 저장 시 decode 필요

---

## 2. CSV 실제 구조 (기본정보, 2025-09-18 스냅샷)

### 2-1. 컬럼 (10개)
| Idx | 컬럼명 | 예시 | 매핑 |
|---|---|---|---|
| 0 | 단지고유번호 | `11710120100792` | `complex_master.complex_pk` (PK) |
| 1 | 필지고유번호 | `1171010200100170000` | `complex_master.representative_pnu` + `complex_parcels` |
| 2 | 주소 | `서울특별시 송파구 신천동 17` | `complex_master.address_jibun` |
| 3 | 단지명_공시가격 | `파크리오` | `complex_master.name` (기본값) |
| 4 | 단지명_건축물대장 | `파크리오` | `complex_master.aliases[]` |
| 5 | 단지명_도로명주소 | `파크리오` | `complex_master.aliases[]` |
| 6 | 단지종류 | `2` (1=아파트, 2=연립, 3=다세대) | `complex_master.complex_type_code` |
| 7 | 동수 | `66` | `complex_master.dong_count` |
| 8 | 세대수 | `6864` | `complex_master.household_count` |
| 9 | 사용승인일 | `2008-08-29` | `complex_master.completion_date` |

### 2-2. 실측 샘플 — 파크리오 (검증 성공)
```
11710120100792 | 1171010200100170000 | 서울특별시 송파구 신천동 17
  공시=파크리오 건대=파크리오 도로=파크리오 동수=66 세대수=6864
```
- **핵심 통찰**: 이 CSV의 파크리오는 **단지고유번호 1건, 대표 PNU 1건(17번지)** 으로 관리됨. 17-4, 17-5, 20, 20-6 지번은 CSV에 포함되지 않음.
- 즉 이 CSV의 "필지고유번호"는 **"단지 대표 PNU"** 이며, 세부 지번을 단지로 묶으려면 **별도 매핑(카카오 Local / VWorld / 건축물대장)이 필요**.

### 2-3. 실측 샘플 — 잠실 단지명 3종 혼용
```
11710100002363 | 1171010100100270000 | 잠실동 27
  공시=주공아파트5단지 건대=(빈값) 도로=주공아파트 507동
```
- 단지명이 공시/건축물대장/도로명에 따라 다르게 불리는 케이스 확보.
- 프론트엔드 자동완성은 **3개 컬럼을 모두 `aliases[]`로 색인** 필요.

### 2-4. 실측 샘플 — 동일 주소 다단지 분리
```
11710100002369 | 1171010200100070000 | 신천동 7 | 장미1 | 21동 2100세대
11710100050192 | 1171010200100110000 | 신천동 11 | 장미2 | 10동 1302세대
11710100002370 | 1171010200100110000 | 신천동 11 | 장미3 |  2동  120세대
```
- 장미 1/2/3차는 **서로 다른 단지고유번호**로 관리되며, 장미2와 장미3는 **동일 PNU(11번지)** 공유.
- 즉 `(PNU → 단지)` 관계는 **1:N**이므로 역방향 매핑(`complex_parcels`) 테이블이 필수.

---

## 3. 파일럿 실행 계획 (API 키 대기 불필요)

### Phase 1 — CSV 다운로드 + 파싱 (오늘)
1. 서버에 `scripts/week5_complex_master/download_kreb_csv.sh` 배포 → `/data/complex_master/raw/apt_basic_info_YYYYMMDD.csv` 저장
2. 로컬에서도 동일 CSV 확보 완료 (`data/complex_master_raw/apt_basic_info_20250918.csv`)
3. 파싱 검증: `scripts/week5_complex_master/parse_and_verify.py`
   - 파크리오 존재 확인 → 단지고유번호 = `11710120100792`
   - 잠실 관련 단지명 3종 혼용 케이스 확인
   - 장미1/2/3 분리 확인

### Phase 2 — DDL 확정 (오늘~내일)
- `complex_master` — 단지 마스터 (단지고유번호 PK)
- `complex_parcels` — 단지 ↔ 필지 N:M (세부 지번은 VWorld/카카오로 사후 보강)
- `complex_aliases` — 단지 ↔ 별칭 (공시/건대/도로 3종 + 과거 이력)
- `complex_dong` — 단지 ↔ 동 (추후 동정보 CSV로 적재)

### Phase 3 — 적재 스크립트 (내일)
- `scripts/week5_complex_master/load_complex_master_from_csv.py`
- 파일럿: 송파(11710) + 동작(11590) + 관악(11620)
- 서울 전역 → 전국 순차

### Phase 4 — 엔드포인트 + UI (이번 주)
- `/api/complex/lookup?pnu=...` / `?lat=...&lon=...` / `?name=...`
- `dong-cluster-renderer.js` complex 레이어
- Propedia 매물 등록 단지 자동완성

### Phase 5 — E2E 검증
- Playwright: 파크리오/잠실주공/사당동 롯데캐슬
- Before/After 스크린샷
- 이 문서 하단에 이미지 첨부 예정

---

## 4. 스키마 재설계 반영 포인트

### 4-1. PK 변경
- **이전 제안**: `kapt_code VARCHAR(11)` (국토부 K-apt 기준)
- **신규 확정**: `complex_pk VARCHAR(14)` (한국부동산원 단지고유번호)
- 국토부 kaptCode와 병행 보관 위해 `kapt_code` 컬럼은 nullable로 유지
- API C의 `COMPLEX_PK`와 동일 체계 → 향후 API 통합 시 변환 불필요

### 4-2. PNU 1:N 처리
- 이전 제안: `pnu_list TEXT[]` 단일 컬럼
- 신규 확정: **`complex_parcels` 별도 테이블** + `representative_pnu` 컬럼 분리
  - 이유: 세부 지번(17-4, 17-5 등)을 VWorld/카카오로 사후 보강해야 하는데, 배열로는 상태 관리 어려움
  - 각 parcel에 `source` 컬럼(`reb_csv`, `vworld_matched`, `kakao_fallback`, `manual`) 포함

### 4-3. 단지명 3종 + 이력 통합 저장
- `complex_aliases` 테이블:
  - `alias_type`: `gongsi`(공시가격), `bldreg`(건축물대장), `road`(도로명주소), `past`(이력), `user`(사용자 입력)
  - `name`: 별칭 값
  - `year`: (past 타입의 경우) 변경년도
- 프론트 자동완성은 `UNION (name) + (alias.name)` 후 GIN(trigram) 인덱스로 매칭

### 4-4. source / confidence 컬럼 필수
- `source`: `reb_csv_20250918`, `kapt_api_v4`, `vworld_nsdi`, `manual`
- `confidence`: 0.0~1.0 (CSV 정확 매칭=1.0, 주소 퍼지 매칭=0.7, 수동 입력=0.9)

---

## 5. 다운로드 재실행 / 갱신 절차

### 5-1. 연간 갱신 (2026-11-11 예정)
1. 공공데이터포털 `/data/15106861/fileData.do` 페이지에서 최신 `atchFileId` 확인 (JS 콘솔 1회 조회)
2. 서버 스크립트의 `atchFileId` 환경변수 갱신
3. `download_kreb_csv.sh` 재실행
4. `load_complex_master_from_csv.py --incremental` 실행 → diff 적용
5. 단지명 변경(past) 이력은 15106867 CSV로 별도 흡수

### 5-2. 운영 중 단건 조회가 필요해질 경우
- 이전 `week5-kapt-api-guide.md`의 API C (dataset 15106817) 신청
- 이 가이드의 section 4.2 절차 참고
- 오너 액션: "활용신청" 버튼 1회만 누르면 개발계정 자동승인
- **현재 시점에는 신청하지 않음** — CSV로 충분

---

## 6. 보안 / 환경변수

```bash
# /home/webapp/goldenrabbit/backend/.env 에 추가 (선택)
REB_CSV_URL=https://www.data.go.kr/cmm/cmm/fileDownload.do
REB_CSV_ATCHFILEID_BASIC=FILE_000000003521525
REB_CSV_ATCHFILEID_DONG=FILE_000000003521522   # 15106866 동정보
REB_CSV_ATCHFILEID_HIST=FILE_000000003521520   # 15106867 이력정보
REB_CSV_FILE_DETAIL_SN=1
COMPLEX_MASTER_RAW_DIR=/home/webapp/goldenrabbit/data/complex_master/raw
```

- atchFileId는 공공데이터 포털에서 주기적으로 변경될 수 있음 → 환경변수 분리
- API 키가 아니므로 소스코드에 하드코딩해도 기밀은 아니지만, URL 구조 통일을 위해 env 관리 권장

---

## 7. 리스크 & 대비

| 리스크 | 확률 | 영향 | 대비 |
|---|---|---|---|
| 공공데이터포털 다운로드 API 변경 | 중 | 상 | atchFileId만 env 갱신. 최후에는 수동 다운로드 후 서버 scp |
| CSV의 "대표 PNU만 제공" 한계 → 세부 지번 매칭 불가 | **상** | **상** | **VWorld/카카오 Local로 주소→PNU 역매핑. building_dong_geometry 캐시 활용** |
| 연간 갱신 주기가 실제보다 지연 (2026-11-11 미등재) | 중 | 중 | 현재 2025-09-18 스냅샷으로 충분. 신규 단지는 매물 등록 시 수동 추가 |
| CSV 한글 문자 인코딩 깨짐 | 저 | 하 | UTF-8 with BOM 확정. Python `encoding='utf-8-sig'` 사용 |
| 307,407건 일괄 INSERT 시 DB 부하 | 중 | 중 | `COPY` 명령 사용 + 일반 INSERT는 배치 2000건 단위 |

---

## 8. 체크리스트

### 완료 (2026-04-16)
- [x] 공공데이터포털 FileData 페이지에서 다운로드 엔드포인트 확인 (`/cmm/cmm/fileDownload.do`)
- [x] 필요 파라미터 추출 (`atchFileId`, `fileDetailSn`)
- [x] 비로그인 상태로 CSV 45.7MB 다운로드 성공
- [x] UTF-8 BOM 파싱 성공, 307,407 레코드 확인
- [x] 파크리오 케이스 확인 (`11710120100792` / `1171010200100170000` / 66동 6864세대)
- [x] 단지명 3종 혼용 케이스 확인 (잠실 주공/엘스/507동)
- [x] 로컬 파일 저장: `data/complex_master_raw/apt_basic_info_20250918.csv`

### 다음 단계
- [ ] `complex_master`, `complex_parcels`, `complex_aliases`, `complex_dong` DDL 확정 → `docs/tech-design-complex-master.md`
- [ ] 서버에 `scripts/week5_complex_master/download_kreb_csv.sh` 배포
- [ ] CSV → DB 적재 스크립트 `load_complex_master_from_csv.py` 작성 + 파일럿 실행
- [ ] `/api/complex/lookup` 엔드포인트 구현
- [ ] `dong-cluster-renderer.js` complex 레이어 확장
- [ ] Propedia 매물 등록 단지 자동완성 UI
- [ ] Playwright E2E 검증 + Before/After 증거

---

## 9. 참고 링크

- [한국부동산원 공동주택 단지 식별정보_기본정보 (15106861)](https://www.data.go.kr/data/15106861/fileData.do)
- [동정보 (15106866)](https://www.data.go.kr/data/15106866/fileData.do)
- [단지명 이력정보 (15106867)](https://www.data.go.kr/data/15106867/fileData.do)
- [이전 API 신청 가이드](./week5-kapt-api-guide.md) — 필요 시 참고

---

## 부록 A. 검증 커맨드 (재현 가능)

```bash
# CSV 다운로드 (로그인 불필요)
curl -sS -X POST "https://www.data.go.kr/cmm/cmm/fileDownload.do" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -H "Referer: https://www.data.go.kr/data/15106861/fileData.do" \
  --data-urlencode "atchFileId=FILE_000000003521525" \
  --data-urlencode "fileDetailSn=1" \
  -o apt_basic_info_20250918.csv \
  --max-time 60 -L

# 파크리오 확인
python -X utf8 -c "
import csv
with open('apt_basic_info_20250918.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['단지명_공시가격'] == '파크리오' and '송파' in r['주소']:
            print(r)
"
```

---

**작성 완료 — 바로 다음 문서(`tech-design-complex-master.md`)에서 DDL 확정 + 매핑 로직 설계 진행합니다.**

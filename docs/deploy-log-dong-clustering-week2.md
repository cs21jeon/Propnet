# Dong Clustering Week 2 Deploy Log

**Date**: 2026-04-16
**Executor**: @propnet-coo (오너 결정 위임 받아 진행)
**Status**: COMPLETE — 기능 플래그 OFF 상태로 배포 완료

## 오너 위임 → 확정 결정

1. 줌 임계값 15 — 그대로
2. 매물 없는 동 회색 윤곽 — B안 (표시함)
3. 단지 팝업 대표 이미지 — YES (첫 매물 사진 노출)
4. NSDI API 키 — **별도 신청 불필요** (기존 `PUBLIC_API_KEY`가 NSDI/BldRgstHubService 공통 사용. 실호출 테스트로 유효성 확인 완료)

## 환경 조사 결과

| 항목 | 값 |
|---|---|
| VWorld API 키 | `VWORLD_APIKEY` 기존 존재, 유효 |
| 공공데이터포털 키 | `PUBLIC_API_KEY` 기존 존재, `BldRgstHubService` `resultCode:00` 확인 |
| agent 매물 테이블 | `goldenrabbit01_sales_building`, `goldenrabbit01_sales_multi_unit` (2개만 실존) |
| VWorld `lt_c_bldginfo` WFS | GeoJSON 정상 반환, 일부 건물 `dong_nm=null` 확인 (NSDI fallback 필요성 검증됨) |

## 변경사항

### 1. DB 스키마 (`goldenrabbit_db`)

- 신규 테이블: `building_dong_geometry`
  - PK `bd_mgt_sn`
  - UNIQUE `(pnu, dong_nm)`
  - GIN 인덱스 `idx_bdg_geom` (geometry)
  - BTREE 인덱스 `idx_bdg_pnu`
  - owner: `goldenrabbit_user`
- 매물 테이블 컬럼 추가:
  - `goldenrabbit01_sales_building.bd_mgt_sn VARCHAR(25) NULL`
  - `goldenrabbit01_sales_multi_unit.bd_mgt_sn VARCHAR(25) NULL`
- 인덱스 (CONCURRENTLY 생성):
  - `idx_sales_building_bdmgtsn`
  - `idx_sales_multi_unit_bdmgtsn`

### 2. 신규 파일

| 서버 경로 | 로컬 미러 | 설명 |
|---|---|---|
| `/backend/property-manager/services/ldareg_service.py` | `backend/property-manager/services/ldareg_service.py` | NSDI 대지권등록정보 래퍼 (건물동명조회) |
| `/backend/property-manager/services/cadastral_service_dong_ext.py` | 동일 | `CadastralService` monkey-patch 확장 (4개 메서드) |
| `/backend/property-manager/routes/map_dong.py` | 동일 | `/api/propsheet/map/dong-coords` 엔드포인트 |

### 3. 기존 파일 수정

| 서버 경로 | 수정 내용 | 백업 |
|---|---|---|
| `/backend/propsheet/app.py` | `map_dong` Blueprint 등록 | `.bak.week2` |
| `/backend/property-manager/app.py` | `map_dong` Blueprint 등록 | `.bak.week2` |
| `/backend/property-manager/routes/app_api.py` | `_resolve_coordinates()` 1.5순위(본번 리다이렉트) 삽입 | `.bak.week2` |
| `/backend/.env` | `ENABLE_DONG_CLUSTERING=false` 추가 | `.bak.week2` |

### 4. 서비스 재시작

```
sudo systemctl restart property-manager proppedia propsheet
```

- 3개 서비스 모두 `active` 확인
- `[CadastralExt] 확장 메서드 주입 완료` 로그 확인

## 검증 결과

### HTTP 응답 (플래그 OFF 상태, 현재)

| 엔드포인트 | 포트 | 응답 |
|---|---|---|
| `/api/propsheet/map/dong-coords/health` | 5000 | 200 `{enabled:false, vworld_key:true, public_api_key:true}` |
| `/api/propsheet/map/dong-coords/health` | 5020 | 200 (동일) |
| `/api/propsheet/map/dong-coords?pnu=...` | 5020 | 503 (의도대로) |

### Smoke Test (플래그 일시 ON)

- 헬스체크: `enabled:true` 정상 노출
- `?lat=37.4988&lon=127.0286` 호출: `get_building_by_coord` 성공 → `get_buildings_by_pnu`에서 VWorld WFS Filter 쿼리 구문 이슈로 `Parcel not found` 반환
- **Week 3 태스크로 이관**: WFS Filter → BBOX+후처리 방식으로 리팩터 또는 NSDI 기반 좌표 확보 보강
- 플래그는 즉시 `false`로 복구, 재배포 완료

## 다음 단계 (Week 3 착수 조건)

1. `get_buildings_by_pnu` 내부 Filter 구문 교정 또는 BBOX+PNU 후처리 전환
2. 실동 데이터 3건 이상 `building_dong_geometry` 캐시로 검증
3. 프론트엔드 `map.html` 측에서 줌 레벨 >= 15일 때 `/api/propsheet/map/dong-coords` 호출 구현
4. `ENABLE_DONG_CLUSTERING=true` 전환 후 프로덕션 검증
5. NSDI `getLdaregAplyInfo` 응답 실데이터 확인 (현재 래퍼만 준비됨)

## 롤백 절차

```
# 1. Blueprint 제거 (app.py 복원)
cp /home/webapp/goldenrabbit/backend/propsheet/app.py.bak.week2 /home/webapp/goldenrabbit/backend/propsheet/app.py
cp /home/webapp/goldenrabbit/backend/property-manager/app.py.bak.week2 /home/webapp/goldenrabbit/backend/property-manager/app.py
cp /home/webapp/goldenrabbit/backend/property-manager/routes/app_api.py.bak.week2 /home/webapp/goldenrabbit/backend/property-manager/routes/app_api.py
cp /home/webapp/goldenrabbit/backend/.env.bak.week2 /home/webapp/goldenrabbit/backend/.env

# 2. 재시작
sudo systemctl restart property-manager proppedia propsheet

# 3. (선택) DB 컬럼 드롭
sudo -u postgres psql -d goldenrabbit_db -c "ALTER TABLE goldenrabbit01_sales_building DROP COLUMN IF EXISTS bd_mgt_sn;"
sudo -u postgres psql -d goldenrabbit_db -c "ALTER TABLE goldenrabbit01_sales_multi_unit DROP COLUMN IF EXISTS bd_mgt_sn;"
sudo -u postgres psql -d goldenrabbit_db -c "DROP TABLE IF EXISTS building_dong_geometry;"
```

## 보안 확인

- VWorld/NSDI 키 하드코딩 없음 (`os.getenv` 사용, `.env` 로딩)
- 업로드 파일에 API 키 문자열 미포함
- `.env.bak.week2` 서버에만 존재, git 대상 아님

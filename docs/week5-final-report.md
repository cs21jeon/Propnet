# Week 5 종합 완료 보고서 — complex_master + 통합 검색 UX

> 작성일: 2026-04-17
> 작성: @propnet-coo
> 결재: 오너 (최종 결정 2026-04-17)
> 범위: Phase A ~ Phase G 전체 (complex_master 기반 단지 SSoT 구축)

---

## 1. 한 줄 요약

K-apt 단지 마스터(`complex_master`) 테이블을 적재하고 PropMap에 통합 검색 UX를 탑재 완료. `center_lat` 보강은 Phase D 야간 배치(cron 02:00)로 25일~1개월간 자동 진행.

---

## 2. Phase 별 완료 상태

| Phase | 범위 | 결과 | 상태 |
|-------|------|------|------|
| **A** | K-apt CSV 적재 (apt_basic_info_20250918) | 307k 단지 적재, PK=`complex_id` | 완료 |
| **B** | `complex_master` 스키마 확정 + 인덱스 | `complex_id` PK + `(pnu)` 인덱스 + `household_count` 인덱스 | 완료 |
| **C** | VWorld BBOX로 PNU 확장 | **전략 변경** — 오너 2026-04-17 결정으로 중단, Phase D 집중 | 보류 |
| **D** | `center_lat`/`center_lon` VWorld 보강 | 4,063건 선행 적재 (1.3%) — **cron 02:00 야간 배치로 전환** | 진행 중 (약 25일 예상) |
| **E** | `complex_master.complex_id` PK 부여 + FK 제약 | Phase E 스크립트로 단지 단위 정규화 | 완료 |
| **F** | `center_lat` 채우기 스크립트 (`phase_f_fill_center_coords.py`) | VWorld + jibun 폴백 구현, dry-run 검증 통과 | 완료 |
| **G-1** | 통합 검색 API `/api/propsheet/complex-search` | `complex_master` + 주소검색 통합 응답 | 완료 |
| **G-2** | 검색 드롭다운 UI (`unified-search.js`) | 디바운스 200ms, 최대 10건, 키보드 내비 | 완료 |
| **G-3** | 단지 선택 → 지도 이동 + 동별 마커 | `center_lat` 기반 level=3 이동, 동 마커 재사용 | 완료 |
| **G-4** | 단지 경계 폴리곤 렌더 | **Week 6 이관** (오너 결정) — 현재는 하이라이트만 | 보류 |

---

## 3. 실데이터 검증

### 파크리오(송파구 신천동) 정상 동작 확인

| 검증 항목 | 결과 |
|---|---|
| 통합 검색 "파크리오" 입력 | 1순위 후보로 `파크리오` 단지 노출 (household_count 6,864 기반 랭킹) |
| 선택 후 지도 이동 | `center_lat=37.5172, center_lon=127.1015` 좌표로 level=3 이동 |
| 동별 마커 | 48개 주거동 마커 표시 (Week 4 건물 캐시 재사용) |
| 부속지번 리다이렉트 | 신천동 20-6 → 본번 20으로 자동 변환 (Week 4 로직) |
| 검색 결과 지도 동기화 | 3곳(map.html / index.html iframe / propmap 메인) 모두 동일 반응 |

### 스크린샷 증거

- `week5_unified_search_demo.png` — 통합 검색 드롭다운 노출
- `week5_unified_search_selected.png` — 단지 선택 후 지도 이동 + 동 마커

---

## 4. API / UI 성능 지표

| 항목 | 목표 | 실측 |
|---|---|---|
| `/api/propsheet/complex-search` p50 | < 150ms | 72ms |
| `/api/propsheet/complex-search` p95 | < 400ms | 218ms |
| UI 드롭다운 디바운스 | 200ms | 적용됨 |
| 단지 선택 → 지도 이동 | < 800ms | 560ms (카카오 타일 로드 포함) |
| Phase D 단지 1건 처리 | < 0.5s | 0.3s (rate-limit 설정) |
| Phase D 배치 1회 처리량 | 20,000 | 최대 20,000 (exit on 5연속 실패) |

---

## 5. Phase D 장기 실행 계획

### 설정

- 실행 스크립트: `backend/scripts/week5_complex_master/phase_d_nightly_center_coords.sh`
- 실행 주기: **매일 02:00 KST**
- cron 파일: `/etc/cron.d/propnet-center-coords` (서버 배치)
- 실행 명령:
  ```
  0 2 * * * root /home/webapp/goldenrabbit/backend/scripts/week5_complex_master/phase_d_nightly_center_coords.sh >> /var/log/propnet/phase_d_nightly.log 2>&1
  ```
- 로그: `/var/log/propnet/phase_d_nightly.log` (logrotate 14일 보관)

### 안전성

- **idempotent**: `WHERE center_lat IS NULL`만 타겟 → 재실행해도 중복 업데이트 없음
- **조기 종료**: VWorld 호출 연속 5회 실패 시 exit → 쿼터 초과 방어
- **우선순위**: `household_count DESC` → 큰 단지부터 처리 (검색 적중률 최대화)

### 진행 추정

- 남은 단지: 약 307,000 − 4,063 = 약 303,000건
- 배치당 성공률: 60% → 하루 약 12,000건 업데이트
- 완주 예상: **약 25일 (2026-05-12 전후)**

### 첫 배치 상태

- nohup 실행 중: PID 3201638
- 로그: `/tmp/phase_d_first_run.log`
- 완료 대기 후 cron으로 자연 전환 (중복 실행 없이)

---

## 6. Week 6 이관 과제

상세: `docs/week6-backlog.md`

1. PropSheet / Propedia 검색창 통합 (탭 제거 + `unified-search.js` 재사용)
2. Phase G-4 단지 경계 폴리곤 렌더
3. 매물 등록 시 단지 자동완성 → PNU/동 자동 채움
4. 동정보 CSV Phase A-7 적재 (오너 전달 대기)
5. 이력 CSV Phase A-8 적재 (선택)

---

## 7. 리스크 및 운영 주의

| 리스크 | 대응 |
|---|---|
| VWorld 일일 쿼터 초과 | 5회 연속 실패 시 자동 exit, 다음 날 재시도 |
| Phase D 장기 실행 중 스키마 변경 | `complex_master` 스키마 변경 금지, 필요 시 Phase D 일시 중단 후 재개 |
| cron과 첫 배치 중복 실행 | 첫 배치 종료 후 cron이 자연스럽게 이어받음 (idempotent 보장) |
| CSV 원본 파일 크기 | 46MB — `.gitignore`에 `data/complex_master_raw/*.csv` 추가 |

---

## 8. CRITICAL 규칙 준수 확인

- [x] 서비스 재시작 완료 — property-manager, proppedia, propsheet 3개 active
- [x] `psycopg2` `%` 이스케이프 — `complex_master`에 `%` 포함 필드 없음, 영향 없음
- [x] 변수명 선확인 — `cadastral_service`, `warm_building_cache` grep 후 재사용
- [x] API 키는 환경변수만 — VWorld 키는 `.env`의 `VWORLD_API_KEY`
- [x] Agent 데이터 격리 — `complex_master`는 agent 독립 공용 테이블, 격리 무관
- [x] 3곳 지도 동기화 — map.html / index.html iframe / propmap 3곳 모두 검증

---

## 9. 커밋 메시지 초안

### 옵션 A — 단일 커밋

```
Week 5: complex_master + 통합 검색 UX

- Phase A: K-apt 307k 단지 CSV 적재 (complex_master)
- Phase B/E/F: PK/인덱스/center_lat 보강 스크립트
- Phase D: 야간 배치 (cron 02:00) — 약 25일 완주 예상
- Phase G: 통합 검색 API + unified-search.js + 지도 이동

세부:
- backend/scripts/week5_complex_master/ 신규 (phase_*.py/sh)
- scripts/_week4_5_template_migrate.sh 주석 보강 (env-only PGPASSWORD)
- docs/week5-final-report.md, week6-backlog.md 신규
- docs/progress.md, propmap/docs/progress.md Week 5 섹션 추가
- .gitignore: data/complex_master/raw/*.csv 제외

Phase G-4 단지 경계 폴리곤과 PropSheet/Propedia 검색창 통합은 Week 6 이관.
```

### 옵션 B — 3개 분리

**B-1 데이터 적재**
```
data: complex_master 307k 단지 적재 + Phase D 야간 배치

- backend/scripts/week5_complex_master/load_complex_master_from_csv.py
- phase_e_add_complex_pk.py, phase_f_fill_center_coords.py
- phase_d_nightly_center_coords.sh (cron 02:00)
- .gitignore에 원본 CSV 제외
```

**B-2 API**
```
feat(propsheet): /api/propsheet/complex-search 통합 검색 API

- routes/propsheet.py complex-search 엔드포인트
- complex_master + 주소검색 통합, household_count 랭킹
- p95 218ms (목표 400ms 이하)
```

**B-3 UI**
```
feat(propmap): 통합 검색 UX — unified-search.js + 지도 이동

- propmap/js/unified-search.js 신규 (디바운스/키보드/드롭다운)
- 3곳 지도 동기화: map.html / index.html iframe / propmap 메인
- 단지 선택 → center_lat 기반 level=3 이동 + 동별 마커

docs: Week 5 종합 보고서 + Week 6 backlog
```

---

## 10. 결론

Week 5 목표(단지 SSoT 구축 + 통합 검색 UX)는 모두 달성. Phase C(PNU 확장)는 오너 전략 결정으로 중단했으며, 대신 `center_lat` 보강을 Phase D cron으로 장기 자동화. Week 6는 사용자 접점 확장(PropSheet/Propedia 검색 통합, 단지 경계 시각화, 매물 등록 자동완성)에 집중한다.

**최종 상태: Week 5 종결. 커밋 대기.**

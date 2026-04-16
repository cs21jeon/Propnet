# Week 3 — QA 종합 테스트 리포트

> 최종 업데이트: 2026-04-16 (서버 배포 + E2E 검증 완료)
> 테스터: @qa-lead (Week 3 배포 검증)
> 대상: PropMap 동 단위 클러스터링 + 캐시 워밍

## 1. 서버 배포 검증

### 1-1. 파일 업로드 결과
| 파일 | 로컬 원본 | 서버 최종 | 결과 |
|---|---:|---:|---|
| `backend/property-manager/services/cadastral_service_dong_ext.py` | 15,926 B | 수정 후 서버 동기화 OK | PASS |
| `backend/property-manager/routes/map_dong.py` | 4,003 B | 수정 후 서버 동기화 OK | PASS |
| `scripts/warm_building_cache.py` | 15,899 B | 수정 후 서버 동기화 OK | PASS |
| `frontend/public/propmap/js/dong-cluster-renderer.js` | 9,775 B | 수정 후 서버 동기화 OK | PASS |
| `frontend/public/propmap/map.html` | 79,022 B | 수정 후 서버 동기화 OK | PASS |

백업(`*.bak.week3`)은 서버에 보존.

### 1-2. 서비스 재시작
```
sudo systemctl restart property-manager proppedia propsheet
```
- property-manager: active
- proppedia: active
- propsheet: active
- 시작 로그 전체에 `[CadastralExt] 확장 메서드 주입 완료` 포함 (3개 모두)

### 1-3. Health endpoint
```
curl https://propnet.kr/propsheet/api/propsheet/map/dong-coords/health
→ {"enabled":true, "public_api_key":true, "success":true, "vworld_key":true}  HTTP 200
```

## 2. 실데이터 API 테스트

| # | 입력 | 결과 | 판정 |
|---|------|------|------|
| T1 | `?pnu=1171010200100170000` (파크리오) | HTTP 200, dongs=81 (파크리오 주거동 48개 + 부속시설/인접 33) | PASS |
| T2 | `?address=서울특별시 동작구 사당동 1132` | HTTP 200, pnu=1159010700111320000, dongs=22, 롯데캐슬 104동(37.49065,126.97264)/106동(37.49106,126.97270) 좌표 분리 | PASS |
| T3a | `?address=서울특별시 송파구 신천동 20-6` | HTTP 200, pnu=1171010200100200000 (본번 정규화), dongs=140 | PASS |
| T3b | `?pnu=1171010200100200006` (부번 6) | HTTP 200, 리다이렉트 후 pnu=1171010200100200000, dongs=140 | PASS |

상세 JSON 응답 분석: `docs/week3-wfs-test-results.md`

## 3. 캐시 워밍 실행

| agent | 유니크 지번 | PNU 해석 | 캐시된 동 | bd_mgt_sn 업데이트 |
|---|---:|---:|---:|---:|
| goldenrabbit | 449 | 446 | ~11,930 (partial, timeout 900s) | 17 / 455 |
| silverrabbit | 17 | 17 | 1,504 | 스킵 (컬럼 없음) |
| propnet | 4 | 4 | 1,176 | 스킵 (컬럼 없음) |
| **합계** | **470** | **467** | **12,118** (unique pnus: 10,847) | **17** |

### 배포 중 발견/수정한 이슈 (9건)
1. `get_db_connection()`이 contextmanager인데 `conn.close()` 직접 호출 → `with get_db_connection() as conn:` 패턴으로 수정 (warm_building_cache.py, cadastral_service_dong_ext.py)
2. `bd_mgt_sn varchar(25)` vs VWorld ufid 28자 → 3개 테이블 `varchar(32)`로 ALTER
3. VWorld WFS typename 대소문자: `LT_C_BLDGINFO` → `lt_c_bldginfo` (소문자만 허용)
4. BBOX 반경 150m → 400m (파크리오, 송파 주공 등 대형 단지 커버)
5. PropSheet 스키마에 맞게 `list_agent_tables`가 `databases`+`workspaces` 조인으로 agent 매물 테이블 탐지 (기존 `agent_property_tables` 테이블 가정은 실제 스키마와 불일치)
6. `"지번 주소"` 공백 포함 컬럼명 감지 추가 (기존 "지번주소"만)
7. 좌표 컬럼 `coordinates_lat/coordinates_lon` 감지 추가 (기존 `lat/lon`만)
8. `jibun_to_pnu` — VWorld getCoord 응답에서 PNU는 `refined.structure.level4LC` (기존 `result.structure.pnu` 오류)
9. 주소 정규화 — "동작구 상도동 499-19"처럼 광역 prefix 누락 시 "서울특별시 " 자동 보강

### 잔여 관측
- `ERROR duplicate key value violates unique constraint "building_dong_geometry_pnu_dong_nm_key"` 가끔 발생 — ON CONFLICT 절은 `bd_mgt_sn` 기준이지만 `(pnu, dong_nm)` 유니크 인덱스와 충돌. 캐시 저장 자체는 스킵되고 진행에는 영향 없음. Week 4에서 `ON CONFLICT ... DO NOTHING` fallback 추가 예정
- 매물-건물 자동 매칭률 낮음 (17/455 ≈ 3.7%) — 매물 테이블에 `동` 컬럼이 없거나 비어 있어 `update_records_with_dong`에서 스킵. PropSheet 매물 등록 UI에 동 입력란 강화가 후속 과제

## 4. 프론트엔드 E2E 검증 (Chrome Playwright)

### 4-1. 페이지 로딩
- `https://propnet.kr/propmap/` 로딩 성공
- 사이드바 + 카테고리 + 중개사무소 리스트 정상
- Kakao 지도 렌더 정상
- DongClusterRenderer 전역 로드 확인 (`window._dongRenderer`)
- 설정: `_enabled: true`, `zoomThreshold: 3`, `apiUrl: /propsheet/api/propsheet/map/dong-coords`

### 4-2. 동 클러스터 렌더링
| 확인 항목 | 결과 |
|---|---|
| level ≤ 3 줌 인 시 동별 마커 생성 | PASS (예: center 37.59,127.05 / level 3 → 48개 동 마커 렌더) |
| 매물 있는 동: 파란 배경 + 매물 수 표시 | PASS (예: "9697만", "7000만") |
| 매물 없는 동: 회색 점선 윤곽 + 0.45 투명도 | PASS (예: 레지던스K, 평화빌라, 교사(K)동, 전기(J)실) |
| level > 3 줌 아웃 시 동 마커 제거 | PASS (level 5에서 동 마커 0개) |
| 줌 전환 시 idle/zoom_changed 이벤트로 재렌더 | PASS |

스크린샷:
- `propmap-dong-clusters-final.png` — 줌 3, 동 마커 48개 + 가격 마커 2개 표시
- `propmap-zoom-out.png` — 줌 5, 동 마커 모두 제거됨

### 4-3. 프론트엔드 수정 내역
1. **map-data API 응답에 pnu/지번주소 부재** — 기존 API는 `lat/lon/agent_slug`만 반환. dong-cluster-renderer가 pnu/address key를 못 찾아 그룹핑 실패 (330개 매물 → 0개 그룹)
   → `dong-cluster-renderer.js`에 **lat/lon 격자(소수점 3자리 ≈ 100m) key fallback** 로직 추가
2. **grid key가 19자라서 PNU로 오판** — `"grid:37.590,127.049"` 길이 정확히 19자 → 기존 `key.length === 19`만으로 PNU 판정. `?pnu=grid%3A37.590...` 로 잘못 전송되어 404
   → `/^\d{19}$/` 정규식 체크 추가해 실제 숫자 PNU만 pnu 파라미터로 전송
3. cache-bust query (`?v=20260416d`) 추가 — 기존 브라우저 캐시로 인한 구 버전 JS 혼선 방지

## 5. 기능 플래그

```
/home/webapp/goldenrabbit/backend/.env
ENABLE_DONG_CLUSTERING=true   (Week 2: false → Week 3 활성화)
```

- 재시작 후 health endpoint가 `enabled: true` 반환 (확인됨)
- 플래그 off로 되돌리면 dong-coords 엔드포인트가 503 반환 → 회귀 시 즉시 비활성화 가능

## 6. 홈페이지 매물지도 (frontend/public/map.html) 동기화

- 홈페이지 `frontend/public/map.html`은 독립적인 price-marker 기반 구현으로 cluster 로직이 다름
- dong-cluster-renderer는 현재 `/propmap/` 전용으로만 배포
- 3곳 동기화 원칙은 propmap 경로(`propmap/map.html` + `propmap/index.html` iframe 자동 반영)에만 해당
- 홈페이지 매물지도 이관은 Week 4 범위 (propmap 통합 시점)로 보류

## 종합 판정: PASS (조건부)

- 서버/프론트 모두 정상 동작
- 3가지 실데이터 시나리오 모두 기대치 이상 반환
- 동 마커 렌더/줌 전환 정상
- 캐시 저장 정상 (12,118건, 10,847 유니크 PNU)
- 매물-건물 자동 매칭률은 낮음 (~3.7%) — 매물측 `동` 컬럼 부재가 원인이며 Week 4 개선 과제

## 롤백 가이드
문제 발생 시:
1. 플래그 끄기
   ```
   sed -i 's/^ENABLE_DONG_CLUSTERING=true/ENABLE_DONG_CLUSTERING=false/' /home/webapp/goldenrabbit/backend/.env
   sudo systemctl restart property-manager proppedia propsheet
   ```
2. 백업 파일 복원
   - `/home/webapp/goldenrabbit/backend/property-manager/services/cadastral_service_dong_ext.py.bak.week3`
   - `/home/webapp/goldenrabbit/backend/property-manager/routes/map_dong.py.bak.week3`
   - `/home/webapp/goldenrabbit/frontend/public/propmap/map.html.bak.week3`
   - `/home/webapp/goldenrabbit/backend/.env.bak.week3`
3. building_dong_geometry는 캐시 테이블이라 데이터 유지해도 무방 (필요 시 `TRUNCATE building_dong_geometry`)
4. bd_mgt_sn varchar 확장은 롤백 불필요 (하위 호환)

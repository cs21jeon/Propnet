# Week 3 — 배포/테스트 운영 가이드

> 로컬 작업이 끝난 뒤, 서버(MCP 또는 SSH)에서 실행하는 절차 모음.

## 0. 준비물

- MCP: `goldenrabbit-server` 연결 (또는 `ssh root@175.119.224.71`)
- `.env`에 `VWORLD_APIKEY`, `PUBLIC_API_KEY` 설정 확인
- 로컬 변경 파일 목록:
  ```
  backend/property-manager/services/cadastral_service_dong_ext.py  (수정)
  backend/property-manager/routes/map_dong.py                      (수정)
  scripts/warm_building_cache.py                                   (신규)
  propmap/js/dong-cluster-renderer.js                              (신규)
  propmap/map.html                                                 (수정: dong-cluster 연동 + 팝업 확장)
  propmap/docs/progress.md                                         (업데이트)
  docs/week3-wfs-test-results.md                                   (신규)
  docs/week3-qa-report.md                                          (신규)
  docs/week3-deployment-guide.md                                   (본 문서, 신규)
  ```

## 1. 서버 파일 업로드

### 1.1 Python 서비스 (5000/5010/5020 공유)

```bash
# MCP 또는 SSH로 서버에 업로드
# 목적지:
#   /home/webapp/goldenrabbit/backend/property-manager/services/cadastral_service_dong_ext.py
#   /home/webapp/goldenrabbit/backend/property-manager/routes/map_dong.py
#   /home/webapp/goldenrabbit/scripts/warm_building_cache.py
```

### 1.2 PropMap 정적 파일

```bash
# 목적지:
#   /home/webapp/goldenrabbit/frontend/public/propmap/js/dong-cluster-renderer.js  (신규 디렉토리)
#   /home/webapp/goldenrabbit/frontend/public/propmap/map.html

mkdir -p /home/webapp/goldenrabbit/frontend/public/propmap/js
```

> **주의**: 로컬 `propmap/` ↔ 서버 `frontend/public/propmap/` 매핑. map.html은 agent별 디렉토리 `frontend/public/propmap/goldenrabbit/` 등에도 복사본이 있을 수 있으니 **반드시 모든 agent 디렉토리에 동기화**할 것.

### 1.3 홈페이지 지도(`frontend/public/index.html`, `map.html`) 동기화

로컬에 파일이 없으므로 서버에서 직접 편집 (또는 MCP Read → 로컬 매핑 → 수정 → Write).
필요한 변경:
- `<script src="/propmap/js/dong-cluster-renderer.js"></script>` 추가
- 지도 초기화 부분 뒤에 `DongClusterRenderer.init({ map, properties, ... })` 호출
- `createClusterPopup` (있다면) 내부에 대표 이미지/동별 배지/동별 보기 버튼 추가 (propmap/map.html 참조)

### 1.4 Propmap agent별 서브 디렉토리 동기화

```bash
# 모든 agent 디렉토리 탐색
ls /home/webapp/goldenrabbit/frontend/public/propmap/

# 각 디렉토리의 map.html, index.html에 동일 패치 적용 (또는 공통 js만 재참조)
for dir in /home/webapp/goldenrabbit/frontend/public/propmap/*/; do
  # map.html 만 대상, js 참조 경로가 절대경로 /propmap/js/... 이므로 자동 해결
  echo "Sync target: ${dir}map.html"
done
```

## 2. 서비스 재시작 (CRITICAL 규칙 #2)

```bash
sudo systemctl restart property-manager proppedia propsheet
sleep 2
sudo systemctl status property-manager proppedia propsheet --no-pager | head -30
```

에러 확인:
```bash
journalctl -u property-manager -n 30 --no-pager
journalctl -u proppedia -n 30 --no-pager
journalctl -u propsheet -n 30 --no-pager
```

## 3. 헬스체크 (기능 플래그 아직 OFF)

```bash
curl -s 'https://goldenrabbit.biz/propsheet/api/propsheet/map/dong-coords/health' | jq .
# 기대:
# {"success": true, "enabled": false, "vworld_key": true, "public_api_key": true}
```

## 4. 캐시 워밍 — 드라이런

```bash
cd /home/webapp/goldenrabbit/backend/property-manager
source venv/bin/activate  # /home/webapp/goldenrabbit/backend/venv
cd /home/webapp/goldenrabbit
python scripts/warm_building_cache.py --dry-run --rate-limit 1.0 2>&1 | tee /tmp/warm-dryrun.log
```

리포트 확인:
- `PNU 해석 실패`가 10% 이상이면 원인 조사 (주소 포맷 이슈 가능성)
- `대상 테이블` 수가 예상(agent 수)과 일치하는지 확인

## 5. 실데이터 테스트 (기능 플래그 임시 ON)

```bash
# .env 임시 수정
sudo sed -i 's/^ENABLE_DONG_CLUSTERING=.*/ENABLE_DONG_CLUSTERING=true/' /home/webapp/goldenrabbit/backend/.env
grep ENABLE_DONG_CLUSTERING /home/webapp/goldenrabbit/backend/.env

sudo systemctl restart property-manager proppedia propsheet

# 헬스체크
curl -s 'https://goldenrabbit.biz/propsheet/api/propsheet/map/dong-coords/health' | jq .
# 기대: enabled: true

# 파크리오 테스트
curl -s 'https://goldenrabbit.biz/propsheet/api/propsheet/map/dong-coords?pnu=1171010100100170000&address=%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C%20%EC%86%A1%ED%8C%8C%EA%B5%AC%20%EC%8B%A0%EC%B2%9C%EB%8F%99%2017' | jq '{success, count, center, source, dongs_count: (.dongs | length), dong_nms: [.dongs[].dong_nm]}'

# 사당동 롯데캐슬
curl -s 'https://goldenrabbit.biz/propsheet/api/propsheet/map/dong-coords?pnu=1159010400111320000&address=%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C%20%EB%8F%99%EC%9E%91%EA%B5%AC%20%EC%82%AC%EB%8B%B9%EB%8F%99%201132' | jq '{success, count, dongs_count: (.dongs | length)}'

# 부속지번
curl -s 'https://goldenrabbit.biz/propsheet/api/propsheet/map/dong-coords?pnu=1171010100100200006' | jq .
```

결과를 `docs/week3-wfs-test-results.md`의 Before/After 란에 기록.

## 6. 캐시 워밍 — 실제 실행

드라이런 이상 없을 시:
```bash
python scripts/warm_building_cache.py --rate-limit 1.0 --fallback-ldareg 2>&1 | tee /tmp/warm-real.log

# DB 확인
psql -d goldenrabbit_db -c "SELECT count(*) FROM building_dong_geometry;"
psql -d goldenrabbit_db -c "SELECT count(*) FROM property_goldenrabbit_단일 WHERE bd_mgt_sn IS NOT NULL;"
```

## 7. QA 수동 검증

`docs/week3-qa-report.md` 체크리스트 12개 완수.
특히:
- 파크리오 지도 진입 → 줌 인 → 동 마커 분리 스크린샷 2장 (Before level=4 / After level=3)
- 부속지번 매물(20-6) 지도 표시 스크린샷
- Propedia 앱 결과화면 스크린샷 (pnu_redirect 케이스)

## 8. 최종 배포 (플래그 확정 ON)

QA 통과 시:
```bash
# 이미 ON 상태면 스킵. 아니면:
sudo sed -i 's/^ENABLE_DONG_CLUSTERING=.*/ENABLE_DONG_CLUSTERING=true/' /home/webapp/goldenrabbit/backend/.env
sudo systemctl restart property-manager proppedia propsheet

# 실제 사용자 트래픽 로그 관찰
journalctl -u property-manager -f | grep -E 'CadastralExt|dong-coords'
```

## 9. 롤백 (문제 발생 시)

```bash
# 플래그만 OFF (코드는 유지)
sudo sed -i 's/^ENABLE_DONG_CLUSTERING=.*/ENABLE_DONG_CLUSTERING=false/' /home/webapp/goldenrabbit/backend/.env
sudo systemctl restart property-manager proppedia propsheet

# 검증
curl -s 'https://goldenrabbit.biz/propsheet/api/propsheet/map/dong-coords/health' | jq .
# 기대: enabled: false
```

코드 롤백 필요 시:
```bash
cd /home/webapp/goldenrabbit
git log --oneline backend/property-manager/services/cadastral_service_dong_ext.py | head -5
git checkout <이전커밋> -- backend/property-manager/services/cadastral_service_dong_ext.py backend/property-manager/routes/map_dong.py
sudo systemctl restart property-manager proppedia propsheet
```

## 10. 최종 git 커밋 (오너 승인 후)

로컬 리포에서:
```bash
git status
git diff --cached  # 커밋 전 반드시 민감정보 확인 (CRITICAL #8)
git add \
  backend/property-manager/services/cadastral_service_dong_ext.py \
  backend/property-manager/routes/map_dong.py \
  scripts/warm_building_cache.py \
  propmap/js/dong-cluster-renderer.js \
  propmap/map.html \
  propmap/docs/progress.md \
  docs/week3-wfs-test-results.md \
  docs/week3-qa-report.md \
  docs/week3-deployment-guide.md
```

커밋 메시지 가이드:
```
feat(week3): 동 단위 클러스터링 ON + VWorld WFS Filter 제거

- get_buildings_by_pnu: Data API attrFilter + BBOX 150m 방식 전환
- resolve_to_main_pnu: Filter XML 제거 (부속지번 → 본번 리다이렉트)
- propmap/js/dong-cluster-renderer.js: 줌 레벨 기반 동 마커 렌더러
- propmap/map.html: 단지 팝업 대표 이미지 + 동별 보기 버튼
- scripts/warm_building_cache.py: 기존 레코드 bd_mgt_sn/좌표 배치 업데이트
- docs: Week 3 WFS 테스트 결과 + QA 리포트 + 배포 가이드
```

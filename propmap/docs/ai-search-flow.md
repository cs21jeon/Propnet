# AI 매물 검색 — 백엔드 동작 흐름도

## 아키텍처 개요

```
프론트엔드 (PropMap)
    │
    ▼
routes/ai_search.py          ← Flask Blueprint (POST /api/ai/*)
    │
    ▼
ai_agent_service.py           ← Claude 에이전트 루프 (도구 자율 선택)
    │
    ├── ai_tools.py            ← 3개 도구 실행기
    │    ├── search_properties
    │    ├── get_property_detail
    │    └── present_recommendations
    │
    ├── enrichment_service.py  ← 매물 주변 정보 (지하철/학교)
    ├── ai_outlier_detector.py ← 이상치 탐지
    └── ai_billing_service.py  ← 크레딧 과금
```

### 핵심 파일 위치 (서버)

| 파일 | 경로 | 역할 |
|------|------|------|
| ai_search.py | routes/ | API 엔드포인트 (세션/채팅/피드백) |
| ai_agent_service.py | services/ | Claude 에이전트 루프 |
| ai_tools.py | services/ | DB 조회 도구 3종 |
| ai_agent_prompts.py | prompts/ | 에이전트 시스템 프롬프트 |
| enrichment_service.py | services/ | 주변 정보 자동 계산 |
| ai_outlier_detector.py | services/ | 가격/면적 이상치 탐지 |
| ai_billing_service.py | services/ | 크레딧 체크/차감 |

---

## 실제 예시: "역세권 수익률 높은 다가구 주택 추천해 줘"

### 턴 1: 첫 질문

```
사용자: "역세권 수익률 높은 다가구 주택 추천해 줘"
```

#### Step 1. 세션 생성

```
POST /api/ai/session
  → UUID 생성: 448181b8-721c-...
  → ai_search_sessions INSERT (state='INIT')
  → 응답: {"session_id": "448181b8-..."}
```

#### Step 2. 채팅 요청

```
POST /api/ai/chat
  body: {"session_id": "448181b8-...", "text": "역세권 수익률 높은 다가구 주택 추천해 줘"}
```

#### Step 3. post_chat() 전처리

```python
# routes/ai_search.py

1) 크레딧 체크 — ai_billing.check_can_search(uid, role)
2) Anthropic 클라이언트 생성 (CLAUDE_API_KEY 환경변수)
3) 세션 로드 + 사용자 메시지를 ai_search_logs에 저장
4) 이전 messages 복원 (첫 턴이므로 빈 배열)

messages = [
    {"role": "user", "content": "역세권 수익률 높은 다가구 주택 추천해 줘"}
]
```

#### Step 4. 에이전트 루프 — run_agent_turn()

```python
# ai_agent_service.py

resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2500,
    system=AGENT_SYSTEM_PROMPT,   # "당신은 한국 부동산 플랫폼 propnet의..."
    tools=ALL_TOOLS,               # [search_properties, get_property_detail, present_recommendations]
    messages=messages,
)
```

#### Step 5. Claude 판단 — 확인 질문 (도구 호출 없음)

시스템 프롬프트 규칙: "첫 턴에는 반드시 한 번의 따뜻한 확인 질문을 먼저"

```
stop_reason = "end_turn" (도구 호출 없이 평문 응답)

Claude: "좋은 조건을 말씀해 주셨네요! 😊
         희망하시는 지역이나 예산 범위가 있으신가요?"
```

→ 1회 반복으로 종료. `state='GATHERING'`

---

### 턴 2: 조건 추가 → 검색 → 추천

```
사용자: "동작구 20억 이내"
```

#### Step 6. messages 복원

```python
messages = [
    {"role": "user",      "content": "역세권 수익률 높은 다가구 주택 추천해 줘"},
    {"role": "assistant", "content": "좋은 조건을 말씀해 주셨네요! ..."},
    {"role": "user",      "content": "동작구 20억 이내"},    # ← 새 메시지
]
```

#### Step 7. 에이전트 루프 iteration 1 — search_properties

```python
resp = client.messages.create(...)
# stop_reason = "tool_use"
```

Claude가 반환한 tool_use 블록:

```json
{
  "name": "search_properties",
  "input": {
    "transaction_type": "매매",
    "property_types": ["다가구"],
    "region_keywords": ["동작구"],
    "price_max_manwon": 200000,
    "sort_by": "yield_desc",
    "limit": 15
  }
}
```

#### Step 8. 도구 실행 — execute_search_properties()

```python
# ai_tools.py

# 1) 테이블별 SQL 조립
#    "다가구" → LLM_TYPE_TO_DB_MAP → db39: ["주택"], db38: [] (빈 리스트 → 건너뜀)
#    → 결과적으로 db39(단일부동산)만 쿼리

# 2) SQL 실행
SELECT
    39::int AS db_id,
    record_id AS rid_raw,
    "지번 주소" AS addr,
    "매물종류" AS property_type,
    "종류" AS transaction_type,
    "매가(만원)" AS price_manwon,
    "융자제외수익률(%%)" AS yield_pct,
    "건폐율(%%)" AS coverage_ratio_pct,
    "용적률(%%)" AS floor_area_ratio_pct,
    coordinates_lat AS lat,
    coordinates_lon AS lon,
    "대표사진" AS photo_url,
    "광고" AS ad_text,
    created_at, updated_at
FROM goldenrabbit01_sales_building
WHERE coordinates_lat IS NOT NULL
  AND coordinates_lon IS NOT NULL
  AND "매가(만원)" IS NOT NULL AND "매가(만원)" > 0
  AND "대표사진" IS NOT NULL AND "광고" IS NOT NULL
  AND ("건폐율(%%)" IS NULL OR "건폐율(%%)" <= 100)
  AND ("용적률(%%)" IS NULL OR "용적률(%%)" <= 2000)
  AND "종류" = '매매'
  AND "매가(만원)" <= 200000
  AND "매물종류" IN ('주택')
  AND "지번 주소" ILIKE '%동작구%'
ORDER BY yield_pct DESC NULLS LAST
LIMIT 30

# 3) 이상치 필터 — outlier.hard_exclude()
#    가격 <= 0, 좌표 없음, 건폐율 > 100 등 제거

# 4) Enrichment 데이터 병합 (Phase 1)
for item in compact:
    rid = "39:recXXX".split(':')[1]  # → "recXXX"
    enr = enrichment_service.get_enrichment(conn, rid, 39)
    # → property_enrichment 테이블 조회
    #   SELECT nearest_subway, nearby_schools FROM property_enrichment
    #   WHERE record_id = 'recXXX' AND db_id = 39
    if enr:
        subway = enr['nearest_subway'][0]  # 최근접역
        item['nearest_subway'] = "상도역(7호선) 도보6.2분"
        item['subway_distance_m'] = 496
        schools = enr['nearby_schools']
        item['nearby_school_count'] = 9
        item['nearest_school'] = "상도초등학교(초등학교) 280m"

# 5) 결과 반환
return {
    "count": 15,
    "results": [
        {
            "record_id": "39:recgbiWq...",
            "db_id": 39,
            "addr": "동작구 상도동 17-51",
            "property_type": "주택",
            "transaction_type": "매매",
            "price_manwon": 175000,
            "yield_pct": 8.0,
            "ad_summary": "상도동 수익형 다가구주택...",
            "nearest_subway": "상도역(7호선) 도보5분",     # ← Enrichment
            "subway_distance_m": 408,                       # ← Enrichment
            "nearby_school_count": 9,                       # ← Enrichment
            "nearest_school": "상도초등학교(초등학교) 280m" # ← Enrichment
        },
        ...
    ]
}
```

→ `observed_record_ids`에 15개 record_id 등록 (환각 방어용)

#### Step 9. tool_result → messages에 추가

```python
messages.append({"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "toolu_xxx",
     "content": '{"count": 15, "results": [...]}'}
]})
```

#### Step 10. 에이전트 루프 iteration 2 — present_recommendations

```python
resp = client.messages.create(...)
# Claude가 15건 결과를 분석하여 상위 5개 선별
# stop_reason = "tool_use"
```

Claude가 반환:

```json
{
  "name": "present_recommendations",
  "input": {
    "selections": [
      {
        "record_id": "39:recgbiWq...",
        "db_id": 39,
        "rank": 1,
        "reason": "수익률 8.0%로 최고. 상도역(7호선) 도보 5분 역세권이며 매매가 17억 5천만원.",
        "warnings": []
      },
      {
        "record_id": "39:recJwf3r...",
        "db_id": 39,
        "rank": 2,
        "reason": "숭실대입구역(7호선) 도보 4분 초역세권. 매매가 9억 9천만원으로 부담 적음.",
        "warnings": []
      },
      ...
    ],
    "summary": "동작구 20억 이내 다가구 주택 중 수익률과 역세권 조건을 모두 충족하는 상위 5곳..."
  }
}
```

#### Step 11. 도구 실행 — execute_present_recommendations()

```python
# ai_tools.py — 환각 방어

valid = []
rejected = []
for sel in selections:
    if sel['record_id'] in observed_record_ids:
        valid.append(sel)       # search_properties에서 실제 조회된 record_id만 통과
    else:
        rejected.append(sel)    # Claude가 지어낸 record_id는 거부

return {
    "accepted": 5,
    "rejected": [],
    "selections": valid,
    "summary": "동작구 20억 이내 다가구 주택 중..."
}
```

#### Step 12. 에이전트 루프 iteration 3 — 최종 평문

```python
resp = client.messages.create(...)
# stop_reason = "end_turn"

Claude: "동작구 20억 이내 다가구 주택 중 수익률과 역세권 조건을
         모두 충족하는 상위 5곳을 추려드렸어요.
         관심 가시는 매물이 있으시면 '1번 자세히 알려줘'라고 말씀해 주세요!"
```

→ run_agent_turn 종료

#### Step 13. post_chat() 후처리

```python
# routes/ai_search.py

# 1) ai_search_logs에 저장
_save_log(cur, session_id, turn_index=2, role="assistant", text="동작구 20억 이내...")
_save_log(cur, session_id, turn_index=2, role="tool",
          text='{"tool": "search_properties", "input": {...}, "result_preview": "..."}')
_save_log(cur, session_id, turn_index=2, role="tool",
          text='{"tool": "present_recommendations", "input": {...}, ...}')

# 2) ai_search_results에 추천 결과 저장
INSERT INTO ai_search_results
    (session_id, stage, record_ids, db_ids, scores, meta_json)
VALUES ('448181b8-...', 'agent',
        '{39:recgbiWq..., 39:recJwf3r..., ...}',
        '{39, 39, 39, 39, 39}',
        '{1, 2, 3, 4, 5}',
        '{"summary": "동작구 20억 이내...", "rejected": []}')

# 3) 세션 상태 갱신
UPDATE ai_search_sessions
SET turn_count = 2,
    state = 'RANKED',
    total_tokens_in = total_tokens_in + 25179,
    total_tokens_out = total_tokens_out + 1568

# 4) 크레딧 차감
ai_billing.deduct_credit(cur, uid, session_id, role=role)

# 5) conn.commit()
```

#### Step 14. JSON 응답 → 프론트엔드

```json
{
  "assistant_text": "동작구 20억 이내 다가구 주택 중 수익률과 역세권...",
  "recommendations": {
    "accepted": 5,
    "rejected": [],
    "selections": [
      {"record_id": "39:recgbiWq...", "rank": 1,
       "reason": "수익률 8.0%...상도역 도보 5분", "warnings": []},
      {"record_id": "39:recJwf3r...", "rank": 2,
       "reason": "숭실대입구역 도보 4분 초역세권...", "warnings": []},
      ...
    ],
    "summary": "..."
  },
  "credit_after": {"remaining": 9, "plan": "free"},
  "tool_log": [
    {"tool": "search_properties", "input": {...}, "result_preview": "..."},
    {"tool": "present_recommendations", "input": {...}, "result_preview": "..."}
  ],
  "turn_index": 2,
  "iterations": 3,
  "stopped": "end_turn",
  "usage": {"input_tokens": 25179, "output_tokens": 1568}
}
```

---

## 전체 흐름도 (턴 2 기준)

```
사용자: "동작구 20억 이내"
  │
  ▼
POST /api/ai/chat ─────────────────────────────────────────────
  │ 크레딧 체크 → 세션 로드 → messages 복원                    │
  ▼                                                             │
run_agent_turn() ── 에이전트 루프 시작                          │
  │                                                             │
  ├─ [iter 1] Claude API 호출                                   │
  │   Claude 판단: "검색이 필요하다"                            │
  │   → tool_use: search_properties                             │
  │     │                                                       │
  │     ▼ execute_search_properties()                           │
  │     ├─ LLM_TYPE_TO_DB_MAP: "다가구" → db39만 쿼리          │
  │     ├─ SQL: WHERE 종류='매매' AND 매가<=200000              │
  │     │        AND 매물종류 IN ('주택')                        │
  │     │        AND 지번주소 ILIKE '%동작구%'                   │
  │     ├─ outlier.hard_exclude() — 이상치 제거                 │
  │     ├─ enrichment_service.get_enrichment() — 역/학교 병합   │
  │     └─ 반환: 15건 (역세권 정보 포함)                        │
  │                                                             │
  │   tool_result → messages에 추가                             │
  │                                                             │
  ├─ [iter 2] Claude API 호출                                   │
  │   Claude 판단: "15건 중 상위 5개를 추천하자"                │
  │   → tool_use: present_recommendations                       │
  │     │                                                       │
  │     ▼ execute_present_recommendations()                     │
  │     ├─ 환각 방어: record_id ∈ observed_record_ids 검증      │
  │     └─ 반환: 5건 선별 + 추천 이유                           │
  │                                                             │
  │   tool_result → messages에 추가                             │
  │                                                             │
  ├─ [iter 3] Claude API 호출                                   │
  │   Claude 판단: "추천 완료, 요약 메시지를 보내자"            │
  │   → end_turn (평문 응답)                                    │
  │                                                             │
  ▼                                                             │
run_agent_turn() 종료                                           │
  │                                                             │
  ▼                                                             │
post_chat() 후처리                                              │
  ├─ ai_search_logs 저장 (대화 + 도구 호출 기록)                │
  ├─ ai_search_results 저장 (추천 record_ids)                   │
  ├─ ai_search_sessions 갱신 (state, tokens, turn_count)        │
  ├─ 크레딧 차감                                                │
  └─ conn.commit()                                              │
  │                                                             │
  ▼                                                             │
JSON 응답 반환 ─────────────────────────────────────────────────
  │
  ▼
프론트엔드: 추천 카드 렌더링
```

---

## DB 테이블 구조

### 매물 테이블 (조회 대상)

| 테이블 | db_id | 유형 | property_type 컬럼 | transaction_type 컬럼 | yield 컬럼 |
|--------|-------|------|--------------------|-----------------------|------------|
| goldenrabbit01_sales_building | 39 | 단일부동산 | "매물종류" | "종류" | "융자제외수익률(%)" |
| goldenrabbit01_sales_multi_unit | 38 | 집합부동산 | "물건종류" | "종류" | NULL (없음) |

### LLM 유형 → DB enum 매핑

| 사용자 표현 | db39 (단일) | db38 (집합) |
|------------|-------------|-------------|
| 아파트 | - | 아파트 |
| 빌라, 다세대 | - | 빌라 |
| 단독주택, 다가구 | 주택 | - |
| 상가주택 | 건물, 주택 | - |
| 상가 | 건물 | 상가 |
| 빌딩, 근린생활시설 | 건물 | - |
| 오피스텔 | - | 오피스텔 |
| 토지 | 토지 | - |

### AI 검색 세션/로그 테이블

| 테이블 | 용도 |
|--------|------|
| ai_search_sessions | 세션 메타 (상태, 턴 수, 토큰 사용량) |
| ai_search_logs | 대화 턴별 기록 (user/assistant/tool) |
| ai_search_results | 추천 결과 스냅샷 (record_ids, scores) |
| ai_feedback | 사용자 피드백 (good/bad/clicked) |
| property_view_events | 매물 노출/클릭/문의 이벤트 |

### Enrichment 테이블 (Phase 1)

| 테이블 | 용도 | 데이터 수 |
|--------|------|----------|
| subway_stations | 지하철역 마스터 (역명, 노선, 좌표) | 404개역 |
| schools | 학교 마스터 (학교명, 유형, 좌표) | 3,223개교 |
| property_enrichment | 매물별 캐시 (최근접역, 주변학교) | 매물 수와 동일 |

---

## 에이전트 도구 3종

### 1. search_properties — 매물 검색

```
입력: transaction_type, region_keywords, property_types, price_min/max, yield_min, sort_by, limit
처리: UNION ALL SQL → 이상치 필터 → Enrichment 병합
출력: [{record_id, addr, price, yield, nearest_subway, nearby_school_count, ...}]
```

### 2. get_property_detail — 매물 상세

```
입력: record_id, db_id
처리: 단건 SQL 조회 → Enrichment 병합
출력: {addr, price, yield, building_area, land_area, ad_text, enrichment: {nearest_subway, nearby_schools}}
```

### 3. present_recommendations — 최종 추천

```
입력: selections [{record_id, rank, reason, warnings}], summary
처리: 환각 방어 (observed_record_ids 검증)
출력: {accepted, rejected, selections, summary}
```

---

## 보안/방어 메커니즘

| 메커니즘 | 위치 | 설명 |
|----------|------|------|
| 환각 방어 | present_recommendations | search_properties에서 조회된 record_id만 추천 허용 |
| 크레딧 과금 | post_chat | 추천 성공 시에만 차감 |
| 세션 턴 상한 | post_chat | 세션당 최대 8턴 (API 비용 방지) |
| 도구 반복 상한 | run_agent_turn | 턴당 최대 6회 도구 호출 |
| 이상치 탐지 | hard_exclude | 가격 0 이하, 좌표 없음, 건폐율 > 100 등 즉시 제거 |
| 프롬프트 주입 방어 | AGENT_SYSTEM_PROMPT | "이전 지시 무시" 요청 무시 규칙 |
| 개인정보 보호 | AGENT_SYSTEM_PROMPT | 소득/가족/직업 등 절대 묻지 않음 |

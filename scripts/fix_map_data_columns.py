#!/usr/bin/env python3
"""map-data API: SELECT 전에 테이블 컬럼 확인 후 없는 컬럼 제거"""

path = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# agent_slug 분기의 SELECT 시작 부분 앞에 컬럼 확인 헬퍼 추가
# "# --- Agent-specific tables ---" 또는 agent 분기 시작 부분을 찾음

# 전략: 각 SELECT에서 하드코딩 컬럼 대신, 존재하는 컬럼만 선택하는 헬퍼 함수 삽입
# get_map_data 함수 시작 부분에 헬퍼 추가

old_marker = "def get_map_data():"
helper = '''def _safe_select_columns(cur, table_name, wanted_columns):
    """테이블에 실제 존재하는 컬럼만 반환"""
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s AND table_schema = 'public'",
        (table_name,)
    )
    existing = set(r[0] for r in cur.fetchall())
    return [c for c in wanted_columns if c.strip('"') in existing or c.strip() in ('coordinates_lat', 'coordinates_lon')]


def get_map_data():'''

if '_safe_select_columns' not in c:
    c = c.replace(old_marker, helper)
    print('[1] _safe_select_columns 헬퍼 추가')
else:
    print('[1] 이미 존재')

# 이제 각 SELECT 부분에서 하드코딩 컬럼 리스트를 동적으로 필터링
# 단일부동산(danil) SELECT 수정
old_danil = """                        base_query = (
                            'SELECT "지번 주소", "도로명주소", "건물명", "매가(만원)",'
                            ' "토지면적(㎡)", "연면적(㎡)", "건폐율(%%)", "용적률(%%)",'
                            ' "층수", "주용도", "용도지역", "현황", "사용승인일",'
                            ' "보증금(만원)", "월세(만원)", "융자(만원)",'
                            ' "실투자금", "융자제외수익률(%%)",'
                            ' "매물종류",'
                            ' "광고(자동완성)", "대표사진", "인접역", "거리(m)",'
                            ' "record_id", coordinates_lat, coordinates_lon'
                            ' FROM ' + danil_table +"""

new_danil = """                        _danil_cols = ['"지번 주소"', '"도로명주소"', '"건물명"', '"매가(만원)"',
                            '"토지면적(㎡)"', '"연면적(㎡)"', '"건폐율(%%)"', '"용적률(%%)"',
                            '"층수"', '"주용도"', '"용도지역"', '"현황"', '"사용승인일"',
                            '"보증금(만원)"', '"월세(만원)"', '"융자(만원)"',
                            '"실투자금"', '"융자제외수익률(%%)"',
                            '"매물종류"',
                            '"광고(자동완성)"', '"대표사진"', '"인접역"', '"거리(m)"',
                            '"record_id"', 'coordinates_lat', 'coordinates_lon']
                        _danil_cols = _safe_select_columns(cur, danil_table, _danil_cols)
                        base_query = (
                            'SELECT ' + ', '.join(_danil_cols) +
                            ' FROM ' + danil_table +"""

if old_danil in c:
    c = c.replace(old_danil, new_danil)
    print('[2] 단일부동산 SELECT 동적화')
else:
    print('[2] 단일 패턴 불일치')

# 집합부동산(jibhap) SELECT도 동일하게
old_jibhap_select = """                        ' "광고(자동완성)", "대표사진", "인접역", "거리(m)",'
                            ' "record_id", coordinates_lat, coordinates_lon'
                            ' FROM ' + jibhap_table +"""
new_jibhap_select = """                        ' "광고(자동완성)", "대표사진",',
                            ' "record_id", coordinates_lat, coordinates_lon']
                        _jibhap_cols = _safe_select_columns(cur, jibhap_table, [c.strip().strip("'").strip(",").strip() for c in _jibhap_raw])
                        # fallback: 위 방식이 복잡하므로 간단히 처리
                        base_query_j = 'dummy'
                        ' FROM ' + jibhap_table +"""

# 위 방식은 너무 복잡. 더 간단한 방식으로: _safe_select_columns를 SELECT 전에 호출해서
# 없는 컬럼만 제거

# 대신 더 간단한 접근: 각 테이블 쿼리 전에 컬럼 체크 후 SELECT *로 변경하고 row.get() 사용
# 이미 row.get() 패턴을 쓰고 있으므로 SELECT * 방식이 가장 안전

# 모든 하드코딩 SELECT를 SELECT * 로 변경
# 패턴: 'SELECT "지번 주소",...' FROM table → 'SELECT *' FROM table

import re

# agent_slug 분기 내의 모든 base_query SELECT 를 SELECT * 로 변경
# 패턴: 'SELECT "지번...' + ... + 'FROM ' + table_var
c = re.sub(
    r"base_query = \(\s*'SELECT .+?coordinates_lon'\s*' FROM ' \+ (\w+_table) \+",
    r"base_query = ('SELECT * FROM ' + \1 +",
    c,
    flags=re.DOTALL
)

print('[3] 모든 agent SELECT를 SELECT * 로 변경')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('완료')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Week 4 — 매칭 로직 정규화 유닛 테스트."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# warm_building_cache 에서 필요한 함수만 분리 import
import importlib.util
spec = importlib.util.spec_from_file_location(
    'warm_building_cache',
    os.path.join(HERE, 'warm_building_cache.py')
)
# DB/서버 의존성 회피: 필요한 함수만 추출해서 로컬에서 평가
import re
from typing import Optional, Tuple, List


_EMPTY_DONG_TOKENS = {
    '', '동 없음', '동없음', '없음', '-', 'n/a', 'N/A', 'na', 'NA', 'none', 'None',
    '.', '_', '0', '없음동',
}


def _normalize_dong(raw) -> Tuple[str, Optional[int]]:
    if raw is None:
        return '', None
    s = str(raw)
    s = s.replace('０', '0').replace('１', '1').replace('２', '2').replace('３', '3').replace('４', '4') \
         .replace('５', '5').replace('６', '6').replace('７', '7').replace('８', '8').replace('９', '9')
    s = s.strip()
    s_lower = s.lower()
    if s_lower in _EMPTY_DONG_TOKENS or s.strip() == '':
        return '', None
    digit_match = re.search(r'\d+', s)
    digit_int: Optional[int] = int(digit_match.group()) if digit_match else None
    if s.endswith('동'):
        canon = s
    elif digit_int is not None and re.fullmatch(r'\d+', s):
        canon = f'{digit_int}동'
    else:
        canon = s
    return canon, digit_int


def _match_dong(rec_dong, dongs):
    rec_canon, rec_digit = _normalize_dong(rec_dong)
    dong_entries = []
    for d in dongs:
        name = d.get('dong_nm') or d.get('bld_nm') or ''
        canon, digit = _normalize_dong(name)
        dong_entries.append({'dong': d, 'canon': canon, 'digit': digit, 'raw': name})
    if rec_canon:
        for e in dong_entries:
            if e['canon'] and e['canon'] == rec_canon:
                return e['dong']
    if rec_digit is not None:
        digit_matches = [e for e in dong_entries if e['digit'] == rec_digit]
        if len(digit_matches) == 1:
            return digit_matches[0]['dong']
    if len(dongs) == 1:
        return dongs[0]
    return None


def test_normalize():
    cases = [
        (None, '', None),
        ('', '', None),
        ('동 없음', '', None),
        ('-', '', None),
        ('n/a', '', None),
        ('103동', '103동', 103),
        ('103', '103동', 103),
        (' 103동 ', '103동', 103),
        ('A동', 'A동', None),
        ('비동', '비동', None),
        ('１０３', '103동', 103),  # 전각 숫자
        ('파크리오 101동', '파크리오 101동', 101),
    ]
    print('=== _normalize_dong 테스트 ===')
    passed = 0
    failed = 0
    for raw, exp_canon, exp_digit in cases:
        canon, digit = _normalize_dong(raw)
        ok = (canon == exp_canon and digit == exp_digit)
        mark = 'OK' if ok else 'FAIL'
        if ok:
            passed += 1
        else:
            failed += 1
        print(f'  [{mark}] input={raw!r} → canon={canon!r} digit={digit} (exp canon={exp_canon!r} digit={exp_digit})')
    print(f'--- {passed} passed, {failed} failed ---\n')
    return failed == 0


def test_match():
    print('=== _match_dong 테스트 ===')
    # 케이스 1: 단일 동 건물 (동 = None)
    dongs_single = [{'dong_nm': '', 'bd_mgt_sn': 'BD1', 'lat': 37.5, 'lon': 127.0}]
    r = _match_dong(None, dongs_single)
    print(f'  [CASE1 단일동, rec=None] matched={r["bd_mgt_sn"] if r else None}')
    # 케이스 2: 동 여러 개, rec=103
    dongs_multi = [
        {'dong_nm': '101동', 'bd_mgt_sn': 'BD101', 'lat': 1, 'lon': 1},
        {'dong_nm': '102동', 'bd_mgt_sn': 'BD102', 'lat': 2, 'lon': 2},
        {'dong_nm': '103동', 'bd_mgt_sn': 'BD103', 'lat': 3, 'lon': 3},
    ]
    r = _match_dong('103', dongs_multi)
    print(f'  [CASE2 rec=103] matched={r["bd_mgt_sn"] if r else None} (expected=BD103)')
    r = _match_dong('103동', dongs_multi)
    print(f'  [CASE3 rec=103동] matched={r["bd_mgt_sn"] if r else None} (expected=BD103)')
    r = _match_dong('동 없음', dongs_multi)
    print(f'  [CASE4 rec=동 없음, 다수동] matched={r["bd_mgt_sn"] if r else None} (expected=None)')
    # 케이스 5: 공백 포함
    r = _match_dong(' 101동 ', dongs_multi)
    print(f'  [CASE5 rec=" 101동 "] matched={r["bd_mgt_sn"] if r else None} (expected=BD101)')
    # 케이스 6: A동 케이스
    dongs_abcd = [
        {'dong_nm': 'A동', 'bd_mgt_sn': 'BDA', 'lat': 1, 'lon': 1},
        {'dong_nm': 'B동', 'bd_mgt_sn': 'BDB', 'lat': 2, 'lon': 2},
    ]
    r = _match_dong('A동', dongs_abcd)
    print(f'  [CASE6 rec=A동] matched={r["bd_mgt_sn"] if r else None} (expected=BDA)')
    r = _match_dong(None, dongs_abcd)  # 단일동 아니므로 매칭 실패해야
    print(f'  [CASE7 rec=None, 다수동] matched={r["bd_mgt_sn"] if r else None} (expected=None)')


if __name__ == '__main__':
    test_normalize()
    test_match()

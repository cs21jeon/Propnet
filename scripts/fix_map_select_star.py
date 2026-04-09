#!/usr/bin/env python3
"""map-data API: 하드코딩 SELECT를 SELECT * 로 변경 (agent별 테이블 호환)"""

path = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

changes = 0

# 단일부동산 SELECT
old_danil = '''                        base_query = (
                            'SELECT "지번 주소", "도로명주소", "건물명", "매가(만원)",'
                            ' "토지면적(㎡)", "연면적(㎡)", "건폐율(%%)", "용적률(%%)",'
                            ' "층수", "주용도", "용도지역", "현황", "사용승인일",'
                            ' "보증금(만원)", "월세(만원)", "융자(만원)",'
                            ' "실투자금", "융자제외수익률(%%)",'
                            ' "매물종류",'
                            ' "광고(자동완성)", "대표사진", "인접역", "거리(m)",'
                            ' "record_id", coordinates_lat, coordinates_lon'
                            ' FROM ' + danil_table +
                            ' WHERE coordinates_lat IS NOT NULL AND coordinates_lon IS NOT NULL'
                        )'''

new_danil = '''                        base_query = (
                            'SELECT * FROM ' + danil_table +
                            ' WHERE coordinates_lat IS NOT NULL AND coordinates_lon IS NOT NULL'
                        )'''

if old_danil in c:
    c = c.replace(old_danil, new_danil)
    changes += 1
    print('[1] 단일부동산 SELECT * 변경')

# 집합부동산 SELECT
old_jibhap = '''                    base_query = (
                        'SELECT "지번 주소", "도로명주소", "건물명", "매가(만원)",'
                        ' "토지면적(㎡)", "연면적(㎡)", "건폐율(%%)", "용적률(%%)",'
                        ' "총층수" AS "층수", "주용도", "용도지역", "현황", "사용승인일",'
                        ' "보증금(만원)", "월세(만원)", "융자(만원)",'
                        ' "전용면적(㎡)", "공급면적(㎡)", "대지면적(㎡)",'
                        ' "방", "화", "종류", "호수", "물건종류",'
                        ' "관리비(만원)", "입주가능일",'
                        ' "광고(자동완성)", "대표사진", "인접역", "거리(m)",'
                        ' "record_id", coordinates_lat, coordinates_lon'
                        ' FROM ' + jibhap_table +
                        ' WHERE coordinates_lat IS NOT NULL AND coordinates_lon IS NOT NULL'
                    )'''

new_jibhap = '''                    base_query = (
                        'SELECT * FROM ' + jibhap_table +
                        ' WHERE coordinates_lat IS NOT NULL AND coordinates_lon IS NOT NULL'
                    )'''

if old_jibhap in c:
    c = c.replace(old_jibhap, new_jibhap)
    changes += 1
    print('[2] 집합부동산 SELECT * 변경')

# 부분부동산 SELECT
old_bubun = '''                    base_query = (
                        'SELECT "지번 주소", "도로명주소", "건물명",'
                        ' "토지면적(㎡)", "연면적(㎡)", "건폐율(%%)", "용적률(%%)",'
                        ' "층수", "주용도", "용도지역", "현황", "사용승인일",'
                        ' "보증금(만원)", "월세(만원)", "융자(만원)",'
                        ' "전용면적", "공급면적(㎡)",'
                        ' "방", "화", "종류", "호수", "물건종류", "룸형태",'
                        ' "관리비", "입주가능일",'
                        ' "광고(자동완성)", "대표사진", "인접역", "거리(m)",'
                        ' "record_id", coordinates_lat, coordinates_lon'
                        ' FROM ' + bubun_table +
                        ' WHERE coordinates_lat IS NOT NULL AND coordinates_lon IS NOT NULL'
                    )'''

new_bubun = '''                    base_query = (
                        'SELECT * FROM ' + bubun_table +
                        ' WHERE coordinates_lat IS NOT NULL AND coordinates_lon IS NOT NULL'
                    )'''

if old_bubun in c:
    c = c.replace(old_bubun, new_bubun)
    changes += 1
    print('[3] 부분부동산 SELECT * 변경')

# %% 이스케이프 처리 제거 (SELECT *에서는 불필요)
# 기존: cur.execute(base_query.replace('%%', '%'))
# SELECT *에서는 %%가 없으므로 replace가 있어도 무해하지만, 깔끔하게 둠

if changes > 0:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print(f'\n총 {changes}개 변경 완료')
else:
    print('변경 없음')

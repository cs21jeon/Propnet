#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
complex_master.address_jibun 시군구 표기 정규화.

문제: '경기도 수원팔달구 고등동 310' (시 누락)
정상: '경기도 수원시 팔달구 고등동 310'

VWorld getCoord API는 정식 행정구역명만 인식하므로
약식 표기를 정규화해야 geocoding 성공률이 올라감.
"""
import argparse
import os
import psycopg2

# 약식 → 정식 매핑
SIGUNGU_MAP = {
    # 경기도
    "수원권선구": "수원시 권선구",
    "수원장안구": "수원시 장안구",
    "수원팔달구": "수원시 팔달구",
    "수원영통구": "수원시 영통구",
    "성남수정구": "성남시 수정구",
    "성남중원구": "성남시 중원구",
    "성남분당구": "성남시 분당구",
    "안양만안구": "안양시 만안구",
    "안양동안구": "안양시 동안구",
    "부천원미구": "부천시 원미구",
    "부천소사구": "부천시 소사구",
    "부천오정구": "부천시 오정구",
    "안산상록구": "안산시 상록구",
    "안산단원구": "안산시 단원구",
    "고양덕양구": "고양시 덕양구",
    "고양일산동구": "고양시 일산동구",
    "고양일산서구": "고양시 일산서구",
    "용인처인구": "용인시 처인구",
    "용인기흥구": "용인시 기흥구",
    "용인수지구": "용인시 수지구",
    # 충청남도
    "천안동남구": "천안시 동남구",
    "천안서북구": "천안시 서북구",
    # 경상북도
    "포항남구": "포항시 남구",
    "포항북구": "포항시 북구",
    # 전북특별자치도
    "전주덕진구": "전주시 덕진구",
    "전주완산구": "전주시 완산구",
    # 경상남도
    "창원의창구": "창원시 의창구",
    "창원성산구": "창원시 성산구",
    "창원마산회원구": "창원시 마산회원구",
    "창원마산합포구": "창원시 마산합포구",
    "창원진해구": "창원시 진해구",
    # 충청북도
    "청주상당구": "청주시 상당구",
    "청주서원구": "청주시 서원구",
    "청주흥덕구": "청주시 흥덕구",
    "청주청원구": "청주시 청원구",
}


def load_env(path='/home/webapp/goldenrabbit/backend/.env'):
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())


def get_conn():
    load_env()
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', '127.0.0.1'),
        port=int(os.environ.get('DB_PORT', '5432')),
        dbname=os.environ.get('DB_NAME', 'goldenrabbit_db'),
        user=os.environ.get('DB_USER', 'goldenrabbit_user'),
        password=os.environ.get('DB_PASSWORD', ''),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='변경 건수만 출력')
    parser.add_argument('--apply', action='store_true', help='실제 UPDATE 실행')
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("--dry-run 또는 --apply 중 하나를 지정하세요.")
        return

    conn = get_conn()
    cur = conn.cursor()

    total = 0
    for old, new in sorted(SIGUNGU_MAP.items()):
        pattern = ' ' + old + ' '
        replacement = ' ' + new + ' '

        cur.execute(
            "SELECT COUNT(*) FROM complex_master WHERE address_jibun LIKE %s",
            ('%' + pattern + '%',),
        )
        cnt = cur.fetchone()[0]

        if cnt == 0:
            continue

        if args.dry_run:
            # 샘플 출력
            cur.execute(
                "SELECT address_jibun FROM complex_master WHERE address_jibun LIKE %s LIMIT 2",
                ('%' + pattern + '%',),
            )
            samples = [r[0] for r in cur.fetchall()]
            before = samples[0] if samples else ''
            after = before.replace(old, new) if before else ''
            print(f"  {old} -> {new}: {cnt}건  예) {before} -> {after}")
        elif args.apply:
            cur.execute(
                "UPDATE complex_master SET address_jibun = REPLACE(address_jibun, %s, %s) WHERE address_jibun LIKE %s",
                (old, new, '%' + pattern + '%'),
            )
            print(f"  {old} -> {new}: {cur.rowcount}건 변경")

        total += cnt

    if args.apply:
        conn.commit()
        print(f"\n총 {total}건 변경 완료 (COMMIT)")
    else:
        print(f"\n총 {total}건 변경 예정 (DRY-RUN)")

    cur.close()
    conn.close()


if __name__ == '__main__':
    main()

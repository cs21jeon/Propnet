#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
건축물대장 전유부 CSV → 건물별 전유면적 합계 CSV 변환

사용법:
    python process_building_summary_local.py

입력: 같은 폴더의 전유부 CSV 파일 (자동 탐색)
출력: building_area_summary.csv

데이터 출처: 건축HUB (hub.go.kr) 대용량 다운로드
"""

import os
import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def find_csv_file():
    """현재 폴더에서 전유부 데이터 파일 찾기"""
    current_dir = Path(".")

    # 가능한 파일 패턴 (csv, txt 모두 지원)
    patterns = ["*.csv", "*.CSV", "*.txt", "*.TXT"]
    csv_files = []

    for pattern in patterns:
        csv_files.extend(current_dir.glob(pattern))

    # 스크립트 자체와 출력 파일 제외
    csv_files = [
        f for f in csv_files
        if "summary" not in f.name.lower()
        and f.name != "building_area_summary.csv"
        and not f.name.endswith(".py")
    ]

    if not csv_files:
        print("오류: CSV 파일을 찾을 수 없습니다.")
        print("전유부 CSV 파일을 이 스크립트와 같은 폴더에 넣어주세요.")
        sys.exit(1)

    if len(csv_files) == 1:
        return csv_files[0]

    # 여러 파일이 있으면 선택
    print("여러 CSV 파일이 발견되었습니다:")
    for i, f in enumerate(csv_files):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  [{i+1}] {f.name} ({size_mb:.1f} MB)")

    while True:
        try:
            choice = int(input("처리할 파일 번호를 입력하세요: ")) - 1
            if 0 <= choice < len(csv_files):
                return csv_files[choice]
        except ValueError:
            pass
        print("올바른 번호를 입력하세요.")


def detect_columns(headers):
    """컬럼명 자동 감지"""
    col_map = {
        "sigungu_cd": None,
        "bjdong_cd": None,
        "bun": None,
        "ji": None,
        "exclusive_area": None,
        "dong_nm": None,
        "ho_nm": None,
    }

    for h in headers:
        h_lower = h.lower().strip()
        h_clean = h.strip()

        # 시군구코드
        if col_map["sigungu_cd"] is None:
            if "sigungucd" in h_lower or "시군구코드" in h_clean or h_lower == "sigungu_cd":
                col_map["sigungu_cd"] = h

        # 법정동코드
        if col_map["bjdong_cd"] is None:
            if "bjdongcd" in h_lower or "법정동코드" in h_clean or h_lower == "bjdong_cd":
                col_map["bjdong_cd"] = h

        # 번 (본번)
        if col_map["bun"] is None:
            if h_lower == "bun" or h_clean == "번" or "본번" in h_clean:
                col_map["bun"] = h

        # 지 (부번)
        if col_map["ji"] is None:
            if h_lower == "ji" or h_clean == "지" or "부번" in h_clean:
                col_map["ji"] = h

        # 전용면적
        if col_map["exclusive_area"] is None:
            if "전용면적" in h_clean or "exclusivearea" in h_lower or "전유면적" in h_clean:
                col_map["exclusive_area"] = h

        # 동명칭
        if col_map["dong_nm"] is None:
            if "동명칭" in h_clean or "dongnm" in h_lower:
                col_map["dong_nm"] = h

        # 호명칭
        if col_map["ho_nm"] is None:
            if "호명칭" in h_clean or "honm" in h_lower:
                col_map["ho_nm"] = h

    return col_map


def parse_pipe_delimited(filepath):
    """파이프(|) 구분 파일 파싱 (헤더 없음)"""

    print(f"\n파이프 구분 파일 처리: {filepath}")
    print("=" * 60)

    # 건물별 데이터 집계
    building_data = defaultdict(lambda: {"total_area": 0.0, "count": 0})

    # 건축HUB 전유부 파일 컬럼 위치 (0-based index)
    # mart_djy_06.txt 형식
    IDX_SIGUNGU = 8      # 시군구코드
    IDX_BJDONG = 9       # 법정동코드
    IDX_BUN = 11         # 번
    IDX_JI = 12          # 지
    IDX_AREA = 35        # 전용면적 (35번 인덱스)

    encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]

    for encoding in encodings:
        try:
            print(f"인코딩 시도: {encoding}")

            with open(filepath, "r", encoding=encoding) as f:
                row_count = 0
                error_count = 0

                for line in f:
                    try:
                        fields = line.strip().split("|")

                        # 필드 수 확인 (최소 37개 필요)
                        if len(fields) < 37:
                            error_count += 1
                            continue

                        sigungu = fields[IDX_SIGUNGU].strip().zfill(5)
                        bjdong = fields[IDX_BJDONG].strip().zfill(5)
                        bun = fields[IDX_BUN].strip().zfill(4)
                        ji = fields[IDX_JI].strip().zfill(4) if fields[IDX_JI].strip() else "0000"

                        # 면적 파싱
                        area_str = fields[IDX_AREA].strip()
                        if area_str and area_str != "-":
                            try:
                                area = float(area_str.replace(",", ""))
                            except ValueError:
                                area = 0.0
                        else:
                            area = 0.0

                        # 유효한 데이터만 처리
                        if len(sigungu) == 5 and len(bjdong) == 5:
                            key = (sigungu, bjdong, bun, ji)
                            building_data[key]["total_area"] += area
                            building_data[key]["count"] += 1

                        row_count += 1

                        if row_count % 500000 == 0:
                            print(f"  처리: {row_count:,}건 / 건물: {len(building_data):,}개")

                    except Exception as e:
                        error_count += 1
                        if error_count <= 5:
                            print(f"  행 처리 오류: {e}")
                        continue

                print(f"\n파싱 완료!")
                print(f"  총 행 수: {row_count:,}")
                print(f"  오류 건수: {error_count:,}")
                print(f"  건물 수: {len(building_data):,}")

                return building_data

        except UnicodeDecodeError:
            print(f"  {encoding} 디코딩 실패")
            continue
        except Exception as e:
            print(f"  오류 ({encoding}): {e}")
            continue

    return None


def parse_csv(filepath):
    """CSV 파일 파싱 후 건물별 합계 계산"""

    print(f"\n파일 읽는 중: {filepath}")
    print("=" * 60)

    # 먼저 파일 형식 확인
    with open(filepath, "r", encoding="utf-8-sig", errors="ignore") as f:
        first_line = f.readline()

    # 파이프 구분자 감지 (|가 5개 이상이면 파이프 구분 파일)
    if first_line.count("|") >= 5:
        print("파이프(|) 구분 파일 감지!")
        return parse_pipe_delimited(filepath)

    # 기존 CSV/TSV 처리
    print("CSV/TSV 파일 처리...")

    # 건물별 데이터 집계
    building_data = defaultdict(lambda: {"total_area": 0.0, "count": 0})

    # 인코딩 시도 순서
    encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]

    for encoding in encodings:
        try:
            print(f"인코딩 시도: {encoding}")

            with open(filepath, "r", encoding=encoding) as f:
                # 첫 줄로 구분자 감지
                first_line = f.readline()
                f.seek(0)

                # 구분자 감지 (쉼표 또는 탭)
                if "\t" in first_line:
                    delimiter = "\t"
                else:
                    delimiter = ","

                reader = csv.DictReader(f, delimiter=delimiter)
                headers = reader.fieldnames

                if not headers:
                    continue

                print(f"컬럼 수: {len(headers)}")
                print(f"컬럼 샘플: {headers[:5]}")

                # 컬럼 매핑
                col_map = detect_columns(headers)

                print(f"\n컬럼 매핑 결과:")
                for k, v in col_map.items():
                    print(f"  {k}: {v}")

                # 필수 컬럼 확인
                required = ["sigungu_cd", "bjdong_cd", "bun"]
                missing = [k for k in required if col_map[k] is None]

                if missing:
                    print(f"경고: 필수 컬럼 누락 - {missing}")
                    print("다른 인코딩 시도...")
                    continue

                print("\n처리 시작...")

                # 데이터 처리
                row_count = 0
                error_count = 0

                for row in reader:
                    try:
                        sigungu = str(row.get(col_map["sigungu_cd"], "")).strip()
                        bjdong = str(row.get(col_map["bjdong_cd"], "")).strip()
                        bun = str(row.get(col_map["bun"], "")).strip()
                        ji = str(row.get(col_map["ji"], "0") or "0").strip()

                        # 코드 정규화
                        if sigungu and len(sigungu) < 5:
                            sigungu = sigungu.zfill(5)
                        if bjdong and len(bjdong) < 5:
                            bjdong = bjdong.zfill(5)
                        if bun and len(bun) < 4:
                            bun = bun.zfill(4)
                        if ji and len(ji) < 4:
                            ji = ji.zfill(4)

                        # 면적 파싱
                        area_str = str(row.get(col_map["exclusive_area"], "0") or "0").strip()
                        if area_str and area_str != "-" and area_str != "":
                            # 쉼표 제거 및 숫자만 추출
                            area_str = area_str.replace(",", "").replace(" ", "")
                            try:
                                area = float(area_str)
                            except ValueError:
                                area = 0.0
                        else:
                            area = 0.0

                        # 유효한 데이터만 처리
                        if sigungu and bjdong and bun and len(sigungu) == 5 and len(bjdong) == 5:
                            key = (sigungu, bjdong, bun, ji)
                            building_data[key]["total_area"] += area
                            building_data[key]["count"] += 1

                        row_count += 1

                        # 진행 상황 출력
                        if row_count % 500000 == 0:
                            print(f"  처리: {row_count:,}건 / 건물: {len(building_data):,}개")

                    except Exception as e:
                        error_count += 1
                        if error_count <= 5:
                            print(f"  행 처리 오류: {e}")
                        continue

                print(f"\n파싱 완료!")
                print(f"  총 행 수: {row_count:,}")
                print(f"  오류 건수: {error_count:,}")
                print(f"  건물 수: {len(building_data):,}")

                return building_data

        except UnicodeDecodeError:
            print(f"  {encoding} 디코딩 실패")
            continue
        except Exception as e:
            print(f"  오류 ({encoding}): {e}")
            continue

    print("\n오류: 지원되는 인코딩을 찾을 수 없습니다.")
    sys.exit(1)


def save_summary_csv(building_data, output_path):
    """결과를 CSV로 저장"""

    print(f"\n결과 저장 중: {output_path}")

    # 100세대 이상 건물만 필터링 (대단지 아파트)
    filtered_data = [
        (k, v) for k, v in building_data.items()
        if v["count"] >= 100
    ]

    print(f"  100세대 이상 건물: {len(filtered_data):,}개")

    # 시군구+법정동+번지 순으로 정렬
    filtered_data.sort(key=lambda x: x[0])

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)

        # 헤더
        writer.writerow([
            "sigungu_cd",
            "bjdong_cd",
            "bun",
            "ji",
            "total_exclusive_area",
            "unit_count"
        ])

        # 데이터
        for (sigungu, bjdong, bun, ji), data in filtered_data:
            writer.writerow([
                sigungu,
                bjdong,
                bun,
                ji,
                round(data["total_area"], 4),
                data["count"]
            ])

    # 파일 크기 확인
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  파일 크기: {size_kb:.1f} KB")
    print(f"\n저장 완료!")


def main():
    print("=" * 60)
    print("건축물대장 전유부 → 건물별 전유면적 합계 변환")
    print("=" * 60)

    start_time = datetime.now()

    # CSV 파일 찾기
    csv_file = find_csv_file()
    print(f"\n선택된 파일: {csv_file}")

    # 파싱
    building_data = parse_csv(csv_file)

    # 저장
    output_path = "building_area_summary.csv"
    save_summary_csv(building_data, output_path)

    elapsed = datetime.now() - start_time

    print("\n" + "=" * 60)
    print(f"완료! 소요시간: {elapsed}")
    print("=" * 60)
    print(f"\n결과 파일: {output_path}")
    print("이 파일을 서버에 업로드하세요.")


if __name__ == "__main__":
    main()

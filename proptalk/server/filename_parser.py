"""
AI 파일명 파싱 - 자유 형식 파일명에서 전화번호, 날짜, 이름 추출

지원 예시:
  - "홍길동_01012345678_상담.mp3"
  - "20250226 녹음.wav"  
  - "상담녹음_2025년2월26일_010-9876-5432.m4a"
  - "김철수 통화 2025.02.26.mp3"
  - "010_1234_5678_메모.wav"
  - "recording_20250226_143022.mp3"
"""
import re
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


def parse_filename(filename: str) -> dict:
    """
    파일명에서 전화번호, 날짜, 이름, 메모를 추출
    
    Returns:
        {
            'phone_number': '01012345678' or None,
            'record_date': date object or None,
            'name': '홍길동' or None,
            'memo': '상담' or None,
        }
    """
    result = {
        'phone_number': None,
        'record_date': None,
        'name': None,
        'memo': None,
    }
    
    # 확장자 제거
    name_part = re.sub(r'\.[a-zA-Z0-9]+$', '', filename)
    
    # 1) 전화번호 추출
    result['phone_number'] = extract_phone(name_part)
    
    # 2) 날짜 추출
    result['record_date'] = extract_date(name_part)
    
    # 3) 이름/메모 추출 (전화번호, 날짜 제거 후 남은 텍스트)
    remaining = remove_phone_and_date(name_part)
    name, memo = extract_name_and_memo(remaining)
    result['name'] = name
    result['memo'] = memo
    
    logger.info(f"파일명 파싱: '{filename}' → {result}")
    return result


# ============================================================
# 전화번호 추출
# ============================================================
def extract_phone(text: str) -> str | None:
    """
    다양한 형식의 한국 전화번호 추출
    - 01012345678
    - 010-1234-5678
    - 010_1234_5678
    - 010.1234.5678
    - 010 1234 5678
    """
    patterns = [
        # 010-1234-5678 / 010_1234_5678 / 010.1234.5678
        r'(01[016789])[-_.\s]?(\d{3,4})[-_.\s]?(\d{4})',
        # 02-1234-5678 (서울) / 031-1234-5678 (경기)
        r'(0[2-6]\d?)[-_.\s]?(\d{3,4})[-_.\s]?(\d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # 숫자만 합치기
            phone = ''.join(match.groups())
            return phone
    
    return None


# ============================================================
# 날짜 추출
# ============================================================
def extract_date(text: str) -> date | None:
    """
    다양한 형식의 날짜 추출
    """
    patterns = [
        # 2025년 2월 26일 / 2025년2월26일
        (r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일', '%Y-%m-%d'),
        # 2025년 2월 (일 없음)
        (r'(\d{4})\s*년\s*(\d{1,2})\s*월', '%Y-%m'),
        # 2025.02.26 / 2025-02-26 / 2025/02/26
        (r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', '%Y-%m-%d'),
        # 20250226 (8자리)
        (r'(\d{4})(\d{2})(\d{2})', '%Y-%m-%d'),
        # 250226 (6자리, 2자리 연도)
        (r'(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)', '%y-%m-%d'),
    ]
    
    for pattern, fmt in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                groups = match.groups()
                if fmt == '%Y-%m':
                    date_str = f"{groups[0]}-{groups[1]}"
                    dt = datetime.strptime(date_str, '%Y-%m')
                    return dt.date()
                else:
                    date_str = f"{groups[0]}-{groups[1]}-{groups[2]}"
                    fmt_actual = fmt
                    dt = datetime.strptime(date_str, fmt_actual)
                    
                    # 유효한 날짜인지 확인 (미래가 아닌지, 너무 과거가 아닌지)
                    if dt.year < 2000 or dt.year > 2100:
                        continue
                    if dt.date() > date.today():
                        # 6자리의 경우 전화번호일 수 있으므로 스킵
                        if len(groups[0]) == 2:
                            continue
                    
                    return dt.date()
            except (ValueError, IndexError):
                continue
    
    return None


# ============================================================
# 이름 / 메모 추출
# ============================================================
def remove_phone_and_date(text: str) -> str:
    """전화번호와 날짜 패턴 제거"""
    # 전화번호 제거
    text = re.sub(r'01[016789][-_.\s]?\d{3,4}[-_.\s]?\d{4}', '', text)
    text = re.sub(r'0[2-6]\d?[-_.\s]?\d{3,4}[-_.\s]?\d{4}', '', text)
    
    # 날짜 제거
    text = re.sub(r'\d{4}\s*년\s*\d{1,2}\s*월\s*(\d{1,2}\s*일)?', '', text)
    text = re.sub(r'\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}', '', text)
    text = re.sub(r'(?<!\d)\d{8}(?!\d)', '', text)  # 20250226
    
    # 구분자 정리
    text = re.sub(r'[_\-.\s]+', ' ', text).strip()
    return text


def extract_name_and_memo(text: str) -> tuple:
    """
    남은 텍스트에서 이름과 메모 분리
    한국어 이름 패턴: 2~4글자 한글
    """
    if not text:
        return None, None
    
    # 불필요한 키워드 제거
    noise_words = ['녹음', '통화', '전화', 'recording', 'rec', '상담녹음', '통화녹음']
    cleaned_parts = []
    memo_parts = []
    
    parts = text.split()
    for part in parts:
        if part.lower() in [w.lower() for w in noise_words]:
            memo_parts.append(part)
        else:
            cleaned_parts.append(part)
    
    # 한국어 이름 찾기 (2~4자 한글)
    name = None
    remaining_for_memo = []
    
    for part in cleaned_parts:
        if not name and re.match(r'^[가-힣]{2,4}$', part):
            name = part
        else:
            remaining_for_memo.append(part)
    
    # 메모 합치기
    all_memo = memo_parts + remaining_for_memo
    memo = ' '.join(all_memo).strip() if all_memo else None
    
    return name, memo


# ============================================================
# 테스트
# ============================================================
if __name__ == '__main__':
    test_cases = [
        "홍길동_01012345678_상담.mp3",
        "20250226 녹음.wav",
        "상담녹음_2025년2월26일_010-9876-5432.m4a",
        "김철수 통화 2025.02.26.mp3",
        "010_1234_5678_메모.wav",
        "recording_20250226_143022.mp3",
        "2025년2월_이영희_상담.mp3",
        "부동산 상담_01098765432.m4a",
        "그냥파일이름.mp3",
    ]
    
    for tc in test_cases:
        result = parse_filename(tc)
        print(f"\n입력: {tc}")
        print(f"  전화번호: {result['phone_number']}")
        print(f"  날짜: {result['record_date']}")
        print(f"  이름: {result['name']}")
        print(f"  메모: {result['memo']}")

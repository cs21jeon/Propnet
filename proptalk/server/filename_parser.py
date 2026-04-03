"""
파일명 파싱 - 통화 녹음 파일명에서 정보 추출

지원 파일명 형식:
  - "이름_전화번호_날짜시간.확장자" (기본 형식)
  - "(주)클래식1st이명화대표이사님_01083104007_20251208153316.m4a"
  - "홍길동_01012345678_상담.mp3"
  - "20250226 녹음.wav"
"""
import re
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


def parse_filename(filename: str) -> dict:
    """
    파일명에서 전화번호, 날짜, 이름을 추출
    
    Returns:
        {
            'phone_number': '01012345678' or None,
            'record_date': date object or None,
            'name': '홍길동' or None,
            'memo': '기타 정보' or None,
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
    
    # 2) 날짜 추출 (14자리 datetime 포함)
    result['record_date'] = extract_date(name_part)
    
    # 3) 이름 추출 (언더스코어로 구분된 첫 번째 부분)
    result['name'] = extract_name(name_part, result['phone_number'])
    
    # 4) 메모 (나머지 부분)
    result['memo'] = extract_memo(name_part, result)
    
    logger.info(f"파일명 파싱: '{filename}' → {result}")
    return result


def extract_phone(text: str) -> str | None:
    """전화번호 추출"""
    patterns = [
        r'(01[016789])[-_.]?(\d{3,4})[-_.]?(\d{4})',
        r'(0[2-6]\d?)[-_.]?(\d{3,4})[-_.]?(\d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return ''.join(match.groups())
    return None


def extract_date(text: str) -> date | None:
    """날짜 추출 - 14자리/12자리/8자리/6자리 datetime 지원"""
    patterns = [
        # 20251208153316 (14자리: YYYYMMDDHHmmss)
        (r'(\d{4})(\d{2})(\d{2})(\d{6})', 'datetime14'),
        # 20250226 (8자리: YYYYMMDD)
        (r'(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)', 'date8'),
        # 260401_153230 (6+6자리: YYMMDD_HHmmss, 언더스코어로 분리)
        (r'(?<!\d)(\d{2})(\d{2})(\d{2})[_](\d{6})(?!\d)', 'datetime6_6'),
        # 260401 (6자리: YYMMDD)
        (r'(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)', 'date6'),
        # 2025.02.26 / 2025-02-26
        (r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', 'date_sep'),
        # 2025년 2월 26일
        (r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일', 'date_kr'),
    ]

    for pattern, fmt_type in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                groups = match.groups()

                if fmt_type == 'datetime14':
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                elif fmt_type in ('datetime6_6', 'date6'):
                    # 6자리: YY → 20YY
                    year, month, day = 2000 + int(groups[0]), int(groups[1]), int(groups[2])
                elif fmt_type in ['date8', 'date_sep', 'date_kr']:
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                else:
                    continue

                # 유효성 검사
                if 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                    return date(year, month, day)
            except (ValueError, IndexError):
                continue
    return None


def extract_name(text: str, phone: str) -> str | None:
    """
    이름 추출 - 언더스코어 구분자 기준 첫 번째 부분
    예: "(주)클래식1st이명화대표이사님_01083104007_20251208" → "(주)클래식1st이명화대표이사님"
    """
    # 언더스코어로 분할
    parts = text.split('_')
    
    if len(parts) >= 2:
        first_part = parts[0].strip()
        
        # 첫 부분이 전화번호나 날짜가 아니면 이름으로 간주
        if first_part and not re.match(r'^\d+$', first_part):
            # 전화번호 패턴이 아닌지 확인
            if not re.match(r'^01[016789]', first_part):
                return first_part
    
    # 공백으로 분할된 경우
    parts = text.split()
    for part in parts:
        # 한글 이름 (2-10자, 회사명 포함)
        if re.search(r'[가-힣]{2,}', part) and not re.match(r'^\d', part):
            # 전화번호나 날짜가 아닌 경우
            if phone and phone in part:
                continue
            if re.match(r'^\d{8,}', part):
                continue
            return part
    
    return None


def extract_memo(text: str, parsed: dict) -> str | None:
    """전화번호, 날짜, 이름 제거 후 남은 메모"""
    remaining = text
    
    # 전화번호 제거
    if parsed.get('phone_number'):
        phone = parsed['phone_number']
        remaining = re.sub(rf'{phone[:3]}[-_.]?{phone[3:7]}[-_.]?{phone[7:]}', '', remaining)
        remaining = remaining.replace(phone, '')
    
    # 날짜 제거 (14자리, 8자리)
    remaining = re.sub(r'\d{14}', '', remaining)
    remaining = re.sub(r'(?<!\d)\d{8}(?!\d)', '', remaining)
    remaining = re.sub(r'\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}', '', remaining)
    
    # 이름 제거
    if parsed.get('name'):
        remaining = remaining.replace(parsed['name'], '')
    
    # 정리
    remaining = re.sub(r'[_\-]+', ' ', remaining).strip()
    remaining = re.sub(r'\s+', ' ', remaining).strip()
    
    return remaining if remaining else None


if __name__ == '__main__':
    test_cases = [
        "(주)클래식1st이명화대표이사님_01083104007_20251208153316.m4a",
        "홍길동_01012345678_20250226143022.mp3",
        "김철수_010-9876-5432_2025.02.26.wav",
        "20250226_녹음.wav",
        "01012345678_상담메모.m4a",
    ]
    
    for tc in test_cases:
        result = parse_filename(tc)
        print(f"\n입력: {tc}")
        print(f"  전화번호: {result['phone_number']}")
        print(f"  날짜: {result['record_date']}")
        print(f"  이름: {result['name']}")
        print(f"  메모: {result['memo']}")

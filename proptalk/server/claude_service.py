"""
Claude API를 사용한 텍스트 요약 서비스
"""
import re
import time
import logging
import anthropic
from config import Config

logger = logging.getLogger(__name__)

# 재시도 설정
MAX_RETRIES = 3
INITIAL_BACKOFF = 2  # 초


def _is_retryable_error(error: Exception) -> bool:
    """재시도 가능한 에러인지 판별 (529 Overloaded, 네트워크 에러)"""
    # 네트워크 연결 에러 → 재시도
    if isinstance(error, anthropic.APIConnectionError):
        return True
    # Rate limit (429) → 재시도
    if isinstance(error, anthropic.RateLimitError):
        return True
    # APIStatusError 중 529 Overloaded만 재시도
    if isinstance(error, anthropic.APIStatusError):
        return error.status_code == 529
    return False


def _call_claude_with_retry(client, **kwargs) -> anthropic.types.Message:
    """
    Claude API 호출 + 재시도 로직

    529 (Overloaded) 또는 네트워크 에러 시 최대 3번 재시도
    재시도 간격: 2초 → 4초 → 8초 (exponential backoff)
    다른 에러(400, 401 등)는 재시도 없이 즉시 raise
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return client.messages.create(**kwargs)
        except Exception as e:
            last_error = e
            if not _is_retryable_error(e):
                # 400, 401, 403 등 재시도 불가 에러는 즉시 raise
                raise

            if attempt < MAX_RETRIES:
                wait_time = INITIAL_BACKOFF * (2 ** (attempt - 1))
                logger.warning(
                    f"Claude API 재시도 {attempt}/{MAX_RETRIES} "
                    f"({type(e).__name__}: {e}), "
                    f"{wait_time}초 후 재시도..."
                )
                time.sleep(wait_time)
            else:
                logger.error(
                    f"Claude API {MAX_RETRIES}회 재시도 모두 실패: "
                    f"{type(e).__name__}: {e}"
                )
                raise


def remove_markdown(text: str) -> str:
    """마크다운 형식 제거"""
    # **볼드** 제거
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # *이탤릭* 제거
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # ## 헤더 제거
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # - 또는 * 리스트 마커를 • 로 변경
    text = re.sub(r'^[\-\*]\s+', '• ', text, flags=re.MULTILINE)
    # 숫자. 리스트를 그대로 유지하되 마크다운 형식 제거
    text = re.sub(r'^(\d+)\.\s+\*\*(.+?)\*\*', r'\1. \2', text, flags=re.MULTILINE)
    return text.strip()


def summarize_transcript(text: str, language: str = 'ko') -> str:
    """
    Claude API를 사용하여 통화 내용을 핵심만 요약

    Args:
        text: 변환된 텍스트 전문
        language: 언어 코드 (기본: ko)

    Returns:
        요약된 텍스트 (마크다운 제거됨)
    """
    if not text or len(text.strip()) < 10:
        return "내용이 너무 짧아 요약할 수 없습니다."

    if not Config.CLAUDE_API_KEY:
        logger.warning("CLAUDE_API_KEY가 설정되지 않았습니다. 요약을 건너뜁니다.")
        return None

    try:
        client = anthropic.Anthropic(api_key=Config.CLAUDE_API_KEY)

        # 언어에 따른 프롬프트 설정 (마크다운 사용하지 않도록 지시)
        if language == 'ko':
            prompt = f"""다음은 전화 통화 녹음을 텍스트로 변환한 내용입니다.
아래 형식에 맞춰 간결하게 요약해주세요.

### 형식 규칙
- 마크다운 형식을 사용하세요
- 각 항목은 **볼드** 키워드 + 설명 형태로
- 불필요한 인사말/반복 제거
- 핵심만 3~5개 bullet으로

### 출력 형식 예시
**주제**: 한 줄 요약

- **핵심1**: 내용
- **핵심2**: 내용
- **핵심3**: 내용

**결론**: 최종 합의/결과 (있는 경우)

[통화 내용]
{text}"""
        else:
            prompt = f"""The following is a phone call recording converted to text.
Summarize concisely using markdown format:

- Use **bold** keywords + description
- 3-5 bullet points max
- Include a one-line **Topic** and **Conclusion** if applicable

[Call Content]
{text}"""

        message = _call_claude_with_retry(
            client,
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        summary = message.content[0].text.strip()

        # 마크다운 형식 유지 (Flutter에서 렌더링)

        logger.info(f"Claude 요약 완료: {len(text)}자 -> {len(summary)}자")
        return summary

    except anthropic.APIConnectionError as e:
        logger.error(f"Claude API 연결 오류 (재시도 후 최종 실패): {e}")
        return None
    except anthropic.RateLimitError as e:
        logger.error(f"Claude API 요청 한도 초과 (재시도 후 최종 실패): {e}")
        return None
    except anthropic.APIStatusError as e:
        logger.error(f"Claude API 오류 (status={e.status_code}): {e}")
        return None
    except Exception as e:
        logger.error(f"Claude 요약 실패: {e}", exc_info=True)
        return None


def extract_action_items(text: str) -> list:
    """
    통화 내용에서 액션 아이템(해야 할 일) 추출

    Args:
        text: 변환된 텍스트 전문

    Returns:
        액션 아이템 리스트
    """
    if not text or not Config.CLAUDE_API_KEY:
        return []

    try:
        client = anthropic.Anthropic(api_key=Config.CLAUDE_API_KEY)

        message = _call_claude_with_retry(
            client,
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": f"""다음 통화 내용에서 해야 할 일(액션 아이템)이 있다면 추출해주세요.
없으면 "없음"이라고 답해주세요.

[통화 내용]
{text}

[액션 아이템]"""
            }]
        )

        result = message.content[0].text.strip()
        if result == "없음" or not result:
            return []

        # 줄바꿈으로 분리하여 리스트로 반환
        items = [item.strip().lstrip('•-123456789. ')
                 for item in result.split('\n')
                 if item.strip()]
        return items

    except Exception as e:
        logger.error(f"액션 아이템 추출 실패: {e}")
        return []

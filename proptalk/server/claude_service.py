"""
Claude API를 사용한 텍스트 요약 서비스
"""
import logging
import anthropic
from config import Config

logger = logging.getLogger(__name__)


def summarize_transcript(text: str, language: str = 'ko') -> str:
    """
    Claude API를 사용하여 통화 내용을 핵심만 요약

    Args:
        text: 변환된 텍스트 전문
        language: 언어 코드 (기본: ko)

    Returns:
        요약된 텍스트
    """
    if not text or len(text.strip()) < 10:
        return "내용이 너무 짧아 요약할 수 없습니다."

    if not Config.CLAUDE_API_KEY:
        logger.warning("CLAUDE_API_KEY가 설정되지 않았습니다. 요약을 건너뜁니다.")
        return None

    try:
        client = anthropic.Anthropic(api_key=Config.CLAUDE_API_KEY)

        # 언어에 따른 프롬프트 설정
        if language == 'ko':
            prompt = f"""다음은 전화 통화 녹음을 텍스트로 변환한 내용입니다.
핵심 내용만 간결하게 3-5개 항목으로 요약해주세요.

[통화 내용]
{text}

[요약]"""
        else:
            prompt = f"""The following is a phone call recording converted to text.
Please summarize the key points in 3-5 bullet points.

[Call Content]
{text}

[Summary]"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        summary = message.content[0].text.strip()
        logger.info(f"Claude 요약 완료: {len(text)}자 -> {len(summary)}자")
        return summary

    except anthropic.APIConnectionError as e:
        logger.error(f"Claude API 연결 오류: {e}")
        return None
    except anthropic.RateLimitError as e:
        logger.error(f"Claude API 요청 한도 초과: {e}")
        return None
    except anthropic.APIStatusError as e:
        logger.error(f"Claude API 오류: {e}")
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

        message = client.messages.create(
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

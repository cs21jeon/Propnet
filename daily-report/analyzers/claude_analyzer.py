"""
Claude API 분석기 — 부서별 메트릭을 AI로 분석

_call_claude_with_retry() 패턴은 proptalk/server/claude_service.py에서 재사용
"""
import json
import time
import logging
import anthropic
from config import Config
from analyzers.prompts import DAILY_PROMPTS, WEEKLY_PROMPTS

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
INITIAL_BACKOFF = 2  # 초

# 모델 선택
MODEL_HAIKU = 'claude-haiku-4-5-20251001'
MODEL_SONNET = 'claude-sonnet-4-6'


def _is_retryable_error(error: Exception) -> bool:
    """재시도 가능한 에러인지 판별"""
    if isinstance(error, anthropic.APIConnectionError):
        return True
    if isinstance(error, anthropic.RateLimitError):
        return True
    if isinstance(error, anthropic.APIStatusError):
        return error.status_code == 529
    return False


def _call_with_retry(client, **kwargs) -> anthropic.types.Message:
    """Claude API 호출 + exponential backoff 재시도"""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return client.messages.create(**kwargs)
        except Exception as e:
            last_error = e
            if not _is_retryable_error(e):
                raise
            if attempt < MAX_RETRIES:
                wait_time = INITIAL_BACKOFF * (2 ** (attempt - 1))
                logger.warning(
                    f"Claude API 재시도 {attempt}/{MAX_RETRIES} "
                    f"({type(e).__name__}), {wait_time}초 후..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"Claude API {MAX_RETRIES}회 재시도 모두 실패")
                raise


class ClaudeAnalyzer:
    """부서별 메트릭을 Claude API로 분석"""

    def __init__(self):
        self.client = None
        if Config.CLAUDE_API_KEY:
            self.client = anthropic.Anthropic(api_key=Config.CLAUDE_API_KEY)
        else:
            logger.warning("CLAUDE_API_KEY 미설정 — AI 분석 비활성화")

    def analyze_department(self, department: str, metrics: dict, mode: str) -> tuple:
        """
        부서 메트릭 분석

        Returns:
            (analysis_text, tokens_used) — 실패 시 (None, 0)
        """
        if not self.client:
            return None, 0

        prompts = DAILY_PROMPTS if mode == 'daily' else WEEKLY_PROMPTS
        dept_prompt = prompts.get(department)
        if not dept_prompt:
            logger.warning(f"[{department}] {mode} 프롬프트 없음")
            return None, 0

        # 메트릭을 JSON 문자열로 변환
        metrics_text = json.dumps(metrics, ensure_ascii=False, indent=2, default=str)
        user_content = dept_prompt['user_prefix'] + metrics_text

        # 일간은 haiku (저렴), 주간은 sonnet (깊은 분석)
        model = MODEL_HAIKU if mode == 'daily' else MODEL_SONNET

        try:
            message = _call_with_retry(
                self.client,
                model=model,
                max_tokens=512 if mode == 'daily' else 1024,
                system=dept_prompt['system'],
                messages=[{'role': 'user', 'content': user_content}],
            )
            text = message.content[0].text.strip()
            tokens = message.usage.input_tokens + message.usage.output_tokens
            logger.info(f"[{department}] 분석 완료 ({tokens} 토큰)")
            return text, tokens
        except Exception as e:
            logger.error(f"[{department}] Claude 분석 ��패: {e}")
            return None, 0

    def analyze_coo(self, reports_text: str, mode: str) -> tuple:
        """
        COO 종합 분석

        Returns:
            (analysis_text, tokens_used)
        """
        if not self.client:
            return None, 0

        from analyzers.prompts import COO_DAILY_PROMPT, COO_WEEKLY_PROMPT
        coo_prompt = COO_DAILY_PROMPT if mode == 'daily' else COO_WEEKLY_PROMPT

        user_content = coo_prompt['user_prefix'] + reports_text

        try:
            message = _call_with_retry(
                self.client,
                model=MODEL_SONNET,  # COO는 항상 sonnet
                max_tokens=1024 if mode == 'daily' else 2048,
                system=coo_prompt['system'],
                messages=[{'role': 'user', 'content': user_content}],
            )
            text = message.content[0].text.strip()
            tokens = message.usage.input_tokens + message.usage.output_tokens
            logger.info(f"[COO] 취합 완료 ({tokens} 토큰)")
            return text, tokens
        except Exception as e:
            logger.error(f"[COO] Claude 분석 실패: {e}")
            return None, 0

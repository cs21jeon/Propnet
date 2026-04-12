"""
BaseCollector - 모든 부서 collector의 추상 베이스 클래스
"""
import logging
import psycopg2
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)


class BaseCollector:
    """부서별 데이터 수집기 베이스 클래스"""

    department = ''       # e.g. 'infra', 'dev'
    display_name = ''     # e.g. '인프라부', '개발부'
    supports_daily = False
    supports_weekly = False

    def collect_daily(self) -> dict:
        """일간 메트릭 수집. 지원하는 collector만 구현."""
        raise NotImplementedError

    def collect_weekly(self) -> dict:
        """주간 메트릭 수집. 지원하는 collector만 구현."""
        raise NotImplementedError

    def collect(self, mode: str) -> dict:
        """mode에 따라 적절한 수집 메서드 호출"""
        try:
            if mode == 'daily' and self.supports_daily:
                return self.collect_daily()
            elif mode == 'weekly' and self.supports_weekly:
                return self.collect_weekly()
            else:
                return {'skipped': True, 'reason': f'{mode} 모드 미지원'}
        except Exception as e:
            logger.error(f"[{self.department}] 수집 실패: {e}", exc_info=True)
            return {'error': str(e)}

    @contextmanager
    def get_main_db(self):
        """goldenrabbit_db 연결 (context manager)"""
        conn = psycopg2.connect(
            host=Config.MAIN_DB_HOST,
            port=Config.MAIN_DB_PORT,
            dbname=Config.MAIN_DB_NAME,
            user=Config.MAIN_DB_USER,
            password=Config.MAIN_DB_PASS,
            connect_timeout=10,
        )
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def get_voice_db(self):
        """voiceroom DB 연결 (context manager)"""
        conn = psycopg2.connect(
            host=Config.VOICE_DB_HOST,
            port=Config.VOICE_DB_PORT,
            dbname=Config.VOICE_DB_NAME,
            user=Config.VOICE_DB_USER,
            password=Config.VOICE_DB_PASS,
            connect_timeout=10,
        )
        try:
            yield conn
        finally:
            conn.close()

    def query_one(self, conn, sql, params=None):
        """단일 행 조회"""
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            row = cur.fetchone()
            return dict(zip(cols, row)) if row else {}

    def query_all(self, conn, sql, params=None):
        """전체 행 조회"""
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def query_scalar(self, conn, sql, params=None):
        """단일 값 조회"""
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return row[0] if row else None

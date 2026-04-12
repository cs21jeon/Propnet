"""
보고서 저장 — DB + JSON 파일
"""
import os
import json
import logging
import psycopg2
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

# DB 테이블 생성 DDL
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS propnet_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    report_type VARCHAR(10) NOT NULL,
    raw_metrics JSONB NOT NULL DEFAULT '{}',
    department_reports JSONB NOT NULL DEFAULT '{}',
    executive_summary TEXT,
    critical_issues JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    html_report TEXT,
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    generation_seconds FLOAT,
    claude_tokens_used INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(report_date, report_type)
);
"""


def ensure_table():
    """propnet_reports 테이블이 없으면 생성"""
    try:
        conn = psycopg2.connect(
            host=Config.MAIN_DB_HOST,
            port=Config.MAIN_DB_PORT,
            dbname=Config.MAIN_DB_NAME,
            user=Config.MAIN_DB_USER,
            password=Config.MAIN_DB_PASS,
            connect_timeout=10,
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLE_SQL)
        conn.close()
        logger.info("propnet_reports 테이블 확인/생성 완료")
    except Exception as e:
        logger.error(f"테이블 생성 실패: {e}")


def save_report(report_data: dict, dry_run: bool = False):
    """보고서를 DB + JSON 파일로 저장"""
    # 1. JSON 파일 저장 (항상)
    _save_json(report_data)

    # 2. DB 저장 (dry_run이 아닐 때)
    if not dry_run:
        _save_db(report_data)


def _save_json(report_data: dict):
    """JSON 파일로 저장"""
    try:
        output_dir = Config.REPORT_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)

        report_date = report_data['report_date']
        report_type = report_data['report_type']
        filename = f"{report_date}_{report_type}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"JSON 저장: {filepath}")
    except Exception as e:
        logger.error(f"JSON 저장 실패: {e}")


def _save_db(report_data: dict):
    """DB에 저장 (UPSERT)"""
    try:
        conn = psycopg2.connect(
            host=Config.MAIN_DB_HOST,
            port=Config.MAIN_DB_PORT,
            dbname=Config.MAIN_DB_NAME,
            user=Config.MAIN_DB_USER,
            password=Config.MAIN_DB_PASS,
            connect_timeout=10,
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO propnet_reports
                        (report_date, report_type, raw_metrics, department_reports,
                         executive_summary, critical_issues, recommendations,
                         html_report, email_sent, email_sent_at,
                         generation_seconds, claude_tokens_used, errors)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (report_date, report_type) DO UPDATE SET
                        raw_metrics = EXCLUDED.raw_metrics,
                        department_reports = EXCLUDED.department_reports,
                        executive_summary = EXCLUDED.executive_summary,
                        critical_issues = EXCLUDED.critical_issues,
                        recommendations = EXCLUDED.recommendations,
                        html_report = EXCLUDED.html_report,
                        email_sent = EXCLUDED.email_sent,
                        email_sent_at = EXCLUDED.email_sent_at,
                        generation_seconds = EXCLUDED.generation_seconds,
                        claude_tokens_used = EXCLUDED.claude_tokens_used,
                        errors = EXCLUDED.errors
                """, (
                    report_data['report_date'],
                    report_data['report_type'],
                    json.dumps(report_data.get('raw_metrics', {}), ensure_ascii=False, default=str),
                    json.dumps(report_data.get('department_reports', {}), ensure_ascii=False, default=str),
                    report_data.get('executive_summary', ''),
                    json.dumps(report_data.get('critical_issues', []), ensure_ascii=False),
                    json.dumps(report_data.get('recommendations', []), ensure_ascii=False),
                    report_data.get('html_report', ''),
                    report_data.get('email_sent', False),
                    datetime.now() if report_data.get('email_sent') else None,
                    report_data.get('generation_seconds', 0),
                    report_data.get('claude_tokens_used', 0),
                    json.dumps(report_data.get('errors', []), ensure_ascii=False),
                ))
        conn.close()
        logger.info("DB 저장 완료")
    except Exception as e:
        logger.error(f"DB 저장 실패: {e}")

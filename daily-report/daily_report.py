#!/usr/bin/env python3
"""
PropNet 보고 시스템 메인 진입점

Usage:
    python daily_report.py --mode daily          # 일간 보고
    python daily_report.py --mode weekly         # 주간 보고
    python daily_report.py --mode daily --dry-run  # 이메일 미발송 (테스트)
"""
import argparse
import json
import logging
import sys
import time
from datetime import datetime, date

from config import Config
from collectors.infra_collector import InfraCollector
from collectors.growth_collector import GrowthCollector
from collectors.dev_collector import DevCollector
from collectors.qa_collector import QACollector
from collectors.cs_collector import CSCollector
from collectors.pm_collector import PMCollector
from collectors.design_collector import DesignCollector
from analyzers.claude_analyzer import ClaudeAnalyzer
from report.aggregator import aggregate_reports
from report.email_sender import send_report_email
from storage.report_storage import save_report

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger('daily_report')

# 부서별 collector 등록
ALL_COLLECTORS = [
    InfraCollector(),
    DevCollector(),
    QACollector(),
    GrowthCollector(),
    CSCollector(),
    PMCollector(),
    DesignCollector(),
]


def run_report(mode: str, dry_run: bool = False):
    """보고서 생성 파이프라인"""
    start_time = time.time()
    today = date.today()
    errors = []
    total_tokens = 0

    logger.info(f"=== PropNet {mode} 보고서 생성 시작 ({today}) ===")

    # 1. 해당 mode를 지원하는 collector만 필터링
    active_collectors = [
        c for c in ALL_COLLECTORS
        if (mode == 'daily' and c.supports_daily) or
           (mode == 'weekly' and c.supports_weekly)
    ]

    logger.info(f"활성 부서: {[c.department for c in active_collectors]}")

    # 2. 순차적으로 메트릭 수집 (RAM 제약)
    raw_metrics = {}
    for collector in active_collectors:
        logger.info(f"[{collector.department}] 수집 시작...")
        metrics = collector.collect(mode)
        raw_metrics[collector.department] = metrics
        if 'error' in metrics:
            errors.append(f"{collector.department}: {metrics['error']}")
            logger.warning(f"[{collector.department}] 수집 실패: {metrics['error']}")
        else:
            logger.info(f"[{collector.department}] 수집 완료")

    # 3. Claude API로 부서별 분석
    analyzer = ClaudeAnalyzer()
    department_reports = {}

    for collector in active_collectors:
        dept = collector.department
        metrics = raw_metrics.get(dept, {})
        if 'error' in metrics or metrics.get('skipped'):
            department_reports[dept] = {
                'display_name': collector.display_name,
                'analysis': f"[수집 실패] {metrics.get('error', '스킵됨')}",
                'raw_only': True,
            }
            continue

        logger.info(f"[{dept}] AI 분석 중...")
        analysis, tokens = analyzer.analyze_department(dept, metrics, mode)
        total_tokens += tokens
        department_reports[dept] = {
            'display_name': collector.display_name,
            'analysis': analysis,
            'raw_only': analysis is None,
        }
        if analysis is None:
            errors.append(f"{dept}: Claude API 분석 실패")
            # fallback: raw 데이터를 텍스트로 포맷
            department_reports[dept]['analysis'] = _format_raw_fallback(metrics)
            department_reports[dept]['raw_only'] = True

    # 4. COO 취합
    logger.info("COO 취합 분석 중...")
    coo_result, coo_tokens = aggregate_reports(
        analyzer, department_reports, raw_metrics, mode, today
    )
    total_tokens += coo_tokens

    # 5. 결과 조합
    generation_seconds = time.time() - start_time
    report_data = {
        'report_date': today.isoformat(),
        'report_type': mode,
        'raw_metrics': raw_metrics,
        'department_reports': {
            dept: {
                'display_name': dr['display_name'],
                'analysis': dr['analysis'],
            }
            for dept, dr in department_reports.items()
        },
        'executive_summary': coo_result.get('executive_summary', ''),
        'critical_issues': coo_result.get('critical_issues', []),
        'recommendations': coo_result.get('recommendations', []),
        'generation_seconds': round(generation_seconds, 1),
        'claude_tokens_used': total_tokens,
        'errors': errors,
    }

    # 6. 저장
    logger.info("보고서 저장 중...")
    save_report(report_data, dry_run=dry_run)

    # 7. 이메일 발송
    if dry_run:
        logger.info("[DRY RUN] 이메일 미발송. 보고서 내용:")
        print(json.dumps(report_data, ensure_ascii=False, indent=2, default=str))
    else:
        logger.info("이메일 발송 중...")
        email_sent = send_report_email(report_data)
        report_data['email_sent'] = email_sent
        if not email_sent:
            errors.append("이메일 발송 실패")
            logger.warning("이메일 발송 실패. 5분 후 재시도...")
            time.sleep(300)
            email_sent = send_report_email(report_data)
            if email_sent:
                logger.info("이메일 재시도 성공")
            else:
                logger.error("이메일 재시도도 실패")

    logger.info(
        f"=== 보고서 생성 완료 ({generation_seconds:.1f}초, "
        f"토큰: {total_tokens}, 에러: {len(errors)}건) ==="
    )
    return report_data


def _format_raw_fallback(metrics: dict) -> str:
    """Claude API 실패 시 raw 데이터를 텍스트로 포맷"""
    lines = ["[AI 분석 실패 - 원시 데이터]"]
    for key, value in metrics.items():
        if isinstance(value, dict):
            lines.append(f"\n{key}:")
            for k, v in value.items():
                lines.append(f"  - {k}: {v}")
        elif isinstance(value, list):
            lines.append(f"\n{key}: {len(value)}건")
        else:
            lines.append(f"- {key}: {value}")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='PropNet 보고 시스템')
    parser.add_argument(
        '--mode', choices=['daily', 'weekly'], required=True,
        help='보고 모드: daily(일간) 또는 weekly(주간)'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='이메일 미발송, 콘솔 출력만'
    )
    args = parser.parse_args()

    run_report(mode=args.mode, dry_run=args.dry_run)


if __name__ == '__main__':
    main()

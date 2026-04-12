"""
COO 취합 — 전 부서 보고를 종합하여 경영진 보고 생성
"""
import json
import logging

logger = logging.getLogger(__name__)


def aggregate_reports(analyzer, department_reports: dict, raw_metrics: dict,
                      mode: str, report_date) -> tuple:
    """
    전 부서 보고를 COO가 종합 분석

    Returns:
        (result_dict, tokens_used)
        result_dict = {
            'executive_summary': str,
            'critical_issues': list,
            'recommendations': list,
        }
    """
    # 부서별 분석 결과를 하나의 텍스트로 조합
    lines = []
    for dept, report in department_reports.items():
        display_name = report.get('display_name', dept)
        analysis = report.get('analysis', '데이터 없음')
        lines.append(f"## {display_name} ({dept})\n{analysis}\n")

    reports_text = '\n'.join(lines)

    # Claude COO 분석
    coo_text, tokens = analyzer.analyze_coo(reports_text, mode)

    if coo_text:
        # COO 응답을 구조화 (간단 파싱)
        result = {
            'executive_summary': coo_text,
            'critical_issues': _extract_section(coo_text, '긴급', '주의'),
            'recommendations': _extract_section(coo_text, '조치', '추천', 'Focus', '액션'),
        }
    else:
        # Claude 실패 시 fallback
        result = {
            'executive_summary': _fallback_summary(department_reports, mode),
            'critical_issues': _find_errors(department_reports),
            'recommendations': [],
        }

    return result, tokens


def _extract_section(text: str, *keywords) -> list:
    """텍스트에서 특정 키워드가 포함된 섹션의 항목 추출"""
    items = []
    in_section = False
    for line in text.split('\n'):
        line = line.strip()
        if any(kw in line for kw in keywords):
            in_section = True
            continue
        if in_section:
            if line.startswith(('-', '*', '•', '1', '2', '3', '4', '5')):
                items.append(line.lstrip('-*• 0123456789.').strip())
            elif line.startswith('#') or (line == '' and items):
                break
    return items


def _fallback_summary(department_reports: dict, mode: str) -> str:
    """Claude 실패 시 간단 요약"""
    label = '일간' if mode == 'daily' else '주간'
    errors = [dept for dept, r in department_reports.items() if r.get('raw_only')]
    if errors:
        return f"[AI 분석 실패 — 원시 데이터 {label} 보고] 분석 실패 부서: {', '.join(errors)}"
    return f"[{label} 보고] 전 부서 데이터 수집 완료 (AI 분석 미수행)"


def _find_errors(department_reports: dict) -> list:
    """에러가 있는 부서 목록"""
    return [
        f"{dept}: 수집/분석 실패"
        for dept, r in department_reports.items()
        if r.get('raw_only')
    ]

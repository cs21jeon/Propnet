"""
이메일 발송 — Gmail SMTP로 HTML 보고서 발송
마크다운 → HTML 변환하여 Gmail에서 깔끔하게 표시
"""
import os
import smtplib
import logging
import markdown
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, timedelta

from config import Config

logger = logging.getLogger(__name__)

# markdown → HTML 변환기 (표, 코드블록 지원)
MD = markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br'])


def md_to_html(text: str) -> str:
    """마크다운 텍스트를 HTML로 변환 + Gmail용 인라인 스타일 주입"""
    if not text:
        return ''
    MD.reset()
    html = MD.convert(text)
    # Gmail은 <style> 태그를 무시하므로 테이블에 인라인 스타일 직접 주입
    html = html.replace(
        '<table>',
        '<table style="border-collapse:collapse;width:100%;margin:8px 0;font-size:13px;">'
    )
    html = html.replace(
        '<th>',
        '<th style="background:#f0f4ff;color:#333;padding:8px 12px;text-align:left;'
        'border:1px solid #ddd;font-weight:600;">'
    )
    html = html.replace(
        '<td>',
        '<td style="padding:6px 12px;border:1px solid #e8e8e8;">'
    )
    html = html.replace(
        '<thead>',
        '<thead style="background:#f0f4ff;">'
    )
    return html


def send_report_email(report_data: dict) -> bool:
    """보고서 이메일 발송"""
    if not Config.EMAIL_ADDRESS or not Config.EMAIL_PASSWORD:
        logger.error("EMAIL_ADDRESS/EMAIL_PASSWORD 미설정")
        return False

    mode = report_data['report_type']
    report_date = report_data['report_date']

    subject = _make_subject(mode, report_date)
    html_body = _build_html(report_data)
    report_data['html_report'] = html_body

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = Config.EMAIL_ADDRESS
        msg['To'] = Config.REPORT_RECIPIENT
        msg['Subject'] = subject

        # 텍스트 fallback (마크다운 그대로)
        text_body = report_data.get('executive_summary', '')
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"이메일 발송 완료: {subject} → {Config.REPORT_RECIPIENT}")
        return True

    except Exception as e:
        logger.error(f"이메일 발송 실패: {e}", exc_info=True)
        return False


def _make_subject(mode: str, report_date: str) -> str:
    """이메일 제목 생성"""
    day_names = ['월', '화', '수', '목', '금', '토', '일']
    d = date.fromisoformat(report_date) if isinstance(report_date, str) else report_date
    day_name = day_names[d.weekday()]

    if mode == 'daily':
        return f"[PropNet 일간보고] {d.strftime('%Y-%m-%d')} ({day_name})"
    else:
        week_start = d - timedelta(days=d.weekday())
        week_end = week_start + timedelta(days=6)
        week_num = d.isocalendar()[1]
        return (
            f"[PropNet 주간보고] "
            f"{week_start.strftime('%m-%d')} ~ {week_end.strftime('%m-%d')} "
            f"({week_num}주차)"
        )


def _build_html(report_data: dict) -> str:
    """보고서 데이터를 HTML 이메일로 변환"""
    mode = report_data['report_type']
    label = '일간' if mode == 'daily' else '주간'
    summary = report_data.get('executive_summary', '')
    dept_reports = report_data.get('department_reports', {})
    critical = report_data.get('critical_issues', [])
    recommendations = report_data.get('recommendations', [])
    errors = report_data.get('errors', [])
    gen_sec = report_data.get('generation_seconds', 0)
    tokens = report_data.get('claude_tokens_used', 0)

    # COO 요약 (마크다운 → HTML)
    summary_html = md_to_html(summary)

    # 긴급 이슈
    critical_html = ''
    critical_items = [c for c in critical if c and c.strip()]
    if critical_items:
        items = ''.join(f'<li style="margin:4px 0;">{c}</li>' for c in critical_items)
        critical_html = f'''
        <div style="margin:16px 0;padding:14px 18px;background:#fce4ec;
        border-left:5px solid #c62828;border-radius:6px;">
        <div style="font-weight:700;color:#c62828;margin-bottom:8px;">긴급 이슈</div>
        <ul style="margin:0;padding-left:20px;color:#b71c1c;">{items}</ul>
        </div>'''

    # 추천 조치
    rec_html = ''
    rec_items = [r for r in recommendations if r and r.strip()]
    if rec_items:
        items = ''.join(f'<li style="margin:4px 0;">{r}</li>' for r in rec_items)
        rec_html = f'''
        <div style="margin:16px 0;padding:14px 18px;background:#e8f5e9;
        border-left:5px solid #2e7d32;border-radius:6px;">
        <div style="font-weight:700;color:#2e7d32;margin-bottom:8px;">조치 필요</div>
        <ol style="margin:0;padding-left:20px;color:#1b5e20;">{items}</ol>
        </div>'''

    # 부서별 보고 (마크다운 → HTML)
    colors = ['#1565c0', '#2e7d32', '#e65100', '#6a1b9a', '#00838f', '#c62828', '#4e342e']
    sections = []
    for i, (dept, info) in enumerate(dept_reports.items()):
        name = info.get('display_name', dept)
        analysis = info.get('analysis', '')
        analysis_html = md_to_html(analysis)
        color = colors[i % len(colors)]
        sections.append(f'''
        <div style="margin:14px 0;padding:14px 18px;background:#fafafa;
        border-left:5px solid {color};border-radius:6px;">
        <div style="font-weight:700;color:{color};font-size:15px;margin-bottom:8px;">{name}</div>
        <div style="font-size:13px;color:#444;line-height:1.7;">{analysis_html}</div>
        </div>''')

    # 에러
    error_html = ''
    if errors:
        items = ''.join(f'<li>{e}</li>' for e in errors)
        error_html = f'''
        <div style="margin:16px 0;padding:10px 16px;background:#fffbe6;
        border-left:4px solid #f9a825;border-radius:4px;">
        <div style="font-weight:700;color:#f57f17;">수집 에러</div>
        <ul style="font-size:12px;color:#666;">{items}</ul>
        </div>'''

    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
  body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans KR',sans-serif;
         max-width:680px;margin:0 auto;padding:20px;color:#333;background:#fff; }}
  table {{ border-collapse:collapse;width:100%;margin:8px 0;font-size:13px; }}
  th {{ background:#f0f4ff;color:#333;padding:8px 12px;text-align:left;
       border:1px solid #ddd;font-weight:600; }}
  td {{ padding:6px 12px;border:1px solid #e8e8e8; }}
  tr:nth-child(even) {{ background:#f9f9f9; }}
  h1,h2,h3 {{ margin:12px 0 6px; }}
  ul,ol {{ padding-left:20px;margin:6px 0; }}
  li {{ margin:3px 0; }}
  hr {{ border:none;border-top:1px solid #e0e0e0;margin:16px 0; }}
  p {{ margin:6px 0;line-height:1.6; }}
</style>
</head>
<body>

<div style="text-align:center;padding:16px 0;border-bottom:3px solid #1a73e8;">
  <div style="color:#1a73e8;font-size:22px;font-weight:700;">PropNet {label} 보고</div>
  <div style="color:#888;font-size:13px;margin-top:4px;">{report_data['report_date']}</div>
</div>

<div style="margin:20px 0;padding:18px;background:linear-gradient(135deg,#e8f0fe,#f0f4ff);
border-radius:10px;line-height:1.7;">
{summary_html}
</div>

{critical_html}
{rec_html}

<div style="margin:24px 0 8px;font-size:17px;font-weight:700;color:#37474f;
border-bottom:1px solid #e0e0e0;padding-bottom:6px;">부서별 보고</div>

{''.join(sections)}

{error_html}

<div style="margin-top:28px;padding-top:14px;border-top:2px solid #e0e0e0;
text-align:center;font-size:11px;color:#aaa;">
생성 {gen_sec}초 | {tokens} 토큰 | PropNet AI Report System
</div>

</body>
</html>'''

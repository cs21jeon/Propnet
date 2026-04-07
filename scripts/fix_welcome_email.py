#!/usr/bin/env python3
"""환영 이메일 템플릿 교체 스크립트 - 서버에서 실행"""
import re

path = '/home/webapp/goldenrabbit/backend/property-manager/services/admin_dashboard_service.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# html_body 블록을 통째로 교체
# 시작: '    html_body = f"""' ~ 끝: 다음 '    """'
pattern = r'(    html_body = f""")(.*?)(    """)'

new_html = r'''    html_body = f"""
    <div style="max-width:520px;margin:0 auto;font-family:'Apple SD Gothic Neo',sans-serif;color:#333;font-size:13px;">
      <div style="background:#2962FF;color:white;padding:20px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="margin:0;font-size:18px;">PropNet 중개사 등록 완료</h1>
      </div>
      <div style="padding:20px;background:#fff;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 8px 8px;">
        <p><b>{agent_name}</b>님, 환영합니다! 아래 서비스를 바로 사용하실 수 있습니다.</p>

        <table width="100%%" cellpadding="0" cellspacing="0" style="margin:14px 0;border-collapse:separate;border-spacing:0 6px;">
          <tr><td style="padding:12px;border-radius:8px;border:1px solid #d0e0f0;background:#f8faff;">
            <b style="font-size:13px;">📊 매물관리 (PropSheet)</b>
            <p style="font-size:11px;color:#888;margin:4px 0;">매물 등록/관리, 스프레드시트형 데이터베이스</p>
            <a href="https://propnet.kr/propsheet/{agent_slug}/" style="color:#2962FF;text-decoration:none;font-size:12px;">PC/모바일 웹 열기</a>
          </td></tr>
          <tr><td style="padding:12px;border-radius:8px;border:1px solid #c8e6c9;background:#f5fff8;">
            <b style="font-size:13px;">📖 부동산백과 (Proppedia)</b>
            <p style="font-size:11px;color:#888;margin:4px 0;">건축물대장, 등기부등본, 토지이용계획 조회</p>
            <a href="https://propnet.kr/app/" style="color:#2962FF;text-decoration:none;font-size:12px;">PC 웹 열기</a>
            <span style="color:#ccc;margin:0 4px;">|</span>
            <a href="https://play.google.com/store/apps/details?id=com.propnet.propedia" style="color:#2962FF;text-decoration:none;font-size:12px;">Android 앱 설치</a>
          </td></tr>
          <tr><td style="padding:12px;border-radius:8px;border:1px solid #ffe0b2;background:#fff8f5;">
            <b style="font-size:13px;">🗺 매물지도 (PropMap)</b>
            <p style="font-size:11px;color:#888;margin:4px 0;">등록 매물을 지도에 표시, 고객 공유용</p>
            <a href="https://propnet.kr/propmap/{agent_slug}/" style="color:#2962FF;text-decoration:none;font-size:12px;">PC/모바일 웹 열기</a>
          </td></tr>
          <tr><td style="padding:12px;border-radius:8px;border:1px solid #d1c4e9;background:#f5f5ff;">
            <b style="font-size:13px;">🎙 업무톡 (Proptalk)</b>
            <p style="font-size:11px;color:#888;margin:4px 0;">통화 녹음 AI 변환, 팀 채팅, 업무 공유</p>
            <a href="https://propnet.kr/proptalk/web/" style="color:#2962FF;text-decoration:none;font-size:12px;">PC 웹 열기</a>
            <span style="color:#ccc;margin:0 4px;">|</span>
            <a href="https://play.google.com/store/apps/details?id=com.propnet.proptalk" style="color:#2962FF;text-decoration:none;font-size:12px;">Android 앱 설치</a>
          </td></tr>
        </table>

        <table width="100%%" cellpadding="0" cellspacing="0" style="margin-top:10px;"><tr><td style="padding:10px;background:#fafafa;border-radius:8px;">
          <p style="font-size:11px;font-weight:600;margin:0 0 4px;">사용 가이드</p>
          <p style="font-size:11px;margin:0;">
            <a href="https://propnet.kr/propsheet/guide" style="color:#2962FF;text-decoration:none;">PropSheet</a>
            <span style="color:#ccc;margin:0 3px;">&middot;</span>
            <a href="https://propnet.kr/app/guide" style="color:#2962FF;text-decoration:none;">Proppedia</a>
            <span style="color:#ccc;margin:0 3px;">&middot;</span>
            <a href="https://propnet.kr/proptalk/" style="color:#2962FF;text-decoration:none;">Proptalk</a>
          </p>
        </td></tr></table>

        <hr style="border:none;border-top:1px solid #eee;margin:14px 0;">
        <p style="font-size:11px;color:#999;text-align:center;">본 메일은 PropNet에서 자동 발송되었습니다.</p>
      </div>
    </div>
    """'''

result = re.sub(pattern, new_html, content, count=1, flags=re.DOTALL)

if result != content:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(result)
    print('SUCCESS: Welcome email template replaced')
else:
    print('FAILED: Pattern not matched')

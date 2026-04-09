#!/usr/bin/env python3
"""agent 신청 시 관리자에게 메일 알림 추가"""

path = '/home/webapp/goldenrabbit/backend/property-manager/routes/register.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old = '''        logger.info(f"Agent registration request: propnet_user_id={propnet_user_id}, "
                     f"company={company_name}, slug={slug}")

        return redirect('/register/complete?role=agent&status=pending')'''

new = '''        logger.info(f"Agent registration request: propnet_user_id={propnet_user_id}, "
                     f"company={company_name}, slug={slug}")

        # 관리자에게 신청 알림 메일 발송
        try:
            _notify_admin_agent_request(company_name, slug, representative, phone, address)
        except Exception as mail_err:
            logger.error(f"Admin notification email failed: {mail_err}")

        return redirect('/register/complete?role=agent&status=pending')'''

if old in c:
    c = c.replace(old, new)
    print('[1] 알림 호출 추가 완료')
else:
    print('[1] 패턴 불일치')

# 함수 정의 추가 (파일 상단, import 뒤)
func = '''

def _notify_admin_agent_request(company_name, slug, representative, phone, address):
    """관리자에게 Agent 신청 알림 이메일"""
    import smtplib
    import threading
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    email_address = os.environ.get('EMAIL_ADDRESS')
    email_password = os.environ.get('EMAIL_PASSWORD')
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    admin_email = 'cs21.jeon@gmail.com'

    if not email_address or not email_password:
        return

    html = f"""
    <div style="max-width:500px;font-family:sans-serif;color:#333;">
      <h2 style="color:#f57f17;margin-bottom:16px;">새 Agent 가입 신청</h2>
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <tr><td style="padding:6px 0;color:#888;width:100px;">사무소명</td><td style="padding:6px 0;font-weight:600;">{company_name}</td></tr>
        <tr><td style="padding:6px 0;color:#888;">slug</td><td style="padding:6px 0;"><code>{slug}</code></td></tr>
        <tr><td style="padding:6px 0;color:#888;">대표자</td><td style="padding:6px 0;">{representative}</td></tr>
        <tr><td style="padding:6px 0;color:#888;">연락처</td><td style="padding:6px 0;">{phone}</td></tr>
        <tr><td style="padding:6px 0;color:#888;">주소</td><td style="padding:6px 0;">{address}</td></tr>
      </table>
      <div style="margin-top:20px;">
        <a href="https://propnet.kr/admin/agent-requests"
           style="display:inline-block;padding:10px 24px;background:#2962FF;color:white;text-decoration:none;border-radius:6px;font-size:14px;">
          승인 대시보드 열기
        </a>
      </div>
      <p style="margin-top:16px;font-size:12px;color:#999;">PropNet 자동 알림</p>
    </div>
    """

    def _send():
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'[PropNet] 새 Agent 신청: {company_name}'
            msg['From'] = email_address
            msg['To'] = admin_email
            msg.attach(MIMEText(html, 'html', 'utf-8'))
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_address, email_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Admin notified: new agent request {company_name}")
        except Exception as e:
            logger.error(f"Admin notify email failed: {e}")

    threading.Thread(target=_send, daemon=True).start()

'''

# import os 확인 후 함수 추가
marker = '\nbp = Blueprint'
if '_notify_admin_agent_request' not in c:
    c = c.replace(marker, func + 'bp = Blueprint')
    print('[2] 알림 함수 추가 완료')
else:
    print('[2] 이미 존재')

# import os 확인
if 'import os' not in c.split('\n')[0:20]:
    c = 'import os\n' + c
    print('[3] import os 추가')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('완료')

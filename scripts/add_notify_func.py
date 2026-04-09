#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/register.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

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

# bp = Blueprint 라인 바로 위에 삽입
if 'def _notify_admin_agent_request' not in c:
    c = c.replace("bp = Blueprint('register'", func + "bp = Blueprint('register'")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('함수 추가 완료')
else:
    print('이미 존재')

#!/usr/bin/env python3
"""submit-inquiry API: agent_slug 지원 + agent 이메일 알림"""

path = '/home/webapp/goldenrabbit/backend/property-manager/routes/propnet_api.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 기존 submit_inquiry 함수의 try 블록 내 INSERT 부분을 수정
# agent_slug가 있으면 해당 agent의 inquiry DB에 저장

old_try = '''    try:
        record_id = ensure_unique_record_id(INQUIRY_TABLE)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO inquiry (database_id, record_id, "매물종류", "연락처", "이메일", "문의사항", "이메일발송") '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (INQUIRY_DB_ID, record_id, property_type, data.get("phone"), email, data.get("message"), '')
                )
                conn.commit()

        logger.info(f"레코드 생성 완료: {record_id}")

        # 백그라운드에서 이메일 발송 및 DB 업데이트
        threading.Thread(
            target=send_email_and_update_db,
            args=(data, email, email_valid, record_id),
            daemon=True
        ).start()'''

new_try = '''    try:
        # agent_slug가 있으면 해당 agent의 inquiry DB에 저장
        agent_slug = data.get('agent_slug', '')
        target_table = INQUIRY_TABLE
        target_db_id = INQUIRY_DB_ID
        agent_email_addr = None

        if agent_slug:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # agent의 inquiry DB 찾기
                    cur.execute("""
                        SELECT d.id, d.table_name FROM databases d
                        JOIN workspaces w ON d.workspace_id = w.id
                        JOIN agents a ON w.agent_id = a.id
                        WHERE a.slug = %s AND d.slug = 'inquiry'
                        LIMIT 1
                    """, (agent_slug,))
                    row = cur.fetchone()
                    if row:
                        target_db_id = row[0]
                        target_table = row[1]
                        logger.info(f"Agent inquiry DB: {target_table} (db_id={target_db_id})")

                    # agent 이메일 조회
                    cur.execute("SELECT email, agency_name FROM agents WHERE slug = %s", (agent_slug,))
                    agent_row = cur.fetchone()
                    if agent_row:
                        agent_email_addr = agent_row[0]

        record_id = ensure_unique_record_id(target_table)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f'INSERT INTO "{target_table}" (database_id, record_id, "매물종류", "연락처", "이메일", "문의사항", "이메일발송") '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (target_db_id, record_id, property_type, data.get("phone"), email, data.get("message"), '')
                )
                conn.commit()

        logger.info(f"레코드 생성 완료: {record_id} (table={target_table})")

        # 백그라운드에서 이메일 발송 및 DB 업데이트
        threading.Thread(
            target=send_email_and_update_db,
            args=(data, email, email_valid, record_id, target_table, agent_email_addr),
            daemon=True
        ).start()'''

if old_try in c:
    c = c.replace(old_try, new_try)
    print('[1] submit_inquiry 수정 완료')
else:
    print('[1] 패턴 불일치')

# send_email_and_update_db 함수에 agent_email 파라미터 추가
old_func = 'def send_email_and_update_db(data, email, email_valid, record_id):'
new_func = 'def send_email_and_update_db(data, email, email_valid, record_id, table_name=None, agent_email_addr=None):'

if old_func in c:
    c = c.replace(old_func, new_func)
    print('[2] 함수 시그니처 수정 완료')
else:
    print('[2] 함수 시그니처 패턴 불일치')

# DB 업데이트에서 테이블명도 동적으로
old_update = """        # DB '이메일발송' 업데이트
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE inquiry SET "이메일발송" = %s WHERE record_id = %s',
                    ('O', record_id)
                )
                conn.commit()"""

new_update = """        # DB '이메일발송' 업데이트
        _tbl = table_name or 'inquiry'
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f'UPDATE "{_tbl}" SET "이메일발송" = %s WHERE record_id = %s',
                    ('O', record_id)
                )
                conn.commit()

        # agent 이메일로도 알림
        if agent_email_addr:
            try:
                _send_agent_inquiry_notification(agent_email_addr, data)
            except Exception as ae:
                logger.error(f"Agent 알림 이메일 실패: {ae}")"""

if old_update in c:
    c = c.replace(old_update, new_update)
    print('[3] DB 업데이트 + agent 알림 추가 완료')
else:
    print('[3] DB 업데이트 패턴 불일치')

# agent 알림 함수 추가 (send_consultation_email 함수 위에)
agent_notify_func = '''
def _send_agent_inquiry_notification(agent_email, customer_data):
    """agent에게 상담 접수 알림"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    email_addr = os.environ.get('EMAIL_ADDRESS')
    email_pass = os.environ.get('EMAIL_PASSWORD')
    if not email_addr or not email_pass:
        return

    property_type_map = {
        'house': '단독/다가구', 'mixed': '상가주택',
        'commercial': '상업용건물', 'land': '재건축/토지', 'sell': '매물접수'
    }
    ptype = property_type_map.get(customer_data.get('propertyType', ''), '기타')

    html = f"""
    <div style="max-width:500px;font-family:sans-serif;color:#333;">
      <h2 style="color:#136dec;margin-bottom:16px;">새 상담 문의가 접수되었습니다</h2>
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <tr><td style="padding:6px 0;color:#888;width:80px;">매물종류</td><td style="padding:6px 0;font-weight:600;">{ptype}</td></tr>
        <tr><td style="padding:6px 0;color:#888;">연락처</td><td style="padding:6px 0;">{customer_data.get('phone', '-')}</td></tr>
        <tr><td style="padding:6px 0;color:#888;">이메일</td><td style="padding:6px 0;">{customer_data.get('email', '-')}</td></tr>
        <tr><td style="padding:6px 0;color:#888;">문의사항</td><td style="padding:6px 0;">{customer_data.get('message', '-')}</td></tr>
      </table>
      <p style="margin-top:16px;font-size:12px;color:#999;">PropNet 매물지도를 통한 상담 문의입니다.</p>
    </div>
    """

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'[PropNet] 새 상담 문의: {ptype} - {customer_data.get("phone", "")}'
        msg['From'] = email_addr
        msg['To'] = agent_email
        msg.attach(MIMEText(html, 'html', 'utf-8'))

        server = smtplib.SMTP(os.environ.get('SMTP_SERVER', 'smtp.gmail.com'), int(os.environ.get('SMTP_PORT', '587')))
        server.starttls()
        server.login(email_addr, email_pass)
        server.send_message(msg)
        server.quit()
        logger.info(f"Agent inquiry notification sent to {agent_email}")
    except Exception as e:
        logger.error(f"Agent inquiry notification failed: {e}")


'''

marker = '# ===== 이메일 발송 함수 ====='
if '_send_agent_inquiry_notification' not in c and marker in c:
    c = c.replace(marker, agent_notify_func + marker)
    print('[4] agent 알림 함수 추가 완료')
else:
    print('[4] 이미 존재하거나 마커 없음')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('완료')

path = '/home/webapp/goldenrabbit/backend/property-manager/services/airtable_service.py'
with open(path, 'r') as f:
    content = f.read()

old = """        # 번지 (bun-ji)
        bun = str(address_data.get('bun', '')).lstrip('0') or '0'
        ji = str(address_data.get('ji', '')).lstrip('0')"""

new = """        # 번지 (bun-ji) - PNU에서 fallback 추출
        bun = str(address_data.get('bun', '')).lstrip('0') or ''
        ji = str(address_data.get('ji', '')).lstrip('0')

        # bun이 없으면 PNU에서 추출 (11~14: 본번, 15~18: 부번)
        if not bun and address_data.get('pnu') and len(str(address_data['pnu'])) >= 19:
            pnu = str(address_data['pnu'])
            bun = pnu[11:15].lstrip('0') or '0'
            ji = pnu[15:19].lstrip('0')"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print('SUCCESS: PNU fallback added to _format_jibun_address')
else:
    print('ERROR: pattern not found')

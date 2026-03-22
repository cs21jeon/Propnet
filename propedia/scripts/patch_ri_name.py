path = '/home/webapp/goldenrabbit/backend/property-manager/services/airtable_service.py'
with open(path, 'r') as f:
    content = f.read()

old = """        # 리 (있는 경우만)
        if address_data.get('ri_name'):
            parts.append(address_data['ri_name'])"""

new = """        # 리 (있는 경우만)
        ri_name = address_data.get('ri_name')
        if not ri_name and address_data.get('full_address') and address_data.get('eupmyeondong_name'):
            # full_address에서 리 이름 추출 (예: "대구광역시 달성군 옥포읍 기세리" → "기세리")
            full = address_data['full_address']
            emd = address_data['eupmyeondong_name']
            idx = full.find(emd)
            if idx >= 0:
                after = full[idx + len(emd):].strip()
                # "기세리" 같은 리 이름이 있으면 추출 (리로 끝나는 단어)
                if after and (after.endswith('리') or after.endswith('동') or after.endswith('가')):
                    ri_name = after.split()[0] if after else None
        if ri_name:
            parts.append(ri_name)"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print('SUCCESS: ri_name extraction from full_address added')
else:
    print('ERROR: pattern not found')

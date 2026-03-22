path = '/home/webapp/goldenrabbit/frontend/public/app/result.html'
with open(path, 'r') as f:
    content = f.read()

old = """                const addressData = {
                    bjdong_code: currentData.address?.bjdong_code,
                    full_address: currentData.address?.full_address,
                    sido_name: currentData.address?.sido_name,
                    sigungu_name: currentData.address?.sigungu_name,
                    eupmyeondong_name: currentData.address?.eupmyeondong_name,
                    pnu: currentData.codes?.pnu,
                    sigungu_cd: currentData.codes?.sigungu_cd,
                    bjdong_cd: currentData.codes?.bjdong_cd
                };"""

new = """                const addressData = {
                    bjdong_code: currentData.address?.bjdong_code,
                    full_address: currentData.address?.full_address,
                    sido_name: currentData.address?.sido_name,
                    sigungu_name: currentData.address?.sigungu_name,
                    eupmyeondong_name: currentData.address?.eupmyeondong_name,
                    ri_name: currentData.address?.ri_name || null,
                    pnu: currentData.codes?.pnu,
                    sigungu_cd: currentData.codes?.sigungu_cd,
                    bjdong_cd: currentData.codes?.bjdong_cd,
                    bun: currentData.codes?.bun || null,
                    ji: currentData.codes?.ji || null,
                    land_type: currentData.codes?.land_type || null
                };"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print('SUCCESS: addressData fields patched with bun, ji, land_type, ri_name')
else:
    print('ERROR: pattern not found')

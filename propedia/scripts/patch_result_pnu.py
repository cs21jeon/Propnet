path = '/home/webapp/goldenrabbit/frontend/public/app/result.html'
with open(path, 'r') as f:
    content = f.read()

# Add PNU parameter parsing after existing URL params
old = """        const urlLat = urlParams.get('lat');  // 지도 검색에서 전달된 좌표
        const urlLng = urlParams.get('lng');"""

new = """        const urlLat = urlParams.get('lat');  // 지도 검색에서 전달된 좌표
        const urlLng = urlParams.get('lng');
        const urlPnu = urlParams.get('pnu');  // 즐겨찾기/검색기록에서 전달된 PNU"""

if old in content:
    content = content.replace(old, new)
    print('1. PNU param added')

# Add PNU-based search to loadData, before the 'throw' line
old_throw = """                } else {
                    throw new Error('검색 파라미터가 없습니다');
                }"""

new_throw = """                } else if (urlPnu && urlPnu.length === 19) {
                    // PNU에서 bjdong_code, bun, ji 추출 (즐겨찾기/검색기록)
                    const pnuBjdong = urlPnu.substring(0, 10);
                    const pnuLandType = urlPnu.substring(10, 11);
                    const pnuBun = urlPnu.substring(11, 15);
                    const pnuJi = urlPnu.substring(15, 19);
                    response = await fetch('/app/api/search/jibun', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ bjdong_code: pnuBjdong, bun: pnuBun, ji: pnuJi, land_type: pnuLandType })
                    });
                } else {
                    throw new Error('검색 파라미터가 없습니다');
                }"""

if old_throw in content:
    content = content.replace(old_throw, new_throw)
    print('2. PNU search logic added to loadData')

with open(path, 'w') as f:
    f.write(content)
print('DONE')

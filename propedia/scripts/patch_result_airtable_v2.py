path = '/home/webapp/goldenrabbit/frontend/public/app/result.html'
with open(path, 'r') as f:
    content = f.read()

# Replace the saveToAirtable function with building-type-aware version
old_fn = """        // Airtable에 저장
        async function saveToAirtable() {
            if (!currentData) return;
            const token = getAccessToken();
            if (!token) {
                showLoginPrompt('로그인 필요', '로그인하면 Airtable에 저장할 수 있습니다.');
                return;
            }

            const btn = document.getElementById('airtableButton');
            const icon = btn.querySelector('.material-symbols-outlined');
            const originalIcon = icon.textContent;
            icon.textContent = 'hourglass_empty';
            btn.disabled = true;

            try {
                const addressData = {
                    bjdong_code: currentData.address?.bjdong_code,
                    full_address: currentData.address?.full_address,
                    sido_name: currentData.address?.sido_name,
                    sigungu_name: currentData.address?.sigungu_name,
                    eupmyeondong_name: currentData.address?.eupmyeondong_name,
                    pnu: currentData.codes?.pnu,
                    sigungu_cd: currentData.codes?.sigungu_cd,
                    bjdong_cd: currentData.codes?.bjdong_cd
                };

                const buildingData = currentData.building ? {
                    has_data: currentData.building.has_data,
                    type: currentData.building.type,
                    building_info: currentData.building.building_info || null,
                    recap_title_info: currentData.building.recap_title_info || null
                } : null;

                const landData = currentData.land || null;

                let endpoint = '/app/api/airtable/save/building';
                let body = { address: addressData, building: buildingData, land: landData };

                // 공동주택이고 면적정보가 있으면 multi-unit
                if (currentData.building?.type === 'multi_unit' && selectedAreaInfo) {
                    endpoint = '/app/api/airtable/save/multi-unit';
                    body.area = selectedAreaInfo;
                }

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify(body)
                });

                const result = await response.json();
                if (result.success) {
                    icon.textContent = 'cloud_done';
                    icon.style.color = '#22c55e';
                    setTimeout(() => {
                        icon.textContent = originalIcon;
                        icon.style.color = '';
                    }, 3000);
                } else if (response.status === 403) {
                    alert('권한이 없습니다');
                    icon.textContent = originalIcon;
                } else {
                    alert(result.error || '저장 실패');
                    icon.textContent = originalIcon;
                }
            } catch (error) {
                console.error('Airtable save error:', error);
                alert('저장 중 오류가 발생했습니다');
                icon.textContent = originalIcon;
            } finally {
                btn.disabled = false;
            }
        }"""

new_fn = """        // Airtable 저장 버튼 상태 업데이트 (건물 유형에 따라)
        function updateAirtableButton() {
            const btn = document.getElementById('airtableButton');
            if (!btn || btn.classList.contains('hidden')) return;
            if (!currentData) return;

            const isMultiUnit = currentData.building?.type === 'multi_unit';
            const icon = btn.querySelector('.material-symbols-outlined');

            if (isMultiUnit) {
                btn.title = '공동주택매물 저장 (Airtable)';
                icon.textContent = 'apartment';
                // 공동주택은 동/호 선택 후에만 활성화
                if (!selectedAreaInfo) {
                    btn.style.opacity = '0.4';
                    btn.disabled = true;
                } else {
                    btn.style.opacity = '1';
                    btn.disabled = false;
                }
            } else {
                btn.title = '건물매물 저장 (Airtable)';
                icon.textContent = 'domain_add';
                btn.style.opacity = '1';
                btn.disabled = false;
            }
        }

        // Airtable에 저장
        async function saveToAirtable() {
            if (!currentData) return;
            const token = getAccessToken();
            if (!token) {
                showLoginPrompt('로그인 필요', '로그인하면 Airtable에 저장할 수 있습니다.');
                return;
            }

            const isMultiUnit = currentData.building?.type === 'multi_unit';

            // 공동주택인데 동/호 선택 안 했으면 안내
            if (isMultiUnit && !selectedAreaInfo) {
                alert('공동주택매물 저장을 위해 동/호를 먼저 선택해주세요.');
                return;
            }

            const saveType = isMultiUnit ? '공동주택매물' : '건물매물';
            if (!confirm(saveType + '로 Airtable에 저장하시겠습니까?')) return;

            const btn = document.getElementById('airtableButton');
            const icon = btn.querySelector('.material-symbols-outlined');
            const originalIcon = icon.textContent;
            icon.textContent = 'hourglass_empty';
            btn.disabled = true;

            try {
                const addressData = {
                    bjdong_code: currentData.address?.bjdong_code,
                    full_address: currentData.address?.full_address,
                    sido_name: currentData.address?.sido_name,
                    sigungu_name: currentData.address?.sigungu_name,
                    eupmyeondong_name: currentData.address?.eupmyeondong_name,
                    pnu: currentData.codes?.pnu,
                    sigungu_cd: currentData.codes?.sigungu_cd,
                    bjdong_cd: currentData.codes?.bjdong_cd
                };

                const buildingData = currentData.building ? {
                    has_data: currentData.building.has_data,
                    type: currentData.building.type,
                    building_info: currentData.building.building_info || null,
                    recap_title_info: currentData.building.recap_title_info || null
                } : null;

                const landData = currentData.land || null;

                let endpoint, body;

                if (isMultiUnit) {
                    endpoint = '/app/api/airtable/save/multi-unit';
                    body = { address: addressData, building: buildingData, area: selectedAreaInfo, land: landData };
                } else {
                    endpoint = '/app/api/airtable/save/building';
                    body = { address: addressData, building: buildingData, land: landData };
                }

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify(body)
                });

                const result = await response.json();
                if (result.success) {
                    icon.textContent = 'cloud_done';
                    icon.style.color = '#22c55e';
                    alert(saveType + ' 저장 완료!');
                    setTimeout(() => {
                        icon.textContent = originalIcon;
                        icon.style.color = '';
                    }, 3000);
                } else if (response.status === 403) {
                    alert('권한이 없습니다');
                    icon.textContent = originalIcon;
                } else {
                    alert(result.error || '저장 실패');
                    icon.textContent = originalIcon;
                }
            } catch (error) {
                console.error('Airtable save error:', error);
                alert('저장 중 오류가 발생했습니다');
                icon.textContent = originalIcon;
            } finally {
                btn.disabled = false;
                updateAirtableButton();
            }
        }"""

if old_fn in content:
    content = content.replace(old_fn, new_fn)
    print('SUCCESS: saveToAirtable replaced')
else:
    print('ERROR: old saveToAirtable not found')

# Add updateAirtableButton call when role check shows button
old_role_show = """                    if (userRole === 'admin' || userRole === 'editor') {
                        document.getElementById('airtableButton').classList.remove('hidden');
                    }"""
new_role_show = """                    if (userRole === 'admin' || userRole === 'editor') {
                        document.getElementById('airtableButton').classList.remove('hidden');
                        updateAirtableButton();
                    }"""
if old_role_show in content:
    content = content.replace(old_role_show, new_role_show)
    print('SUCCESS: role show patched')

# Add updateAirtableButton call when selectedAreaInfo is set
old_area = 'selectedAreaInfo = areaData;'
new_area = 'selectedAreaInfo = areaData;\n                        updateAirtableButton();'
count = content.count(old_area)
if count > 0:
    content = content.replace(old_area, new_area)
    print(f'SUCCESS: selectedAreaInfo patched ({count} occurrences)')
else:
    print('WARNING: selectedAreaInfo = areaData; not found')

with open(path, 'w') as f:
    f.write(content)
print('DONE')

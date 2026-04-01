#!/usr/bin/env python3
"""Patch index.html: Update openPropertyDetail to support 3 property types"""

FILE = '/home/webapp/goldenrabbit/frontend/public/index.html'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open(FILE + '.bak2', 'w', encoding='utf-8') as f:
    f.write(content)

# ===== PATCH 1: postMessage handler - pass dbId =====
old_msg = """        if (event.data && event.data.action === 'openPropertyDetail') {
            openPropertyDetail(event.data.recordId);"""

new_msg = """        if (event.data && event.data.action === 'openPropertyDetail') {
            openPropertyDetail(event.data.recordId, event.data.dbId);"""

if old_msg in content:
    content = content.replace(old_msg, new_msg)
    print("PATCH 1: postMessage handler updated")
else:
    print("WARN: postMessage handler not found")

# ===== PATCH 2: openPropertyDetail function - accept dbId + fetch with db_id =====
old_func_start = "    async function openPropertyDetail(recordId) {"
new_func_start = "    async function openPropertyDetail(recordId, dbId) {"

if old_func_start in content:
    content = content.replace(old_func_start, new_func_start)
    print("PATCH 2a: function signature updated")
else:
    print("WARN: function signature not found")

old_fetch = "            const response = await fetch('/propsheet/api/propsheet/property-detail?id=' + recordId);"
new_fetch = "            const response = await fetch('/propsheet/api/propsheet/property-detail?id=' + recordId + (dbId ? '&db_id=' + dbId : ''));"

if old_fetch in content:
    content = content.replace(old_fetch, new_fetch)
    print("PATCH 2b: fetch URL updated with db_id")
else:
    print("WARN: fetch URL not found")

# ===== PATCH 3: Detail modal content - support all 3 types =====
old_detail_body = """            // 상세 정보 행 생성
            let infoRows = '';
            if (p.investment) infoRows += infoRow('융자제외 실투자금', formatPrice(p.investment));
            if (p.yield_rate) infoRows += infoRow('수익률', parseFloat(p.yield_rate).toFixed(1) + '%');
            if (p.price && p.land_area) {
                const pyeong = p.land_area / 3.3058;
                const pricePerPyeong = Math.round(p.price / pyeong);
                infoRows += infoRow('평단가', pricePerPyeong.toLocaleString() + '만원/평');
            }"""

new_detail_body = """            // 유형 뱃지
            var typeNames = {danil: '단일', jibhap: '집합', bubun: '부분'};
            var typeColors = {danil: '#1D4ED8', jibhap: '#15803D', bubun: '#EA580C'};
            var propType = p.property_type || 'danil';
            var txnType = p.transaction_type || '매매';
            var typeBadge = '<span style="display:inline-block;font-size:11px;font-weight:600;padding:2px 8px;border-radius:4px;color:white;background:' + (typeColors[propType] || '#1D4ED8') + ';margin-bottom:6px;">' + (typeNames[propType] || '단일') + ' ' + txnType + '</span>';

            // 가격 표시 (유형별)
            var priceDisplay = '';
            if (txnType === '월세') {
                priceDisplay = '보증금 ' + formatPrice(p.deposit) + ' / 월세 ' + formatPrice(p.rent);
            } else if (txnType === '전세') {
                priceDisplay = '전세 ' + formatPrice(p.deposit);
            } else {
                priceDisplay = formatPrice(p.price);
            }

            // 상세 정보 행 생성
            let infoRows = '';
            if (propType === 'danil') {
                // 단일부동산: 기존 필드
                if (p.investment) infoRows += infoRow('융자제외 실투자금', formatPrice(p.investment));
                if (p.yield_rate) infoRows += infoRow('수익률', parseFloat(p.yield_rate).toFixed(1) + '%');
                if (p.price && p.land_area) {
                    const pyeong = p.land_area / 3.3058;
                    const pricePerPyeong = Math.round(p.price / pyeong);
                    infoRows += infoRow('평단가', pricePerPyeong.toLocaleString() + '만원/평');
                }
                if (p.land_area) infoRows += infoRow('토지면적', Math.round(p.land_area / 3.3058) + '평 (' + p.land_area + '㎡)');
                if (p.total_area) infoRows += infoRow('연면적', Math.round(p.total_area / 3.3058) + '평 (' + p.total_area + '㎡)');
            } else {
                // 집합/부분: 전세/월세 관련 필드
                if (txnType === '매매' && p.deposit) infoRows += infoRow('보증금', formatPrice(p.deposit));
                if (txnType === '매매' && p.rent) infoRows += infoRow('월세', formatPrice(p.rent));
                if (p.exclusive_area) infoRows += infoRow('전용면적', Math.round(p.exclusive_area / 3.3058) + '평 (' + p.exclusive_area + '㎡)');
                if (p.supply_area) infoRows += infoRow('공급면적', Math.round(p.supply_area / 3.3058) + '평 (' + p.supply_area + '㎡)');
                if (p.rooms) infoRows += infoRow('방/화장실', p.rooms + '방 / ' + (p.bathrooms || 0) + '화');
                if (p.maintenance_fee) infoRows += infoRow('관리비', formatPrice(p.maintenance_fee));
                if (p.move_in_date) infoRows += infoRow('입주가능일', p.move_in_date);
                if (p.property_subtype) infoRows += infoRow('물건종류', p.property_subtype);
                if (p.unit_no) infoRows += infoRow('호수', p.unit_no);
                if (p.land_area) infoRows += infoRow('토지면적', Math.round(p.land_area / 3.3058) + '평 (' + p.land_area + '㎡)');
            }
            // 공통 필드
            if (p.loan) infoRows += infoRow('융자', formatPrice(p.loan));"""

if old_detail_body in content:
    content = content.replace(old_detail_body, new_detail_body)
    print("PATCH 3: Detail info rows updated for 3 types")
else:
    print("WARN: Detail body not found")

# ===== PATCH 4: Replace price display and add type badge in modal HTML =====
old_modal_html = """                        '<p class="text-base text-slate-700 font-semibold">' + address + '</p>' +
                        '<p class="text-2xl font-bold text-primary mt-1">' + formatPrice(p.price) + '</p>' +"""

new_modal_html = """                        typeBadge +
                        '<p class="text-base text-slate-700 font-semibold">' + address + '</p>' +
                        '<p class="text-2xl font-bold text-primary mt-1">' + priceDisplay + '</p>' +"""

if old_modal_html in content:
    content = content.replace(old_modal_html, new_modal_html)
    print("PATCH 4: Modal HTML updated with type badge + dynamic price")
else:
    print("WARN: Modal HTML not found")

# ===== PATCH 5: card onclick in category properties - pass null for dbId =====
# This is for category properties (재건축, 고수익, 저가) which are all 단일
# No change needed - dbId will be undefined which defaults to 39

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: index.html detail view patched")

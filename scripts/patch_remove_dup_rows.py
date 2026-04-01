#!/usr/bin/env python3
"""Remove duplicate info rows from 집합/부분 detail views in both map.html and index.html"""

# ===== PATCH 1: index.html =====
FILE1 = '/home/webapp/goldenrabbit/frontend/public/index.html'
with open(FILE1, 'r', encoding='utf-8') as f:
    content1 = f.read()

old_index_rows = """            } else {
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
            }"""

new_index_rows = """            } else {
                // 집합/부분: 상세정보(광고자동완성)에 중복되는 필드 제외 — 가격 관련만 표시
                if (txnType === '매매' && p.deposit) infoRows += infoRow('보증금', formatPrice(p.deposit));
                if (txnType === '매매' && p.rent) infoRows += infoRow('월세', formatPrice(p.rent));
            }"""

if old_index_rows in content1:
    content1 = content1.replace(old_index_rows, new_index_rows)
    with open(FILE1, 'w', encoding='utf-8') as f:
        f.write(content1)
    print("PATCH 1: index.html - removed duplicate rows for 집합/부분")
else:
    print("WARN: index.html pattern not found")

# ===== PATCH 2: map.html =====
FILE2 = '/home/webapp/goldenrabbit/frontend/public/map.html'
with open(FILE2, 'r', encoding='utf-8') as f:
    content2 = f.read()

old_map_rows = """        } else {
            // 집합/부분
            if (data.exclusive_area > 0) addRow('전용면적', toPyeong(data.exclusive_area) + ' (' + data.exclusive_area + '㎡)');
            if (data.supply_area > 0) addRow('공급면적', toPyeong(data.supply_area) + ' (' + data.supply_area + '㎡)');
            if (data.rooms > 0) addRow('방/화장실', data.rooms + '방 / ' + (data.bathrooms || 0) + '화');
            if (data.maintenance_fee > 0) addRow('관리비', formatPrice(data.maintenance_fee));
            if (data.move_in_date) addRow('입주가능일', escapeHtml(data.move_in_date));
            if (data.property_subtype) addRow('물건종류', escapeHtml(data.property_subtype));
            if (data.unit_no) addRow('호수', escapeHtml(data.unit_no));
            if (data.land_area > 0) addRow('토지면적', toPyeong(data.land_area) + ' (' + data.land_area + '㎡)');
        }"""

new_map_rows = """        } else {
            // 집합/부분: 상세정보(광고자동완성)에 중복되는 필드 제외
        }"""

if old_map_rows in content2:
    content2 = content2.replace(old_map_rows, new_map_rows)
    with open(FILE2, 'w', encoding='utf-8') as f:
        f.write(content2)
    print("PATCH 2: map.html - removed duplicate rows for 집합/부분")
else:
    print("WARN: map.html pattern not found")

print("SUCCESS: Duplicate rows removed")

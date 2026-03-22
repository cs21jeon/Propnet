#!/usr/bin/env python3
"""Re-apply safe changes after revert (no renderTable, no timing)"""

# === 1. HTML fixes ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

# 1a. "전체 보기" → "필터 초기화"
html = html.replace(
    '<button class="btn" @click="resetFilters()">전체 보기</button>',
    '<button class="btn" @click="resetFilters()">필터 초기화</button>'
)
print("1. Renamed 전체보기 → 필터초기화")

# 1b. Add "전체" per_page option
if '전체</option>' not in html:
    html = html.replace(
        '<option value="100">100개씩</option>',
        '<option value="100">100개씩</option>\n                    <option value="9999">전체</option>'
    )
    print("2. Added 전체 per_page option")

with open(html_path, 'w') as f:
    f.write(html)

# === 2. CSS: widen column-manager ===
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
with open(css_path, 'r') as f:
    css = f.read()

if 'min-width: 280px' in css:
    css = css.replace('min-width: 280px;', 'min-width: 360px;')
    print("3. Widened column-manager")

if 'white-space: nowrap;' not in css.split('.column-manager-actions')[1].split('}')[0] if '.column-manager-actions' in css else '':
    css = css.replace(
        """.column-manager-actions {
    display: flex;
    gap: 6px;
}""",
        """.column-manager-actions {
    display: flex;
    gap: 6px;
    white-space: nowrap;
}"""
    )
    print("4. No-wrap column-manager buttons")

with open(css_path, 'w') as f:
    f.write(css)

# === 3. Backend: per_page limit ===
route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(route_path, 'r') as f:
    content = f.read()

if 'max: 100' in content or ', 100)' in content:
    content = content.replace(
        "per_page = min(request.args.get('per_page', 50, type=int), 100)",
        "per_page = min(request.args.get('per_page', 50, type=int), 10000)"
    )
    print("5. Raised per_page limit")

with open(route_path, 'w') as f:
    f.write(content)

print("Done!")

#!/usr/bin/env python3

# === 1. HTML: Change "전체 보기" button text to "필터 초기화" ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

html = html.replace(
    '<button class="btn" @click="resetFilters()">전체 보기</button>',
    '<button class="btn" @click="resetFilters()">필터 초기화</button>'
)
print("1. Changed '전체 보기' → '필터 초기화'")

with open(html_path, 'w') as f:
    f.write(html)

# === 2. CSS: Widen column-manager and prevent button text wrapping ===
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
with open(css_path, 'r') as f:
    css = f.read()

css = css.replace(
    "min-width: 280px;\n    max-height: 500px;",
    "min-width: 360px;\n    max-height: 500px;"
)

css = css.replace(
    """.column-manager-actions {
    display: flex;
    gap: 6px;
}""",
    """.column-manager-actions {
    display: flex;
    gap: 6px;
    white-space: nowrap;
    flex-shrink: 0;
}"""
)

# Also prevent button text wrapping
css = css.replace(
    """.btn-select-all, .btn-deselect-all {
    padding: 3px 8px;
    font-size: 11px;""",
    """.btn-select-all, .btn-deselect-all {
    padding: 3px 8px;
    font-size: 11px;
    white-space: nowrap;"""
)

print("2. Widened column-manager + no-wrap buttons")

with open(css_path, 'w') as f:
    f.write(css)

# === 3. Bump version ===
with open(html_path, 'rb') as f:
    raw = f.read()
raw = raw.replace(b'database_list.css?v=20260317', b'database_list.css?v=20260317t')
# Find current js version and bump
import re
raw_str = raw.decode('utf-8')
raw_str = re.sub(r'database_list\.css\?v=\w+', 'database_list.css?v=20260317t', raw_str)
with open(html_path, 'w') as f:
    f.write(raw_str)
print("3. Version bumped")

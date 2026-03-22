#!/usr/bin/env python3

# 1. HTML: Add "전체" option
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

html = html.replace(
    """<option value="25">25개씩</option>
                    <option value="50">50개씩</option>
                    <option value="100">100개씩</option>""",
    """<option value="25">25개씩</option>
                    <option value="50">50개씩</option>
                    <option value="100">100개씩</option>
                    <option value="9999">전체</option>"""
)
with open(html_path, 'w') as f:
    f.write(html)
print("1. HTML: Added 전체 option")

# 2. Backend: Raise per_page limit
route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(route_path, 'r') as f:
    content = f.read()

content = content.replace(
    "per_page = min(request.args.get('per_page', 50, type=int), 100)",
    "per_page = min(request.args.get('per_page', 50, type=int), 10000)"
)
with open(route_path, 'w') as f:
    f.write(content)
print("2. Backend: Raised per_page limit to 10000")

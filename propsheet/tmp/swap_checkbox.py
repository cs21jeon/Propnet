#!/usr/bin/env python3
"""Swap checkbox and expand columns: checkbox first, then expand"""
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()

# 1. Swap in thead (header row)
old_thead = '''<th style="width:30px;min-width:30px;max-width:30px;"></th>
                            <th style="width:32px;min-width:32px;max-width:32px;padding:0;text-align:center;position:sticky;left:36px;z-index:11;background:var(--surface,#fff);">
                                <input type="checkbox" @click="toggleAllRows()" :checked="selectedRows.length > 0 && selectedRows.length === items.length" style="cursor:pointer;">
                            </th>'''

new_thead = '''<th style="width:32px;min-width:32px;max-width:32px;padding:0;text-align:center;position:sticky;left:0;z-index:11;background:var(--surface,#fff);">
                                <input type="checkbox" @click="toggleAllRows()" :checked="selectedRows.length > 0 && selectedRows.length === items.length" style="cursor:pointer;">
                            </th>
                            <th style="width:30px;min-width:30px;max-width:30px;position:sticky;left:32px;z-index:11;background:var(--surface,#fff);"></th>'''

if old_thead in html:
    html = html.replace(old_thead, new_thead, 1)
    print("1. Swapped thead")

# 2. Swap in tbody (data rows)
old_tbody = '''<td class="cell-expand" @click.stop="openDetailPanel(item.id)" title="상세 보기" style="width:30px;min-width:30px;max-width:30px;text-align:center;cursor:pointer;color:var(--gray-400);">
                                    <span style="font-size:14px">▶</span>
                                </td>
                                <td class="cell-checkbox" @click.stop="toggleRowSelect($event, item.id)" style="width:32px;min-width:32px;max-width:32px;padding:0;text-align:center;">
                                    <input type="checkbox" :checked="selectedRows.includes(item.id)" @click.stop="toggleRowSelect($event, item.id)" style="cursor:pointer;">
                                </td>'''

new_tbody = '''<td class="cell-checkbox" @click.stop="toggleRowSelect($event, item.id)" style="width:32px;min-width:32px;max-width:32px;padding:0;text-align:center;">
                                    <input type="checkbox" :checked="selectedRows.includes(item.id)" @click.stop="toggleRowSelect($event, item.id)" style="cursor:pointer;">
                                </td>
                                <td class="cell-expand" @click.stop="openDetailPanel(item.id)" title="상세 보기" style="width:30px;min-width:30px;max-width:30px;text-align:center;cursor:pointer;color:var(--gray-400);">
                                    <span style="font-size:14px">▶</span>
                                </td>'''

if old_tbody in html:
    html = html.replace(old_tbody, new_tbody, 1)
    print("2. Swapped tbody")

with open(path, 'w') as f:
    f.write(html)

# 3. Update CSS: checkbox at left:0, expand at left:32px
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
with open(css_path, 'r') as f:
    css = f.read()

# Fix checkbox sticky position
css = css.replace(
    """.cell-checkbox {
    position: sticky;
    left: 36px;""",
    """.cell-checkbox {
    position: sticky;
    left: 0;"""
)

# Fix expand sticky position
css = css.replace(
    """.cell-expand {
    width: 36px;
    min-width: 36px;
    max-width: 36px;
    text-align: center;
    padding: 0 !important;
    position: sticky;
    left: 0;
    z-index: 2;""",
    """.cell-expand {
    width: 30px;
    min-width: 30px;
    max-width: 30px;
    text-align: center;
    padding: 0 !important;
    position: sticky;
    left: 32px;
    z-index: 2;"""
)

with open(css_path, 'w') as f:
    f.write(css)
print("3. Updated CSS positions")

print("Done!")

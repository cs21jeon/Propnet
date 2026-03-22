#!/usr/bin/env python3
# Add ⚙ settings button to detail panel field labels + CSS

html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

old = '<div class="detail-field-label" x-text="col.label"></div>'
new = '<div class="detail-field-label"><span x-text="col.label"></span><button class="detail-field-settings-btn" @click.stop="openFieldSettings(col)" title="필드 설정">&#9881;</button></div>'

if old in html:
    html = html.replace(old, new, 1)
    print("1. Added settings button to detail panel")

with open(html_path, 'w') as f:
    f.write(html)

# CSS
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
with open(css_path, 'r') as f:
    css = f.read()

if '.detail-field-settings-btn' not in css:
    css += """
/* Detail panel field settings button */
.detail-field-label {
    display: flex !important;
    align-items: center;
    gap: 4px;
}
.detail-field-settings-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 11px;
    color: var(--gray-300);
    padding: 0 2px;
    line-height: 1;
    opacity: 0;
    transition: opacity 0.15s, color 0.15s;
}
.detail-field-row:hover .detail-field-settings-btn {
    opacity: 1;
}
.detail-field-settings-btn:hover {
    color: var(--gray-600);
}
"""
    with open(css_path, 'w') as f:
        f.write(css)
    print("2. Added CSS")

print("Done")

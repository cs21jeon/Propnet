#!/usr/bin/env python3
"""Fix detail panel to show newlines as <br> in text fields"""
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()

# Fix the broken line from sed attempt - find and replace
old = '<span x-show="!isUrlValue(col.key)" x-text="getDetailDisplayValue(col.key)"></span>'
new = """<span x-show="!isUrlValue(col.key)" style="white-space:pre-line;" x-text="getDetailDisplayValue(col.key)"></span>"""

if old in html:
    html = html.replace(old, new, 1)
    print("1. Added white-space:pre-line to detail value span")
else:
    # The sed may have broken it - fix by finding partial match
    import re
    # Find the broken line
    pattern = r'<span x-show="!isUrlValue\(col\.key\)"[^>]*>.*?getDetailDisplayValue.*?$'
    match = re.search(pattern, html, re.MULTILINE)
    if match:
        broken = match.group(0)
        print(f"   Found broken: {broken[:80]}...")
        # Replace the whole broken span
        html = html.replace(broken, new)
        print("1. Fixed broken line and added white-space:pre-line")
    else:
        print("1. WARN: could not find the span")

with open(path, 'w') as f:
    f.write(html)

print("Done!")

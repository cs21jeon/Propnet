#!/usr/bin/env python3
"""Fix the broken detail panel span - replace with white-space:pre-line approach"""
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()

# The broken content spans multiple lines due to sed error
broken = """<span x-show="!isUrlValue(col.key)" x-html="getDetailDisplayValue(col.key).replace(/\n/g, '<br>').replace(/\n/g, '<br>')"></span>"""

fixed = """<span x-show="!isUrlValue(col.key)" style="white-space:pre-line;" x-text="getDetailDisplayValue(col.key)"></span>"""

if broken in html:
    html = html.replace(broken, fixed, 1)
    print("1. Fixed broken span with white-space:pre-line")
else:
    # Try to find it with the actual newlines
    import re
    pattern = r'<span x-show="!isUrlValue\(col\.key\)"[^>]*x-html="getDetailDisplayValue[^"]*"[^>]*></span>'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        html = html.replace(match.group(0), fixed, 1)
        print(f"1. Replaced via regex: {repr(match.group(0)[:60])}...")
    else:
        # Try matching the multiline broken version
        lines = html.split('\n')
        for i, line in enumerate(lines):
            if 'getDetailDisplayValue(col.key).replace(/' in line:
                # This line and next lines are broken - find the closing </span>
                j = i + 1
                while j < len(lines) and '</span>' not in lines[j]:
                    j += 1
                # Replace lines i through j with the fixed version
                indent = '                                                '
                lines[i:j+1] = [indent + fixed]
                html = '\n'.join(lines)
                print(f"1. Fixed broken lines {i+1}-{j+1} with white-space:pre-line")
                break
        else:
            print("1. WARN: could not find broken span")

with open(path, 'w') as f:
    f.write(html)

print("Done!")

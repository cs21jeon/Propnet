#!/usr/bin/env python3
"""Fix unterminated string literal in propnet_api.py"""

FILE = '/home/webapp/goldenrabbit/backend/property-manager/routes/propnet_api.py'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

old_line = "        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
new_block = """        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        import re as _re_mod
        email_valid = bool(_re_mod.match(email_pattern, email))"""

if old_line in content:
    content = content.replace(old_line, new_block)
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("FIXED: propnet_api.py line 274")
else:
    print("NOT FOUND - checking content around line 274...")
    lines = content.split('\n')
    for i in range(272, min(278, len(lines))):
        print(f"  {i+1}: {repr(lines[i])}")

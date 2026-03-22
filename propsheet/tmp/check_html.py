#!/usr/bin/env python3
"""Check HTML template for syntax issues"""
with open('/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html') as f:
    html = f.read()

issues = []
for i, line in enumerate(html.split('\n'), 1):
    stripped = line.strip()
    # Check Alpine directives for quote issues
    for directive in ['x-html=', 'x-text=', ':class=', ':style=', '@click=']:
        if directive in stripped:
            # Find the directive value
            idx = stripped.index(directive) + len(directive)
            if idx < len(stripped) and stripped[idx] == '"':
                # Count remaining quotes from this point
                rest = stripped[idx:]
                dq = rest.count('"')
                if dq % 2 != 0:
                    issues.append(f'Line {i}: odd quotes in {directive} -> {stripped[:80]}')

    # Check for _getCachedCell usage
    if '_getCachedCell' in stripped:
        print(f'Line {i}: _getCachedCell found -> {stripped[:80]}')

    # Check for _cellClass usage
    if '_cellClass' in stripped:
        print(f'Line {i}: _cellClass found -> {stripped[:80]}')

if issues:
    print('\n=== ISSUES ===')
    for iss in issues:
        print(iss)
else:
    print('\nNo quote issues found')

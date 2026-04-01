#!/usr/bin/env python3
"""Patch propsheet.py: All 3 endpoints (map-data, search-map, property-detail)"""
import re
import sys
import textwrap

FILE = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open(FILE + '.bak2', 'w', encoding='utf-8') as f:
    f.write(content)

# ===== PATCH 1: map-data =====
old_map = r"@bp\.route\('/api/propsheet/map-data'.*?return jsonify\(\{'success': True, 'markers': markers, 'total': len\(markers\), 'agent': agent\}\)"
match = re.search(old_map, content, re.DOTALL)
if not match:
    print("ERROR: map-data not found")
    sys.exit(1)

# Read the new map-data code from file
MAP_DATA_CODE = open('/tmp/new_map_data.py', 'r').read()
content = content[:match.start()] + MAP_DATA_CODE + content[match.end():]
print(f"PATCH 1: map-data replaced")

# ===== PATCH 2: search-map =====
old_search = r"@bp\.route\('/api/propsheet/search-map', methods=\['POST'\]\)\ndef search_map_db\(\):.*?return jsonify\(\{\s*'map_html': map_html,\s*'markers': markers,\s*'count': len\(markers\),\s*'statistics':.*?\}\s*\)"
match = re.search(old_search, content, re.DOTALL)
if not match:
    print("ERROR: search-map not found")
    sys.exit(1)

SEARCH_CODE = open('/tmp/new_search_map.py', 'r').read()
content = content[:match.start()] + SEARCH_CODE + content[match.end():]
print(f"PATCH 2: search-map replaced")

# ===== PATCH 3: property-detail =====
old_detail = r"@bp\.route\('/api/propsheet/property-detail'.*?return jsonify\(\{'error': str\(e\)\}\), 500"
match = re.search(old_detail, content, re.DOTALL)
if not match:
    print("ERROR: property-detail not found")
    sys.exit(1)

DETAIL_CODE = open('/tmp/new_property_detail.py', 'r').read()
content = content[:match.start()] + DETAIL_CODE + content[match.end():]
print(f"PATCH 3: property-detail replaced")

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

# Verify syntax
import py_compile
try:
    py_compile.compile(FILE, doraise=True)
    print("SYNTAX CHECK: OK")
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
    # Restore
    import shutil
    shutil.copy(FILE + '.bak2', FILE)
    print("Restored from backup")
    sys.exit(1)

print("SUCCESS: All 3 endpoints patched")

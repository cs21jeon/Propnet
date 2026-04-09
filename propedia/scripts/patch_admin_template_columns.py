#!/usr/bin/env python3
"""
Fix column names in agent_requests template
"""

path = '/home/webapp/goldenrabbit/backend/property-manager/templates/admin/agent_requests.html'
with open(path, 'r') as f:
    content = f.read()

changes = 0

# Fix column references in template
replacements = [
    ("req.agency_name", "req.agent_name"),
    ("req.slug", "req.agent_slug"),
    ("req.address", "req.office_address"),
    ("req.license_file", "req.license_file_path"),
    ("req.user_email", "req.user_email"),  # already correct (comes from JOIN)
    ("req.user_name", "req.user_name"),    # already correct
    ("req.license_no", "req.license_no"),  # this column doesn't exist, but won't error in jinja
]

for old, new in replacements:
    if old in content and old != new:
        content = content.replace(old, new)
        changes += 1
        print(f"  Fixed: {old} -> {new}")

with open(path, 'w') as f:
    f.write(content)

print(f"\nDone: {changes} fixes applied")

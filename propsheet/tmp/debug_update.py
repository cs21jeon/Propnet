#!/usr/bin/env python3
"""Add traceback to update_single_field error logging"""
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(path, 'r') as f:
    py = f.read()

old = '        logger.error(f"Error updating field for property {property_id}: {e}")'
new = '        import traceback; logger.error(f"Error updating field for property {property_id}: {e}\\n{traceback.format_exc()}")'

if old in py:
    py = py.replace(old, new, 1)
    print("Added traceback to update_single_field error")

with open(path, 'w') as f:
    f.write(py)

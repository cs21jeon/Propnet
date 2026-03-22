#!/usr/bin/env python3
"""Add sync event to create_new_property"""
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(path, 'r') as f:
    py = f.read()

# Add sync event after conn.commit() in create_new_property
old = """                new_id = result['id'] if isinstance(result, dict) else result[0]
                conn.commit()

                msg = '레코드가 복제되었습니다' if source_id else '새 레코드가 생성되었습니다'"""

new = """                new_id = result['id'] if isinstance(result, dict) else result[0]
                _log_sync_event(cursor, 'record_add', database_id=database_id, record_id=new_id)
                conn.commit()

                msg = '레코드가 복제되었습니다' if source_id else '새 레코드가 생성되었습니다'"""

if old in py and "sync_event.*record_add" not in py:
    py = py.replace(old, new, 1)
    print("Added sync event to create_new_property")
else:
    print("SKIP or already exists")

with open(path, 'w') as f:
    f.write(py)

#!/usr/bin/env python3
"""delete_column에서 field_definitions도 함께 삭제하도록 수정"""

path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old = """                # Drop column from table
                cursor.execute(f'''
                    ALTER TABLE "{db_info['table_name']}"
                    DROP COLUMN "{column_name}"
                ''')
                _log_sync_event(cursor, 'field_delete', database_id=database_id, field_name=column_name)"""

new = """                # Drop column from table
                cursor.execute(f'''
                    ALTER TABLE "{db_info['table_name']}"
                    DROP COLUMN "{column_name}"
                ''')
                # field_definitions에서도 삭제
                cursor.execute(
                    "DELETE FROM field_definitions WHERE database_id = %s AND field_name = %s",
                    (database_id, column_name)
                )
                _log_sync_event(cursor, 'field_delete', database_id=database_id, field_name=column_name)"""

if old in c:
    c = c.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('버그 수정 완료')
else:
    print('패턴 불일치')

#!/usr/bin/env python3
"""
Fix clone: after table clone, remove all column defaults + apply map trigger.
This ensures new workspaces/databases work identically.
"""
path = '/home/webapp/goldenrabbit/backend/property-manager/services/workspace_service.py'
with open(path, 'r') as f:
    content = f.read()

# Add cleanup after clone_database_table_impl in clone_database_full
old = '                clone_database_views_impl(cursor, source_db_id, target_db_id)'
new = '''                clone_database_views_impl(cursor, source_db_id, target_db_id)

                # Remove inherited column defaults (prevent auto-fill on new records)
                cursor.execute("""
                    SELECT column_name, column_default FROM information_schema.columns
                    WHERE table_name = %s AND column_default IS NOT NULL
                    AND column_name NOT IN ('id', 'created_at', 'updated_at')
                """, (target_table,))
                defaults_to_drop = [r['column_name'] if isinstance(r, dict) else r[0] for r in cursor.fetchall()]
                for col in defaults_to_drop:
                    try:
                        cursor.execute(psql.SQL('ALTER TABLE {} ALTER COLUMN {} DROP DEFAULT').format(
                            psql.Identifier(target_table), psql.Identifier(col)))
                    except:
                        pass
                if defaults_to_drop:
                    logger.info(f"Dropped {len(defaults_to_drop)} column defaults from '{target_table}'")

                # Apply map link trigger if 지도 and 지번 주소 columns exist
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = %s AND column_name IN ('지도', '지번 주소')
                """, (target_table,))
                map_cols = {r['column_name'] if isinstance(r, dict) else r[0] for r in cursor.fetchall()}
                if '지도' in map_cols and '지번 주소' in map_cols:
                    trigger_name = f'trigger_map_{target_table[:30]}'
                    cursor.execute(psql.SQL('DROP TRIGGER IF EXISTS {} ON {}').format(
                        psql.Identifier(trigger_name), psql.Identifier(target_table)))
                    cursor.execute(psql.SQL("""
                        CREATE TRIGGER {} BEFORE INSERT OR UPDATE ON {}
                        FOR EACH ROW EXECUTE FUNCTION update_map_link()
                    """).format(psql.Identifier(trigger_name), psql.Identifier(target_table)))
                    logger.info(f"Created map trigger on '{target_table}'")'''

if 'Remove inherited column defaults' not in content:
    content = content.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(content)
    print("OK - Added defaults cleanup + map trigger to clone_database_full")
else:
    print("Already has")

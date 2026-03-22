#!/usr/bin/env python3
"""
워크스페이스 복제 안정화 - Steps 1~5 통합 구현
1. clone_database_views() JSONB 수정
2. 단일 트랜잭션 clone_database_full()
3. 시퀀스 리셋
4. api_clone_workspace() 강화
5. 고아 메타데이터 정리 유틸
"""
import re

ws_path = '/home/webapp/goldenrabbit/backend/property-manager/services/workspace_service.py'
route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'

# ============================================================
# STEP 1-3: Rewrite clone functions in workspace_service.py
# ============================================================

with open(ws_path, 'r') as f:
    ws = f.read()

# Find and replace both clone functions + add clone_database_full + find_orphaned_databases
# Locate the start of clone_database_table
clone_start = ws.index('def clone_database_table(')
# Find the next top-level function after clone_database_views
# Look for the next "def " at the start of a line after clone_database_views
after_views = ws.index('def clone_database_views(')
# Find end - next function definition at module level
remaining = ws[after_views:]
lines = remaining.split('\n')
end_offset = 0
found_end = False
for i, line in enumerate(lines):
    if i > 0 and line.startswith('def ') or (i > 0 and line.startswith('class ')):
        end_offset = sum(len(l) + 1 for l in lines[:i])
        found_end = True
        break
if not found_end:
    end_offset = len(remaining)

clone_end = after_views + end_offset

new_clone_code = '''def clone_database_table_impl(cursor, source_table, target_table, source_db_id, target_db_id):
    """Clone table structure + data using an existing cursor (no commit)"""
    # Create table with identical structure
    cursor.execute(f'CREATE TABLE "{target_table}" (LIKE "{source_table}" INCLUDING DEFAULTS)')

    # Remove inherited FK constraints
    cursor.execute(f"""
        SELECT conname FROM pg_constraint
        WHERE conrelid = '"{target_table}"'::regclass AND contype = 'f'
    """)
    for row in cursor.fetchall():
        con = row[0] if isinstance(row, tuple) else row['conname']
        cursor.execute(f'ALTER TABLE "{target_table}" DROP CONSTRAINT IF EXISTS "{con}"')

    # Create new sequence for id column
    cursor.execute(f"""
        SELECT column_default FROM information_schema.columns
        WHERE table_name = '{target_table}' AND column_name = 'id'
    """)
    col_default = cursor.fetchone()
    default_val = col_default[0] if isinstance(col_default, tuple) else (col_default.get('column_default') if col_default else None)
    if default_val and 'nextval' in str(default_val):
        cursor.execute(f"""
            CREATE SEQUENCE IF NOT EXISTS "{target_table}_id_seq";
            ALTER TABLE "{target_table}" ALTER COLUMN id SET DEFAULT nextval('"{target_table}_id_seq"');
            ALTER SEQUENCE "{target_table}_id_seq" OWNED BY "{target_table}".id;
        """)

    # Get column names (except id)
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s AND column_name != 'id'
        ORDER BY ordinal_position
    """, (source_table,))
    all_cols = [r[0] if isinstance(r, tuple) else r['column_name'] for r in cursor.fetchall()]

    if not all_cols:
        raise ValueError(f"Source table '{source_table}' has no columns")

    # Escape % in column names for psycopg2
    def esc(name):
        return '"' + name.replace('%', '%%') + '"'

    cols_escaped = ', '.join(esc(c) for c in all_cols)
    select_parts = []
    for c in all_cols:
        if c == 'database_id':
            select_parts.append('%%s')
        else:
            select_parts.append(esc(c))
    select_escaped = ', '.join(select_parts)

    copy_sql = f'INSERT INTO "{target_table}" ({cols_escaped}) SELECT {select_escaped} FROM "{source_table}"'
    cursor.execute(copy_sql, (target_db_id,))
    row_count = cursor.rowcount

    # Reset sequence to max(id) + 1
    cursor.execute(f"""
        SELECT setval('"{target_table}_id_seq"',
            COALESCE((SELECT MAX(id) FROM "{target_table}"), 0) + 1, false)
    """)

    logger.info(f"Cloned table '{source_table}' -> '{target_table}' ({row_count} rows)")
    return row_count


def clone_database_views_impl(cursor, source_db_id, target_db_id):
    """Clone views using an existing cursor (no commit). Handles JSONB with Json()."""
    from psycopg2.extras import Json

    cursor.execute("""
        SELECT name, slug, filter_config, sort_config, column_config,
               display_order, is_default
        FROM views WHERE database_id = %s
        ORDER BY display_order
    """, (source_db_id,))
    views = cursor.fetchall()

    cloned = 0
    for view in views:
        # Handle both tuple and dict cursor results
        if isinstance(view, tuple):
            name, slug, fc, sc, cc, order, is_def = view
        else:
            name = view['name']
            slug = view['slug']
            fc = view['filter_config']
            sc = view['sort_config']
            cc = view['column_config']
            order = view['display_order']
            is_def = view['is_default']

        cursor.execute("""
            INSERT INTO views (database_id, name, slug, filter_config,
                               sort_config, column_config, display_order, is_default)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            target_db_id, name, slug,
            Json(fc) if fc is not None else None,
            Json(sc) if sc is not None else None,
            Json(cc) if cc is not None else None,
            order, is_def
        ))
        cloned += 1

    logger.info(f"Cloned {cloned} views from db {source_db_id} -> {target_db_id}")
    return cloned


def clone_database_full(source_table, target_table, source_db_id, target_db_id):
    """Atomic clone: table + data + sequence + views in a single transaction"""
    from psycopg2.extras import RealDictCursor
    with get_db_connection() as conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                clone_database_table_impl(cursor, source_table, target_table, source_db_id, target_db_id)
                clone_database_views_impl(cursor, source_db_id, target_db_id)

            conn.commit()

            # Post-clone validation
            with conn.cursor() as verify:
                verify.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)", (target_table,))
                if not verify.fetchone()[0]:
                    raise RuntimeError(f"Post-clone validation failed: table '{target_table}' not found")
                verify.execute(f'SELECT COUNT(*) FROM "{target_table}"')
                count = verify.fetchone()[0]
                logger.info(f"Clone validated: '{target_table}' has {count} rows")

        except Exception as e:
            conn.rollback()
            # Clean up: drop table if partially created
            try:
                with conn.cursor() as cleanup:
                    cleanup.execute(f'DROP TABLE IF EXISTS "{target_table}" CASCADE')
                conn.commit()
            except:
                pass
            logger.error(f"Clone failed and rolled back: {source_table} -> {target_table}: {e}")
            raise


def find_orphaned_databases(cleanup=False):
    """Find databases entries where the actual table doesn't exist"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT d.id, d.name, d.table_name, d.workspace_id
                FROM databases d
                WHERE NOT EXISTS (
                    SELECT 1 FROM information_schema.tables t
                    WHERE t.table_name = d.table_name AND t.table_schema = 'public'
                )
            """)
            orphans = cursor.fetchall()

            if cleanup and orphans:
                for orphan in orphans:
                    oid = orphan[0] if isinstance(orphan, tuple) else orphan['id']
                    cursor.execute("DELETE FROM views WHERE database_id = %s", (oid,))
                    cursor.execute("DELETE FROM database_shares WHERE database_id = %s", (oid,))
                    cursor.execute("DELETE FROM databases WHERE id = %s", (oid,))
                conn.commit()
                logger.info(f"Cleaned up {len(orphans)} orphaned database records")

            return orphans


# Keep old function names as wrappers for backward compatibility
def clone_database_table(source_table, target_table, source_db_id, target_db_id):
    """Legacy wrapper - use clone_database_full() for atomic operations"""
    clone_database_full(source_table, target_table, source_db_id, target_db_id)


def clone_database_views(source_db_id, target_db_id):
    """Legacy wrapper - views are now cloned inside clone_database_full()"""
    pass  # No-op: views are cloned atomically inside clone_database_full


'''

ws_new = ws[:clone_start] + new_clone_code + ws[clone_end:]

with open(ws_path, 'w') as f:
    f.write(ws_new)
print("Steps 1-3,5: Rewrote clone functions in workspace_service.py")

# ============================================================
# STEP 4: Update api_clone_workspace in routes/propsheet.py
# ============================================================

with open(route_path, 'r') as f:
    route = f.read()

# Ensure clone_database_full is imported
if 'clone_database_full' not in route:
    route = route.replace(
        'from services.workspace_service import',
        'from services.workspace_service import clone_database_full, find_orphaned_databases,',
        1
    )
    print("Step 4a: Added imports")

# Replace the clone loop in api_clone_workspace
old_loop = """        results = {'cloned': [], 'failed': []}
        for db in databases:
            import secrets as _s
            import string as _str
            db_suffix = ''.join(_s.choice(_str.ascii_lowercase + _str.digits) for _ in range(4))
            new_db_slug = db['slug'] + '_' + db_suffix
            new_table_name = new_db_slug.replace('-', '_')

            try:
                new_db_id = create_database(
                    workspace_id=new_ws_id, name=db['name'], slug=new_db_slug,
                    table_name=new_table_name, description=db.get('description', ''),
                    icon=db.get('icon', '📊'), color=db.get('color', '#667eea'))

                clone_database_table(
                    source_table=db['table_name'], target_table=new_table_name,
                    source_db_id=db['id'], target_db_id=new_db_id)
                clone_database_views(db['id'], new_db_id)
                results['cloned'].append(db['name'])
            except Exception as clone_err:
                logger.warning(f"Failed to clone DB '{db['name']}': {clone_err}")
                results['failed'].append({'name': db['name'], 'error': str(clone_err)})
                # Cleanup: remove metadata entry and drop table if it was created
                try:
                    delete_database(new_db_id)
                except:
                    pass
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(f'DROP TABLE IF EXISTS "{new_table_name}"')
                        conn.commit()
                except:
                    pass"""

if old_loop not in route:
    # Try the older version
    old_loop = """        cloned_count = 0
        for db in databases:
            import secrets as _s
            import string as _str
            db_suffix = ''.join(_s.choice(_str.ascii_lowercase + _str.digits) for _ in range(4))
            new_db_slug = db['slug'] + '_' + db_suffix
            new_table_name = new_db_slug.replace('-', '_')

            new_db_id = create_database(
                workspace_id=new_ws_id,
                name=db['name'],
                slug=new_db_slug,
                table_name=new_table_name,
                description=db.get('description', ''),
                icon=db.get('icon', '📊'),
                color=db.get('color', '#667eea')
            )

            try:
                clone_database_table(
                    source_table=db['table_name'],
                    target_table=new_table_name,
                    source_db_id=db['id'],
                    target_db_id=new_db_id
                )
                clone_database_views(db['id'], new_db_id)
                cloned_count += 1
            except Exception as clone_err:
                logger.warning(f"Skipped cloning DB '{db['name']}': {clone_err}")
                # Clean up the empty database entry
                try:
                    from services.workspace_service import delete_database
                    delete_database(new_db_id)
                except:
                    pass"""

new_loop = """        # Clean orphaned records first
        find_orphaned_databases(cleanup=True)

        results = {'cloned': [], 'failed': []}
        for db in databases:
            import secrets as _s
            import string as _str
            db_suffix = ''.join(_s.choice(_str.ascii_lowercase + _str.digits) for _ in range(4))
            new_db_slug = db['slug'] + '_' + db_suffix
            new_table_name = new_db_slug.replace('-', '_')
            new_db_id = None

            try:
                new_db_id = create_database(
                    workspace_id=new_ws_id, name=db['name'], slug=new_db_slug,
                    table_name=new_table_name, description=db.get('description', ''),
                    icon=db.get('icon', '📊'), color=db.get('color', '#667eea'))

                clone_database_full(
                    source_table=db['table_name'], target_table=new_table_name,
                    source_db_id=db['id'], target_db_id=new_db_id)
                results['cloned'].append(db['name'])

            except Exception as clone_err:
                logger.warning(f"Failed to clone DB '{db['name']}': {clone_err}")
                results['failed'].append(db['name'])
                # Cleanup: metadata + table
                if new_db_id:
                    try:
                        from services.workspace_service import delete_database
                        delete_database(new_db_id)
                    except:
                        pass"""

if old_loop in route:
    route = route.replace(old_loop, new_loop, 1)
    print("Step 4b: Replaced clone loop")
else:
    print("Step 4b: WARN - could not find clone loop pattern")

# Fix the return to use results dict
old_return = """        logger.info(f"Cloned workspace '{slug}' -> '{new_slug}' ({cloned_count} databases)")
        return jsonify({
            'success': True,
            'slug': new_slug,
            'databases_cloned': cloned_count
        })"""

new_return = """        cloned_count = len(results['cloned'])
        logger.info(f"Cloned workspace '{slug}' -> '{new_slug}' ({cloned_count} databases)")
        return jsonify({
            'success': True,
            'slug': new_slug,
            'databases_cloned': cloned_count,
            'databases_failed': len(results['failed']),
            'details': results
        })"""

if old_return in route:
    route = route.replace(old_return, new_return, 1)
    print("Step 4c: Updated return")

with open(route_path, 'w') as f:
    f.write(route)

print("\nAll steps complete!")

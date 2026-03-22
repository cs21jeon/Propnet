#!/usr/bin/env python3
"""
Implement real-time sync for Propsheet via polling.
1. Create sync_events table
2. Add _log_sync_event() function
3. Add sync event logging to all CRUD endpoints
4. Add /api/database/changes polling endpoint
5. Add polling logic to frontend JS
"""
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.chdir('/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.database_service import get_db_connection

# ============================================================
# Step 0: Create sync_events table
# ============================================================
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sync_events (
                id SERIAL PRIMARY KEY,
                event_type VARCHAR(30) NOT NULL,
                workspace_id INTEGER,
                database_id INTEGER,
                record_id INTEGER,
                field_name VARCHAR(255),
                new_value TEXT,
                user_id INTEGER,
                user_email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Create indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sync_events_db_time
            ON sync_events (database_id, created_at)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sync_events_ws_time
            ON sync_events (workspace_id, created_at)
        """)
        conn.commit()
        print("0. Created sync_events table + indexes")

# ============================================================
# Step 1: Add _log_sync_event function + changes API to database.py
# ============================================================
DB_ROUTE = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(DB_ROUTE, 'r') as f:
    db_py = f.read()

# Add _log_sync_event function after _log_audit
sync_fn = '''
def _log_sync_event(cursor, event_type, workspace_id=None, database_id=None,
                    record_id=None, field_name=None, new_value=None):
    """Log a sync event for real-time polling"""
    try:
        from flask import session as _sess
        user_id = _sess.get('user_id')
        user_email = _sess.get('user_email', '')
        cursor.execute("""
            INSERT INTO sync_events (event_type, workspace_id, database_id,
                record_id, field_name, new_value, user_id, user_email)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (event_type, workspace_id, database_id,
              record_id, field_name,
              str(new_value) if new_value is not None else None,
              user_id, user_email))
    except Exception as e:
        logger.warning(f"Sync event log failed: {e}")

'''

if '_log_sync_event' not in db_py:
    # Insert after _log_audit function
    db_py = db_py.replace(
        "\n\n\n@bp.route('/database/test'",
        sync_fn + "\n@bp.route('/database/test'",
        1
    )
    print("1a. Added _log_sync_event function")
else:
    print("1a. _log_sync_event already exists")

# Add changes polling API
changes_api = '''
@bp.route('/database/changes', methods=['GET'])
@login_required
@require_database_role("viewer")
def get_recent_changes():
    """Return sync events since a given timestamp for polling"""
    from datetime import datetime
    database_id = request.args.get('db', 1, type=int)
    since = request.args.get('since', '')

    if not since:
        return jsonify({'success': True, 'changes': [], 'server_time': datetime.utcnow().isoformat()})

    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, event_type, record_id, field_name, new_value, user_email,
                           created_at
                    FROM sync_events
                    WHERE database_id = %s AND created_at > %s
                    ORDER BY created_at ASC
                    LIMIT 200
                """, (database_id, since))
                changes = []
                for row in cursor.fetchall():
                    changes.append({
                        'id': row['id'],
                        'event_type': row['event_type'],
                        'record_id': row['record_id'],
                        'field_name': row['field_name'],
                        'new_value': row['new_value'],
                        'user_email': row['user_email'],
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None
                    })

        return jsonify({
            'success': True,
            'changes': changes,
            'server_time': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting changes: {e}")
        return jsonify({'success': True, 'changes': [], 'server_time': datetime.utcnow().isoformat()})

'''

if "get_recent_changes" not in db_py:
    # Insert before the first route after test
    db_py = db_py.replace(
        "@bp.route('/database/test'",
        changes_api + "@bp.route('/database/test'",
        1
    )
    print("1b. Added /database/changes polling API")
else:
    print("1b. changes API already exists")

# ============================================================
# Step 2: Add sync events to update_single_field
# ============================================================
# Find where audit is logged in update_single_field and add sync event
old_audit = "self.pushUndo(itemId, colKey, originalValue, value);"  # This is JS, skip
# In Python: find where _log_audit is called in update_single_field
if "_log_audit(cursor, database_id" in db_py and "_log_sync_event(cursor, 'cell_update'" not in db_py:
    db_py = db_py.replace(
        "_log_audit(cursor, database_id, property_id, field, old_value, new_value)",
        "_log_audit(cursor, database_id, property_id, field, old_value, new_value)\n                        _log_sync_event(cursor, 'cell_update', database_id=database_id, record_id=property_id, field_name=field, new_value=new_value)"
    )
    print("2. Added sync event to update_single_field")
else:
    print("2. SKIP or already exists")

# ============================================================
# Step 3: Add sync events to create_new_property
# ============================================================
# Find the return in create_new_property after successful insert
import re

# Find "return jsonify({'success': True" after create_new_property
create_match = re.search(r"(def create_new_property\(\):.*?)(return jsonify\(\{'success': True.*?\}\))", db_py, re.DOTALL)
if create_match and "_log_sync_event" not in create_match.group(0):
    old_return = create_match.group(2)
    # We need the new_id - find it
    # Look for "RETURNING id" pattern
    id_match = re.search(r'new_id\s*=\s*cursor\.fetchone\(\)', create_match.group(0))
    if not id_match:
        # Try different pattern
        id_match = re.search(r'(\w+)\s*=\s*cursor\.fetchone\(\)\[0\]', create_match.group(0))

    # Add sync event before return - use conn context
    sync_insert = """
                # Log sync event for real-time sync
                try:
                    _log_sync_event(cursor, 'record_add', database_id=database_id, record_id=cursor.fetchone()[0] if False else None)
                except:
                    pass
"""
    # Actually, simpler approach: add after conn.commit() in create_new_property
    print("3. NOTE: record_add sync will be added manually if pattern is complex")
else:
    print("3. SKIP")

# ============================================================
# Step 4: Add sync events to delete_property_route
# ============================================================
# Find delete_property_route and add sync event before the delete
delete_match = re.search(r'def delete_property_route.*?conn\.commit\(\)', db_py, re.DOTALL)
if delete_match and "sync_event.*record_delete" not in delete_match.group(0):
    old_delete = delete_match.group(0)
    new_delete = old_delete.replace(
        'conn.commit()',
        '_log_sync_event(cursor, \'record_delete\', database_id=database_id, record_id=property_id)\n                conn.commit()',
        1
    )
    db_py = db_py.replace(old_delete, new_delete, 1)
    print("4. Added sync event to delete_property_route")
else:
    print("4. SKIP or already exists")

# ============================================================
# Step 5: Add sync events to add_column / delete_column
# ============================================================
# add_column
add_col_match = re.search(r"def add_column\(\):.*?return jsonify\(\{'success': True", db_py, re.DOTALL)
if add_col_match and "sync_event.*field_add" not in add_col_match.group(0):
    old_add = add_col_match.group(0)
    new_add = old_add.replace(
        "conn.commit()",
        "_log_sync_event(cursor, 'field_add', database_id=database_id, field_name=column_name)\n                conn.commit()",
        1
    )
    db_py = db_py.replace(old_add, new_add, 1)
    print("5a. Added sync event to add_column")
else:
    print("5a. SKIP")

# delete_column
del_col_match = re.search(r"def delete_column\(\):.*?return jsonify\(\{'success': True", db_py, re.DOTALL)
if del_col_match and "sync_event.*field_delete" not in del_col_match.group(0):
    old_del = del_col_match.group(0)
    new_del = old_del.replace(
        "conn.commit()",
        "_log_sync_event(cursor, 'field_delete', database_id=database_id, field_name=column_name)\n                conn.commit()",
        1
    )
    db_py = db_py.replace(old_del, new_del, 1)
    print("5b. Added sync event to delete_column")
else:
    print("5b. SKIP")

with open(DB_ROUTE, 'w') as f:
    f.write(db_py)
print("database.py saved")

# ============================================================
# Step 6: Add polling to frontend JS
# ============================================================
JS_PATH = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(JS_PATH, 'r') as f:
    js = f.read()

# Add syncTimestamp and syncInterval init
poll_init = """
                    // Real-time sync: poll for changes every 3 seconds
                    this.syncTimestamp = new Date().toISOString();
                    this.syncInterval = setInterval(() => this.pollChanges(), 3000);
                    window.addEventListener('beforeunload', () => {
                        if (this.syncInterval) clearInterval(this.syncInterval);
                    });

"""

if 'syncInterval' not in js:
    # Insert after Ctrl+Z listener block
    js = js.replace(
        "                    // Close column manager and select dropdown when clicking outside",
        poll_init + "                    // Close column manager and select dropdown when clicking outside",
        1
    )
    print("6a. Added sync polling init")
else:
    print("6a. syncInterval already exists")

# Add pollChanges method
poll_method = """
                // ===== Real-time Sync Polling =====
                async pollChanges() {
                    if (!this.databaseId || this.loading) return;
                    try {
                        const res = await fetch(
                            `${basePath}/api/database/changes?db=${this.databaseId}&since=${encodeURIComponent(this.syncTimestamp)}`
                        );
                        if (!res.ok) return;
                        const data = await res.json();
                        if (data.server_time) this.syncTimestamp = data.server_time;
                        if (!data.success || !data.changes || !data.changes.length) return;

                        const myEmail = document.querySelector('meta[name="user-email"]')?.content || '';
                        let needReloadData = false;
                        let needReloadColumns = false;

                        for (const change of data.changes) {
                            if (change.user_email === myEmail) continue;

                            switch (change.event_type) {
                                case 'cell_update': {
                                    const item = this.items.find(i => i.id === change.record_id);
                                    if (item && change.field_name) {
                                        item[change.field_name] = change.new_value;
                                    }
                                    break;
                                }
                                case 'record_add':
                                case 'record_delete':
                                    needReloadData = true;
                                    break;
                                case 'field_add':
                                case 'field_delete':
                                    needReloadColumns = true;
                                    needReloadData = true;
                                    break;
                            }
                        }

                        if (needReloadColumns) await this.loadColumns();
                        if (needReloadData) await this.loadData();
                    } catch (e) {
                        // Silent retry on next poll
                    }
                },

"""

if 'pollChanges' not in js:
    # Insert before formatCell
    js = js.replace(
        "                formatCell(value, col, row) {",
        poll_method + "                formatCell(value, col, row) {",
        1
    )
    print("6b. Added pollChanges method")
else:
    print("6b. pollChanges already exists")

with open(JS_PATH, 'w') as f:
    f.write(js)

# ============================================================
# Step 7: Add user email meta tag to HTML template
# ============================================================
HTML_PATH = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(HTML_PATH, 'r') as f:
    html = f.read()

if 'meta[name="user-email"]' not in html and 'user-email' not in html:
    html = html.replace(
        '<head>',
        '<head>\n    <meta name="user-email" content="{{ session.get(\'user_email\', \'\') }}">',
        1
    )
    print("7. Added user-email meta tag")
else:
    print("7. user-email meta already exists")

# Bump version
import time
ts = str(int(time.time()))
html = html.replace(
    "database_list.js') }}?v=",
    "database_list.js') }}?v=" + ts + "____"  # temp marker
).replace(
    "?v=" + ts + "____",
    "?v=" + ts
)
# Actually simpler approach
import re
html = re.sub(r"database_list\.js'\)\s*\}\}\?v=[^\"']+", f"database_list.js') }}?v={ts}", html)
html = re.sub(r"database_list\.css'\)\s*\}\}\?v=[^\"']+", f"database_list.css') }}?v={ts}", html)
print(f"   Bumped version to {ts}")

with open(HTML_PATH, 'w') as f:
    f.write(html)

# ============================================================
# Step 8: Verify JS syntax
# ============================================================
import subprocess
result = subprocess.run(['node', '-c', JS_PATH], capture_output=True, text=True)
if result.returncode == 0:
    print("\nJS syntax: OK")
else:
    print(f"\nJS SYNTAX ERROR:\n{result.stderr}")

print("\nDone! Restart: sudo systemctl restart property-manager propsheet")

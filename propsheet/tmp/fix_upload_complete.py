#!/usr/bin/env python3
"""Complete file upload system rewrite"""

# === 1. Rewrite upload route — single transaction with cell update ===
route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(route_path, 'r') as f:
    content = f.read()

# Find and replace the entire upload_file function
import re

# Remove old upload_file and replace
old_upload_start = "# ===== File Upload ====="
old_upload_end_marker = "def get_db_usage"  # function after upload section

if old_upload_start in content:
    start_idx = content.index(old_upload_start)
    # Find the end - right before get_db_usage or end of file
    if old_upload_end_marker in content[start_idx:]:
        # Find the decorator before get_db_usage
        rest = content[start_idx:]
        usage_idx = rest.index(old_upload_end_marker)
        # Go back to find the @bp.route decorator
        lines_before = rest[:usage_idx].rstrip().rsplit('\n', 3)
        end_idx = start_idx + usage_idx
        # Find @bp.route before get_db_usage
        for i in range(end_idx - 1, start_idx, -1):
            if content[i:i+9] == '@bp.route' and 'usage' in content[i:i+100]:
                end_idx = i
                break
    else:
        end_idx = len(content)

    new_upload = '''# ===== File Upload =====
UPLOAD_DIR = '/home/webapp/goldenrabbit/uploads/propsheet'
MAX_DB_SIZE = 1 * 1024 * 1024 * 1024  # 1GB per database
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'hwp', 'txt', 'csv'}


def _rebuild_cell_value(cursor, db_id, record_id, field_name, table_name):
    """Rebuild cell value from file_attachments for a given record+field"""
    from psycopg2 import sql as psql
    cursor.execute(
        "SELECT original_filename, file_path FROM file_attachments WHERE database_id = %s AND record_id = %s AND field_name = %s ORDER BY created_at",
        (db_id, record_id, field_name)
    )
    files = cursor.fetchall()
    if files:
        parts = []
        for f in files:
            fname = f['original_filename'] if isinstance(f, dict) else f[0]
            fpath = f['file_path'] if isinstance(f, dict) else f[1]
            parts.append(f'{fname} ({fpath})')
        cell_value = ', '.join(parts)
    else:
        cell_value = None

    cursor.execute(psql.SQL('UPDATE {} SET {} = %s WHERE id = %s').format(
        psql.Identifier(table_name), psql.Identifier(field_name)
    ), (cell_value, record_id))


@bp.route('/database/<int:db_id>/upload', methods=['POST'])
@login_required
@require_database_role("editor")
def upload_file(db_id):
    """Upload file to a database record — single transaction"""
    import os, uuid
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '파일이 없습니다'}), 400

        file = request.files['file']
        record_id = request.form.get('record_id', type=int)
        field_name = request.form.get('field_name', '')

        if not file.filename or not record_id or not field_name:
            return jsonify({'success': False, 'error': '파일, 레코드ID, 필드명이 필요합니다'}), 400

        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({'success': False, 'error': f'허용되지 않는 파일 형식: {ext}'}), 400

        file_data = file.read()
        file_size = len(file_data)

        # Get DB info
        from services.workspace_service import get_database as _get_db
        db_info = _get_db(db_id)
        if not db_info:
            return jsonify({'success': False, 'error': 'DB not found'}), 404

        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                # Check usage limit
                cursor.execute('SELECT COALESCE(SUM(file_size), 0) as total FROM file_attachments WHERE database_id = %s', (db_id,))
                current_usage = cursor.fetchone()['total']
                if current_usage + file_size > MAX_DB_SIZE:
                    remaining = (MAX_DB_SIZE - current_usage) / (1024*1024)
                    return jsonify({'success': False, 'error': f'용량 초과! 남은: {remaining:.0f}MB (1GB 제한)'}), 400

                # Save physical file
                safe_filename = f'{uuid.uuid4().hex[:12]}.{ext}' if ext else uuid.uuid4().hex[:12]
                upload_dir = os.path.join(UPLOAD_DIR, str(db_id), str(record_id))
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, safe_filename)
                with open(file_path, 'wb') as f:
                    f.write(file_data)

                relative_path = f'/uploads/propsheet/{db_id}/{record_id}/{safe_filename}'

                # Insert metadata
                cursor.execute("""
                    INSERT INTO file_attachments (database_id, record_id, field_name, filename, original_filename, file_size, mime_type, file_path, uploaded_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (db_id, record_id, field_name, safe_filename, file.filename, file_size, file.content_type, relative_path, session.get('user_id')))
                file_id = cursor.fetchone()['id']

                # Rebuild cell value from all attachments
                _rebuild_cell_value(cursor, db_id, record_id, field_name, db_info['table_name'])

                conn.commit()

        logger.info(f"File uploaded: {file.filename} ({file_size} bytes) to db={db_id}, record={record_id}")
        return jsonify({
            'success': True,
            'file': {
                'id': file_id,
                'filename': file.filename,
                'url': relative_path,
                'size': file_size,
                'mime_type': file.content_type
            }
        })
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/database/<int:db_id>/file/<int:file_id>', methods=['DELETE'])
@login_required
@require_database_role("editor")
def delete_file(db_id, file_id):
    """Delete an uploaded file and rebuild cell value"""
    import os
    try:
        from services.workspace_service import get_database as _get_db2
        db_info = _get_db2(db_id)

        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                cursor.execute('SELECT * FROM file_attachments WHERE id = %s AND database_id = %s', (file_id, db_id))
                file_rec = cursor.fetchone()
                if not file_rec:
                    return jsonify({'success': False, 'error': '파일 없음'}), 404

                # Delete physical file
                full_path = '/home/webapp/goldenrabbit' + file_rec['file_path']
                if os.path.exists(full_path):
                    os.remove(full_path)

                # Delete metadata
                cursor.execute('DELETE FROM file_attachments WHERE id = %s', (file_id,))

                # Rebuild cell value
                if db_info:
                    _rebuild_cell_value(cursor, db_id, file_rec['record_id'], file_rec['field_name'], db_info['table_name'])

                conn.commit()

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/database/<int:db_id>/files/<int:record_id>/<field_name>', methods=['GET'])
@login_required
@require_database_role("viewer")
def get_record_files(db_id, record_id, field_name):
    """Get files for a specific record field"""
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, filename, original_filename, file_size, mime_type, file_path, created_at
                    FROM file_attachments
                    WHERE database_id = %s AND record_id = %s AND field_name = %s
                    ORDER BY created_at
                """, (db_id, record_id, field_name))
                files = cursor.fetchall()
                for f in files:
                    if f.get('created_at'):
                        f['created_at'] = f['created_at'].isoformat()
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


'''
    content = content[:start_idx] + new_upload + content[end_idx:]
    with open(route_path, 'w') as f:
        f.write(content)
    print("1. Rewrote upload/delete/files routes")

# === 2. Fix formatCell — extract URL from parentheses ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

# Current: builds URL from airtable path
# Fix: extract URL directly from cell value's parentheses
old_img = """                            if (ext === 'pdf') {
                                // PDF: show icon + filename
                                if (aid) {
                                    const url = `/uploads/airtable/${aid}/${encodeURIComponent(filename)}`;
                                    return `<span class="cell-pdf" onclick="event.stopPropagation(); window.open('${url}', '_blank')">📄 ${filename}</span>`;
                                }
                                return `<span class="cell-pdf">📄 ${filename}</span>`;
                            } else if (aid) {
                                // Image: show thumbnail
                                const url = `/uploads/airtable/${aid}/${encodeURIComponent(filename)}`;"""

new_img = """                            // Extract URL from parentheses — works for both airtable and propsheet paths
                            const urlMatch = value.match(/\\(([^)]+)\\)/);

                            if (ext === 'pdf') {
                                const url = urlMatch ? urlMatch[1] : (aid ? `/uploads/airtable/${aid}/${encodeURIComponent(filename)}` : null);
                                if (url) {
                                    return `<span class="cell-pdf" onclick="event.stopPropagation(); window.open('${url}', '_blank')">📄 ${filename}</span>`;
                                }
                                return `<span class="cell-pdf">📄 ${filename}</span>`;
                            } else {
                                const url = urlMatch ? urlMatch[1] : (aid ? `/uploads/airtable/${aid}/${encodeURIComponent(filename)}` : null);
                                if (url) {"""

if old_img in js:
    js = js.replace(old_img, new_img, 1)
    print("2. Fixed formatCell to use URL from cell value")

# Also fix the image tag line to use the new url variable
old_img_tag = """                                return `<img src="${url}" alt="${filename}" class="cell-thumbnail" loading="lazy" onclick="event.stopPropagation(); window._openImageModal && window._openImageModal(this.src, this.alt)" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='inline'"><span style="display:none">${filename}</span>`;
                            }"""
new_img_tag = """                                return `<img src="${url}" alt="${filename}" class="cell-thumbnail" loading="lazy" onclick="event.stopPropagation(); window._openImageModal && window._openImageModal(this.src, this.alt)" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='inline'"><span style="display:none">${filename}</span>`;
                                }
                                return filename;
                            }"""

if old_img_tag in js:
    js = js.replace(old_img_tag, new_img_tag, 1)
    print("2b. Fixed closing braces")

with open(js_path, 'w') as f:
    f.write(js)

# === 3. Update detail panel attachment UI ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

# Replace the attachment template in detail panel
old_attach = """                                <!-- Attachment field (이미지/PDF) -->
                                <template x-if="col.type === 'attachment'">
                                    <div class="detail-attachment-field">
                                        <span x-html="formatCell(detailPanel.item[col.key], col, detailPanel.item)"></span>
                                        <div class="attachment-upload-area"
                                             @click="triggerFileUpload(detailPanel.item.id, col.key)"
                                             @dragover.prevent="$event.currentTarget.classList.add('dragover')"
                                             @dragleave="$event.currentTarget.classList.remove('dragover')"
                                             @drop.prevent="$event.currentTarget.classList.remove('dragover'); handleFileDrop($event, detailPanel.item.id, col.key)">
                                            <span>+ 파일 추가 (클릭 또는 드래그)</span>
                                        </div>
                                    </div>
                                </template>"""

new_attach = """                                <!-- Attachment field (이미지/PDF) -->
                                <template x-if="col.type === 'attachment'">
                                    <div class="detail-attachment-field">
                                        <span x-html="formatCell(detailPanel.item[col.key], col, detailPanel.item)"></span>
                                        <div class="attachment-upload-area"
                                             @click="triggerFileUpload(detailPanel.item.id, col.key)"
                                             @dragover.prevent="$event.currentTarget.classList.add('dragover')"
                                             @dragleave="$event.currentTarget.classList.remove('dragover')"
                                             @drop.prevent="$event.currentTarget.classList.remove('dragover'); handleFileDrop($event, detailPanel.item.id, col.key)">
                                            <span>+ 파일 추가 (클릭 또는 드래그, 50MB 이하)</span>
                                        </div>
                                    </div>
                                </template>"""

if old_attach in html:
    html = html.replace(old_attach, new_attach, 1)
    print("3. Updated detail panel attachment UI")

# Bump version
html = html.replace('v=20260318b', 'v=20260318c')

with open(html_path, 'w') as f:
    f.write(html)

print("Done!")

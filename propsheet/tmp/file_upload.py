#!/usr/bin/env python3
"""Add file upload feature to Propsheet"""
import re

# === 1. Upload API routes ===
route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(route_path, 'r') as f:
    content = f.read()

if '/upload' not in content:
    upload_routes = '''

# ===== File Upload =====
UPLOAD_DIR = '/home/webapp/goldenrabbit/uploads/propsheet'
MAX_DB_SIZE = 1 * 1024 * 1024 * 1024  # 1GB per database
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'hwp', 'txt', 'csv'}

@bp.route('/database/<int:db_id>/upload', methods=['POST'])
@login_required
@require_database_role("editor")
def upload_file(db_id):
    """Upload file to a database record"""
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
            return jsonify({'success': False, 'error': f'허용되지 않는 파일 형식입니다: {ext}'}), 400

        # Check DB usage limit
        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                cursor.execute('SELECT COALESCE(SUM(file_size), 0) as total FROM file_attachments WHERE database_id = %s', (db_id,))
                current_usage = cursor.fetchone()['total']

        # Read file to check size
        file_data = file.read()
        file_size = len(file_data)

        if current_usage + file_size > MAX_DB_SIZE:
            remaining = (MAX_DB_SIZE - current_usage) / (1024*1024)
            return jsonify({'success': False, 'error': f'용량 초과! 남은 용량: {remaining:.0f}MB (1GB 제한)'}), 400

        # Save file
        safe_filename = f'{uuid.uuid4().hex[:12]}_{ext}' if ext else uuid.uuid4().hex[:12]
        upload_dir = os.path.join(UPLOAD_DIR, str(db_id), str(record_id))
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, safe_filename)

        with open(file_path, 'wb') as f:
            f.write(file_data)

        # Save metadata
        relative_path = f'/uploads/propsheet/{db_id}/{record_id}/{safe_filename}'
        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO file_attachments (database_id, record_id, field_name, filename, original_filename, file_size, mime_type, file_path, uploaded_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (db_id, record_id, field_name, safe_filename, file.filename, file_size, file.content_type, relative_path, session.get('user_id')))
                file_id = cursor.fetchone()['id']
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
    """Delete an uploaded file"""
    import os
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                cursor.execute('SELECT * FROM file_attachments WHERE id = %s AND database_id = %s', (file_id, db_id))
                file_rec = cursor.fetchone()
                if not file_rec:
                    return jsonify({'success': False, 'error': '파일을 찾을 수 없습니다'}), 404

                # Delete physical file
                full_path = '/home/webapp/goldenrabbit' + file_rec['file_path']
                if os.path.exists(full_path):
                    os.remove(full_path)

                # Delete metadata
                cursor.execute('DELETE FROM file_attachments WHERE id = %s', (file_id,))
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


@bp.route('/database/<int:db_id>/usage', methods=['GET'])
@login_required
@require_database_role("viewer")
def get_db_usage(db_id):
    """Get storage usage for a database"""
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT COALESCE(SUM(file_size), 0) as total_bytes,
                           COUNT(*) as file_count
                    FROM file_attachments WHERE database_id = %s
                """, (db_id,))
                usage = cursor.fetchone()
        return jsonify({
            'success': True,
            'usage_bytes': usage['total_bytes'],
            'usage_mb': round(usage['total_bytes'] / (1024*1024), 1),
            'file_count': usage['file_count'],
            'limit_bytes': MAX_DB_SIZE,
            'limit_mb': MAX_DB_SIZE / (1024*1024)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

'''
    # Add before the last line or at the end of the file
    # Find a good insertion point - before the last route or at end
    content += upload_routes
    with open(route_path, 'w') as f:
        f.write(content)
    print("1. Added upload API routes")

# === 2. JS: Add upload functions ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

if 'uploadFile' not in js:
    upload_js = '''
                async uploadFile(recordId, fieldName, file) {
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('record_id', recordId);
                    formData.append('field_name', fieldName);

                    try {
                        const res = await fetch(`${basePath}/api/database/${this.databaseId}/upload`, {
                            method: 'POST',
                            body: formData
                        });
                        if (!_checkAuth(res)) return null;
                        const data = await res.json();
                        if (data.success) {
                            this.showToast('파일이 업로드되었습니다', 'success');
                            return data.file;
                        } else {
                            this.showToast(data.error || '업로드 실패', 'error');
                            return null;
                        }
                    } catch (e) {
                        this.showToast('업로드 실패: ' + e.message, 'error');
                        return null;
                    }
                },

                async deleteFile(fileId) {
                    if (!confirm('파일을 삭제하시겠습니까?')) return false;
                    try {
                        const res = await fetch(`${basePath}/api/database/${this.databaseId}/file/${fileId}`, {
                            method: 'DELETE'
                        });
                        const data = await res.json();
                        if (data.success) {
                            this.showToast('파일이 삭제되었습니다', 'success');
                            return true;
                        }
                        this.showToast(data.error || '삭제 실패', 'error');
                        return false;
                    } catch (e) {
                        this.showToast('삭제 실패: ' + e.message, 'error');
                        return false;
                    }
                },

                async loadRecordFiles(recordId, fieldName) {
                    try {
                        const res = await fetch(`${basePath}/api/database/${this.databaseId}/files/${recordId}/${encodeURIComponent(fieldName)}`);
                        if (!_checkAuth(res)) return [];
                        const data = await res.json();
                        return data.success ? data.files : [];
                    } catch (e) {
                        return [];
                    }
                },

                triggerFileUpload(recordId, fieldName) {
                    const input = document.createElement('input');
                    input.type = 'file';
                    input.accept = 'image/*,.pdf,.doc,.docx,.xls,.xlsx,.hwp,.txt,.csv';
                    input.onchange = async (e) => {
                        const file = e.target.files[0];
                        if (!file) return;
                        const result = await this.uploadFile(recordId, fieldName, file);
                        if (result) {
                            await this.loadData();
                        }
                    };
                    input.click();
                },

                async handleFileDrop(event, recordId, fieldName) {
                    event.preventDefault();
                    const files = event.dataTransfer.files;
                    if (files.length === 0) return;
                    for (let i = 0; i < files.length; i++) {
                        await this.uploadFile(recordId, fieldName, files[i]);
                    }
                    await this.loadData();
                },

'''
    # Insert before formatCellWithColor
    js = js.replace('                formatCellWithColor(value, col) {', upload_js + '                formatCellWithColor(value, col) {', 1)
    with open(js_path, 'w') as f:
        f.write(js)
    print("2. Added upload JS functions")

# === 3. Update formatCell to show uploaded files for attachment fields ===
# The current attachment rendering shows airtable backup images
# We need to also show uploaded files
# For now, add an upload button to attachment cells in the detail panel

html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

# Update the attachment template in detail panel
old_attach = """                                <!-- Attachment field (이미지/PDF) -->
                                <template x-if="col.type === 'attachment'">
                                    <div class="detail-attachment-field">
                                        <span x-html="formatCell(detailPanel.item[col.key], col, detailPanel.item)"></span>
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
                                            <span>+ 파일 추가 (클릭 또는 드래그)</span>
                                        </div>
                                    </div>
                                </template>"""

if 'attachment-upload-area' not in html:
    html = html.replace(old_attach, new_attach, 1)
    print("3. Added upload area to detail panel")

with open(html_path, 'w') as f:
    f.write(html)

# === 4. CSS ===
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
with open(css_path, 'r') as f:
    css = f.read()

if '.attachment-upload-area' not in css:
    css += """
/* File upload area */
.attachment-upload-area {
    margin-top: 8px;
    padding: 16px;
    border: 2px dashed var(--gray-300);
    border-radius: 8px;
    text-align: center;
    cursor: pointer;
    color: var(--gray-400);
    font-size: 13px;
    transition: all 0.15s;
}
.attachment-upload-area:hover {
    border-color: var(--brand-blue, #667eea);
    color: var(--brand-blue, #667eea);
    background: var(--primary-50, #f0f4ff);
}
.attachment-upload-area.dragover {
    border-color: var(--brand-blue, #667eea);
    background: var(--primary-50, #f0f4ff);
    color: var(--brand-blue, #667eea);
}
"""
    with open(css_path, 'w') as f:
        f.write(css)
    print("4. Added upload CSS")

# === 5. Nginx config ===
nginx_path = '/home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf'
with open(nginx_path, 'r') as f:
    nginx = f.read()

if '/uploads/propsheet/' not in nginx:
    # Add after the airtable uploads block
    old_nginx = '    # 블로그 업로드 파일'
    new_nginx = """    # Propsheet 업로드 파일
    location ^~ /uploads/propsheet/ {
        alias /home/webapp/goldenrabbit/uploads/propsheet/;
        autoindex off;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # 블로그 업로드 파일"""
    if old_nginx in nginx:
        nginx = nginx.replace(old_nginx, new_nginx, 1)
        with open(nginx_path, 'w') as f:
            f.write(nginx)
        print("5. Added Nginx config")
    else:
        print("5. WARN: Nginx marker not found")
else:
    print("5. Nginx already configured")

print("\nDone!")

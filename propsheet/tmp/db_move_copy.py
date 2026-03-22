#!/usr/bin/env python3
"""Add database copy-to/move-to another workspace feature"""

# === 1. Backend: Add API routes ===
route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'
with open(route_path, 'r') as f:
    content = f.read()

if 'database/copy-to' not in content:
    # Find the update workspace route to insert before it
    marker = "@bp.route('/api/workspace/<slug>', methods=['PUT', 'PATCH'])"

    new_routes = '''
@bp.route('/api/database/<int:db_id>/copy-to', methods=['POST'])
@propsheet_login_required
def api_copy_database_to(db_id):
    """Copy a database to another workspace"""
    try:
        from services.workspace_service import get_database, clone_database_full
        db = get_database(db_id)
        if not db:
            return jsonify({'success': False, 'error': '데이터베이스를 찾을 수 없습니다'}), 404

        data = request.get_json()
        target_ws_id = data.get('workspace_id')
        new_name = data.get('name', db['name'])
        new_slug = data.get('slug')

        if not target_ws_id or not new_slug:
            return jsonify({'success': False, 'error': '대상 워크스페이스와 슬러그가 필요합니다'}), 400

        new_table = new_slug.replace('-', '_')
        new_db_id = create_database(
            workspace_id=target_ws_id, name=new_name, slug=new_slug,
            table_name=new_table, description=db.get('description', ''),
            icon=db.get('icon', '📊'), color=db.get('color', '#667eea'))

        clone_database_full(db['table_name'], new_table, db['id'], new_db_id)

        logger.info(f"Copied database '{db['name']}' (id={db_id}) to workspace {target_ws_id}")
        return jsonify({'success': True, 'new_db_id': new_db_id})

    except Exception as e:
        logger.error(f"Error copying database: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/database/<int:db_id>/move-to', methods=['POST'])
@propsheet_login_required
def api_move_database_to(db_id):
    """Move a database to another workspace (just update workspace_id)"""
    try:
        from services.workspace_service import get_database
        from services.database_service import get_db_connection
        db = get_database(db_id)
        if not db:
            return jsonify({'success': False, 'error': '데이터베이스를 찾을 수 없습니다'}), 404

        data = request.get_json()
        target_ws_id = data.get('workspace_id')
        if not target_ws_id:
            return jsonify({'success': False, 'error': '대상 워크스페이스가 필요합니다'}), 400

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE databases SET workspace_id = %s WHERE id = %s', (target_ws_id, db_id))
                conn.commit()

        logger.info(f"Moved database '{db['name']}' (id={db_id}) to workspace {target_ws_id}")
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error moving database: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


'''
    content = content.replace(marker, new_routes + marker, 1)
    with open(route_path, 'w') as f:
        f.write(content)
    print("1. Added copy-to/move-to API routes")

# === 2. JS: Add modal state + functions ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(js_path, 'r') as f:
    js = f.read()

if 'showMoveModal' not in js:
    # Add state
    js = js.replace(
        'showCloneModal: false,',
        'showCloneModal: false,\n                showMoveModal: false,\n                moveDb: null,\n                moveTargetWs: \'\',\n                moveAction: \'copy\',\n                moveNewName: \'\',\n                moveNewSlug: \'\','
    )
    print("2a. Added modal state")

    # Add functions before openCloneModal
    move_fns = '''
                openMoveModal(workspace, db, action) {
                    this.moveDb = { ...db, sourceWs: workspace };
                    this.moveAction = action; // 'copy' or 'move'
                    this.moveTargetWs = '';
                    this.moveNewName = action === 'copy' ? db.name + ' (복사)' : db.name;
                    this.moveNewSlug = db.slug + (action === 'copy' ? '_copy' : '');
                    this.showMoveModal = true;
                    this.error = '';
                },

                async submitMove() {
                    if (!this.moveTargetWs) {
                        this.error = '대상 워크스페이스를 선택하세요';
                        return;
                    }
                    if (this.moveAction === 'copy' && !this.moveNewSlug) {
                        this.error = '영문 이름을 입력하세요';
                        return;
                    }

                    const endpoint = this.moveAction === 'copy'
                        ? `/propsheet/api/database/${this.moveDb.id}/copy-to`
                        : `/propsheet/api/database/${this.moveDb.id}/move-to`;

                    const body = { workspace_id: parseInt(this.moveTargetWs) };
                    if (this.moveAction === 'copy') {
                        body.name = this.moveNewName;
                        body.slug = this.moveNewSlug;
                    }

                    try {
                        const res = await fetch(endpoint, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(body)
                        });
                        const data = await res.json();
                        if (data.success) {
                            this.showMoveModal = false;
                            const msg = this.moveAction === 'copy' ? '복제되었습니다' : '이동되었습니다';
                            alert(`데이터베이스가 ${msg}.`);
                            await this.loadWorkspaces();
                        } else {
                            this.error = data.error || '실패';
                        }
                    } catch (e) {
                        this.error = e.message;
                    }
                },

'''
    js = js.replace('                openCloneModal(workspace) {', move_fns + '                openCloneModal(workspace) {')
    print("2b. Added move/copy functions")

with open(js_path, 'w') as f:
    f.write(js)

# === 3. HTML: Add buttons + modal ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(html_path, 'r') as f:
    html = f.read()

if 'openMoveModal' not in html:
    # Add copy-to/move-to buttons in database actions
    old_btns = '''<button @click.stop="duplicateDatabase(workspace, db)" title="복제">
                                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M3 11V3a1.5 1.5 0 011.5-1.5H11"/></svg>
                                    </button>
                                    <button @click.stop="openEditDatabaseModal(workspace, db)" title="편집">'''

    new_btns = '''<button @click.stop="duplicateDatabase(workspace, db)" title="같은 워크스페이스에 복제">
                                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M3 11V3a1.5 1.5 0 011.5-1.5H11"/></svg>
                                    </button>
                                    <button @click.stop="openMoveModal(workspace, db, 'copy')" title="다른 워크스페이스로 복제">
                                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8 1v14M1 8h14"/></svg>
                                    </button>
                                    <button @click.stop="openMoveModal(workspace, db, 'move')" title="다른 워크스페이스로 이동">
                                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 8h12M9 4l4 4-4 4"/></svg>
                                    </button>
                                    <button @click.stop="openEditDatabaseModal(workspace, db)" title="편집">'''

    html = html.replace(old_btns, new_btns, 1)
    print("3a. Added action buttons")

    # Add modal before Clone Workspace Modal
    move_modal = '''        <!-- Move/Copy Database Modal -->
        <div class="modal-overlay" x-show="showMoveModal" x-cloak @click.self="showMoveModal = false" style="display:none;">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 x-text="moveAction === 'copy' ? '다른 워크스페이스로 복제' : '다른 워크스페이스로 이동'"></h2>
                    <button class="btn-close" @click="showMoveModal = false">&times;</button>
                </div>

                <div class="error-message" x-show="error" x-text="error"></div>

                <template x-if="moveDb">
                    <div>
                        <div style="padding:10px;background:var(--gray-50);border-radius:6px;margin-bottom:16px;display:flex;align-items:center;gap:8px;">
                            <span x-text="moveDb.icon || '📊'" style="font-size:20px;"></span>
                            <div>
                                <div style="font-weight:600;" x-text="moveDb.name"></div>
                                <div style="font-size:12px;color:var(--text-secondary);" x-text="moveDb.sourceWs.name + ' 워크스페이스에서'"></div>
                            </div>
                        </div>

                        <div class="form-group">
                            <label>대상 워크스페이스 *</label>
                            <select x-model="moveTargetWs" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:13px;">
                                <option value="">선택하세요</option>
                                <template x-for="ws in workspaces" :key="ws.id">
                                    <template x-if="!moveDb || ws.id !== moveDb.sourceWs.id">
                                        <option :value="ws.id" x-text="ws.icon + ' ' + ws.name"></option>
                                    </template>
                                </template>
                            </select>
                        </div>

                        <template x-if="moveAction === 'copy'">
                            <div>
                                <div class="form-group">
                                    <label>데이터베이스 이름</label>
                                    <input type="text" x-model="moveNewName" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:13px;">
                                </div>
                                <div class="form-group">
                                    <label>영문 URL *</label>
                                    <input type="text" x-model="moveNewSlug" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:13px;">
                                </div>
                            </div>
                        </template>

                        <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:16px;">
                            <button class="btn-cancel" @click="showMoveModal = false">취소</button>
                            <button class="btn-save" @click="submitMove()" x-text="moveAction === 'copy' ? '복제' : '이동'"></button>
                        </div>
                    </div>
                </template>
            </div>
        </div>

'''
    html = html.replace('        <!-- Clone Workspace Modal -->', move_modal + '        <!-- Clone Workspace Modal -->')
    print("3b. Added move/copy modal")

import re
html = re.sub(r'workspaces\.js\?v=\w+', 'workspaces.js?v=20260318e', html)

with open(html_path, 'w') as f:
    f.write(html)

print("Done!")

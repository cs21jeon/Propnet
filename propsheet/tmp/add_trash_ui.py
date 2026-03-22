#!/usr/bin/env python3
"""Add trash UI: button in toolbar + modal with list + restore/permanent delete"""

# === 1. JS: Add trash functions ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

if 'showTrash' not in js:
    # Add state
    js = js.replace(
        'showHistory: false,',
        'showHistory: false,\n                showTrash: false,\n                trashItems: [],'
    )
    print("1a. Added trash state")

    # Add trash methods before pushUndo
    trash_methods = '''
                async loadTrash() {
                    this.showTrash = true;
                    this.trashItems = [];
                    try {
                        const res = await fetch(`${basePath}/api/database/${this.databaseId}/trash`);
                        if (!_checkAuth(res)) return;
                        const data = await res.json();
                        if (data.success) {
                            this.trashItems = data.items;
                        }
                    } catch (e) {}
                },

                async restoreFromTrash(trashId) {
                    try {
                        const res = await fetch(`${basePath}/api/database/${this.databaseId}/trash/${trashId}/restore`, {
                            method: 'POST'
                        });
                        const data = await res.json();
                        if (data.success) {
                            this.showToast('레코드가 복원되었습니다', 'success');
                            await this.loadTrash();
                            await this.loadData();
                        } else {
                            this.showToast(data.error || '복원 실패', 'error');
                        }
                    } catch (e) {
                        this.showToast('복원 실패: ' + e.message, 'error');
                    }
                },

                async permanentDelete(trashId) {
                    if (!confirm('영구 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return;
                    try {
                        const res = await fetch(`${basePath}/api/database/${this.databaseId}/trash/${trashId}`, {
                            method: 'DELETE'
                        });
                        const data = await res.json();
                        if (data.success) {
                            this.showToast('영구 삭제되었습니다', 'success');
                            await this.loadTrash();
                        } else {
                            this.showToast(data.error || '삭제 실패', 'error');
                        }
                    } catch (e) {
                        this.showToast('삭제 실패', 'error');
                    }
                },

                getTrashSummary(recordData) {
                    if (!recordData) return '(데이터 없음)';
                    const keys = ['지번 주소', '도로명주소', '건물명', 'name', 'id'];
                    for (const k of keys) {
                        if (recordData[k]) return String(recordData[k]).substring(0, 50);
                    }
                    return 'ID: ' + (recordData.id || recordData.original_id || '?');
                },

'''
    js = js.replace('                pushUndo(', trash_methods + '                pushUndo(', 1)
    print("1b. Added trash methods")

with open(js_path, 'w') as f:
    f.write(js)

# === 2. HTML: Trash button + modal ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'r') as f:
    html = f.read()

if 'loadTrash' not in html:
    # Add trash button in toolbar (near filter/field buttons)
    old_filter_btn = '<button class="btn" @click="resetFilters()">필터 초기화</button>'
    new_filter_btn = '<button class="btn" @click="resetFilters()">필터 초기화</button>\n                <button class="btn" @click="loadTrash()" title="휴지통">🗑 휴지통</button>'
    html = html.replace(old_filter_btn, new_filter_btn, 1)
    print("2a. Added trash button")

    # Add trash modal before </body>
    trash_modal = '''
    <!-- Trash Modal -->
    <div x-show="showTrash" x-cloak @click.self="showTrash = false"
         style="position:fixed;inset:0;background:rgba(0,0,0,0.3);z-index:5000;display:flex;align-items:center;justify-content:center;">
        <div style="background:white;border-radius:12px;width:550px;max-width:90vw;max-height:70vh;display:flex;flex-direction:column;box-shadow:0 8px 32px rgba(0,0,0,0.2);" @click.stop>
            <div style="display:flex;justify-content:space-between;align-items:center;padding:16px 20px;border-bottom:1px solid var(--gray-100);">
                <h3 style="margin:0;font-size:15px;">🗑 휴지통 <span style="color:var(--gray-400);font-weight:normal;" x-text="trashItems.length ? '(' + trashItems.length + '개)' : ''"></span></h3>
                <button @click="showTrash = false" style="background:none;border:none;font-size:20px;cursor:pointer;">&times;</button>
            </div>
            <div style="overflow-y:auto;flex:1;padding:8px 0;">
                <template x-if="trashItems.length === 0">
                    <p style="color:var(--gray-400);text-align:center;padding:40px;">휴지통이 비어있습니다</p>
                </template>
                <template x-for="item in trashItems" :key="item.id">
                    <div style="display:flex;align-items:center;gap:10px;padding:10px 20px;border-bottom:1px solid var(--gray-50);">
                        <div style="flex:1;min-width:0;">
                            <div style="font-size:13px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" x-text="getTrashSummary(item.record_data)"></div>
                            <div style="font-size:11px;color:var(--gray-400);">
                                <span x-text="formatTimeAgo(item.deleted_at)"></span> 삭제 ·
                                <span x-text="formatTimeAgo(item.expires_at)"></span> 만료
                            </div>
                        </div>
                        <button @click="restoreFromTrash(item.id)"
                                style="padding:4px 12px;border:1px solid #1976d2;background:white;color:#1976d2;border-radius:4px;cursor:pointer;font-size:12px;white-space:nowrap;">복원</button>
                        <button @click="permanentDelete(item.id)"
                                style="padding:4px 12px;border:1px solid #e53935;background:white;color:#e53935;border-radius:4px;cursor:pointer;font-size:12px;white-space:nowrap;">영구삭제</button>
                    </div>
                </template>
            </div>
            <div style="padding:12px 20px;border-top:1px solid var(--gray-100);text-align:center;">
                <span style="font-size:11px;color:var(--gray-400);">삭제된 레코드는 30일 후 자동으로 영구 삭제됩니다</span>
            </div>
        </div>
    </div>
'''
    html = html.replace('</body>', trash_modal + '</body>', 1)
    print("2b. Added trash modal")

# Bump version
html = html.replace('v=20260318f', 'v=20260318g')

with open(html_path, 'w') as f:
    f.write(html)

# === 3. Backend: Add permanent delete API ===
route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(route_path, 'r') as f:
    content = f.read()

if 'permanent_delete_from_trash' not in content:
    perm_delete = '''

@bp.route('/database/<int:db_id>/trash/<int:trash_id>', methods=['DELETE'])
@login_required
@require_database_role("owner")
def permanent_delete_from_trash(db_id, trash_id):
    """Permanently delete a record from trash"""
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                cursor.execute('DELETE FROM deleted_records WHERE id = %s AND database_id = %s', (trash_id, db_id))
                if cursor.rowcount == 0:
                    return jsonify({'success': False, 'error': '항목을 찾을 수 없습니다'}), 404
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

'''
    # Add before file upload section
    marker = '# ===== File Upload ====='
    if marker in content:
        content = content.replace(marker, perm_delete + marker, 1)
    else:
        content += perm_delete
    with open(route_path, 'w') as f:
        f.write(content)
    print("3. Added permanent delete API")

print("Done!")

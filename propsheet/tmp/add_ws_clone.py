#!/usr/bin/env python3
"""Add workspace clone: API route + JS function + UI button"""

# === 1. Route: Add workspace clone API ===
route_path = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'
with open(route_path, 'r') as f:
    content = f.read()

if 'clone_workspace' not in content:
    # Find the update workspace route and insert clone before it
    clone_route = '''
@bp.route('/api/workspace/<slug>/clone', methods=['POST'])
@require_workspace_role('owner')
def api_clone_workspace(slug):
    """Clone entire workspace with all databases"""
    try:
        workspace = get_workspace_by_slug(slug)
        if not workspace:
            return jsonify({'success': False, 'error': '워크스페이스를 찾을 수 없습니다'}), 404

        data = request.get_json()
        new_name = data.get('name', workspace['name'] + ' (복제)')
        new_slug = data.get('slug')
        if not new_slug:
            import secrets, string
            new_slug = slug + '-' + ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4))

        # Create new workspace
        from services.workspace_service import create_workspace
        new_ws_id = create_workspace(
            name=new_name,
            slug=new_slug,
            description=workspace.get('description', ''),
            icon=workspace.get('icon', '📁')
        )

        # Add current user as owner
        user_id = session.get('user_id')
        if user_id:
            from services.workspace_member_service import add_member
            try:
                add_member(new_ws_id, user_id, 'owner', user_id)
            except:
                pass

        # Clone all databases
        databases = get_databases_by_workspace(workspace['id'])
        cloned_dbs = []
        for db in databases:
            import secrets, string
            db_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4))
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

            clone_database_table(
                source_table=db['table_name'],
                target_table=new_table_name,
                source_db_id=db['id'],
                target_db_id=new_db_id
            )
            clone_database_views(db['id'], new_db_id)
            cloned_dbs.append(db['name'])

        logger.info(f"Cloned workspace '{slug}' -> '{new_slug}' ({len(cloned_dbs)} databases)")
        return jsonify({
            'success': True,
            'slug': new_slug,
            'databases_cloned': len(cloned_dbs)
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error cloning workspace: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

'''
    # Insert before the update workspace route
    marker = "@bp.route('/api/workspace/<slug>', methods=['PUT', 'PATCH'])"
    content = content.replace(marker, clone_route + marker, 1)

    # Ensure imports
    if 'get_databases_by_workspace' not in content:
        content = content.replace(
            'from services.workspace_service import',
            'from services.workspace_service import get_databases_by_workspace,',
            1
        )

    with open(route_path, 'w') as f:
        f.write(content)
    print("1. Added clone workspace API route")
else:
    print("1. Already exists")

# === 2. JS: Add cloneWorkspace function ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(js_path, 'r') as f:
    js = f.read()

if 'cloneWorkspace' not in js:
    clone_fn = '''
                async cloneWorkspace(workspace) {
                    const newName = prompt('복제할 워크스페이스 이름:', workspace.name + ' (복제)');
                    if (!newName) return;

                    const newSlug = prompt('영문 이름 (URL):', workspace.slug + '-copy');
                    if (!newSlug) return;

                    try {
                        const res = await fetch(`/propsheet/api/workspace/${workspace.slug}/clone`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ name: newName, slug: newSlug })
                        });
                        const data = await res.json();
                        if (data.success) {
                            alert(`워크스페이스가 복제되었습니다. (${data.databases_cloned}개 데이터베이스)`);
                            this.loadWorkspaces();
                        } else {
                            alert('복제 실패: ' + (data.error || '알 수 없는 오류'));
                        }
                    } catch (e) {
                        alert('복제 실패: ' + e.message);
                    }
                },

'''
    # Insert before loadWorkspaces
    js = js.replace('                async loadWorkspaces() {', clone_fn + '                async loadWorkspaces() {', 1)
    with open(js_path, 'w') as f:
        f.write(js)
    print("2. Added cloneWorkspace JS function")
else:
    print("2. Already exists")

# === 3. HTML: Add clone button to workspace header ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(html_path, 'r') as f:
    html = f.read()

if 'cloneWorkspace' not in html:
    old_edit_btn = '''<button class="edit-btn" @click.stop="openEditWorkspaceModal(workspace)" title="워크스페이스 편집">
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M11.5 1.5l3 3-9 9H2.5v-3l9-9z"/></svg>
                            </button>'''

    new_edit_btn = '''<button class="edit-btn" @click.stop="cloneWorkspace(workspace)" title="워크스페이스 복제">
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M3 11V3a1.5 1.5 0 011.5-1.5H11"/></svg>
                            </button>
                            <button class="edit-btn" @click.stop="openEditWorkspaceModal(workspace)" title="워크스페이스 편집">
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M11.5 1.5l3 3-9 9H2.5v-3l9-9z"/></svg>
                            </button>'''

    html = html.replace(old_edit_btn, new_edit_btn, 1)
    print("3. Added clone button to workspace header")

# Bump
import re
html = re.sub(r'workspaces\.js\?v=\w+', 'workspaces.js?v=20260318a', html)
html = re.sub(r'workspaces\.css\?v=\w+', 'workspaces.css?v=20260318a', html)

with open(html_path, 'w') as f:
    f.write(html)

print("Done!")

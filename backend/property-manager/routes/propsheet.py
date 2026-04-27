#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PropSheet Routes - Slug-based workspace and database management
"""

import logging
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, session

from services.permission_service import (
    propsheet_login_required,
    require_workspace_role,
    require_agent_access
)
from services.workspace_service import (
    clone_database_full, find_orphaned_databases,
    list_workspaces,
    get_workspace_by_slug,
    get_database_by_slug,
    create_workspace,
    create_database,
    update_workspace,
    update_database,
    delete_workspace,
    delete_database,
    create_empty_database_table,
    create_calendar_database_table,
    clone_database_table,
    clone_database_views,
    get_database
)

logger = logging.getLogger(__name__)

bp = Blueprint('propsheet', __name__)


def _get_agent_slug_for_workspace(ws_slug):
    """workspace slug로 agent slug 조회. workspace에 연결된 agent의 slug 반환."""
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT a.slug FROM agents a
                    JOIN workspaces w ON w.agent_id = a.id
                    WHERE w.slug = %s AND a.is_active = true
                    LIMIT 1
                """, (ws_slug,))
                row = cur.fetchone()
                return row['slug'] if row else None
    except Exception:
        return None


def _get_filtered_workspaces():
    """Get workspaces filtered by user role.
    - admin/agent/subagent: 자기 agent_id 워크스페이스만 (admin도 타 agent 데이터 접근 불가)
    - user: workspace_members based
    """
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    user_email = session.get('user_email', '')
    user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)

    logger.info(f"_get_filtered_workspaces: email={user_email}, user_id={user_id}, is_admin={is_admin}")

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # propnet_users에서 role/agent_id 조회 (Single Source of Truth)
            propnet_uid = session.get('propnet_user_id')
            if propnet_uid:
                cur.execute(
                    "SELECT role, agent_id FROM propnet_users WHERE id = %s AND is_active = true",
                    (propnet_uid,)
                )
            else:
                # fallback: service_user_links 경유
                cur.execute("""
                    SELECT pu.role, pu.agent_id FROM propnet_users pu
                    JOIN service_user_links sl ON sl.propnet_user_id = pu.id
                    WHERE sl.service = 'propsheet' AND sl.local_user_id = %s AND pu.is_active = true
                """, (user_id,))
            user_row = cur.fetchone()
            user_role = user_row['role'] if user_row else 'user'
            user_agent_id = user_row['agent_id'] if user_row else None

            if (user_role in ('agent', 'subagent', 'admin') or is_admin) and user_agent_id:
                # Agent/subagent: see workspaces with matching agent_id
                cur.execute("""
                    SELECT w.*, json_agg(
                        json_build_object('id', d.id, 'name', d.name, 'slug', d.slug,
                            'icon', d.icon, 'color', d.color, 'description', d.description, 'table_name', d.table_name)
                        ORDER BY d.display_order, d.id
                    ) FILTER (WHERE d.id IS NOT NULL) AS databases
                    FROM workspaces w
                    LEFT JOIN databases d ON d.workspace_id = w.id
                    WHERE w.agent_id = %s
                    GROUP BY w.id
                    ORDER BY w.display_order, w.id
                """, (user_agent_id,))
                workspaces = [dict(r) for r in cur.fetchall()]
                logger.info(f"  Agent/Subagent (agent_id={user_agent_id}): returning {len(workspaces)} workspaces")
                return workspaces

            # Regular user: workspace_members based
            cur.execute("""
                SELECT w.*, json_agg(
                    json_build_object('id', d.id, 'name', d.name, 'slug', d.slug,
                        'icon', d.icon, 'color', d.color, 'table_name', d.table_name)
                    ORDER BY d.display_order, d.id
                ) FILTER (WHERE d.id IS NOT NULL) AS databases
                FROM workspaces w
                JOIN workspace_members wm ON wm.workspace_id = w.id AND wm.user_id = %s
                LEFT JOIN databases d ON d.workspace_id = w.id
                GROUP BY w.id
                ORDER BY w.display_order, w.id
            """, (user_id,))
            workspaces = [dict(r) for r in cur.fetchall()]
            logger.info(f"  User (member): returning {len(workspaces)} workspaces")
            return workspaces


def legacy_workspace_view():
    """Redirect old workspace-view URL to new PropSheet workspaces"""
    return flask_redirect('/propsheet/workspaces', code=301)


@bp.route('/legacy/database')
def legacy_database():
    """Redirect old database URL to new slug-based URL"""
    db_id = request.args.get('db', type=int)
    db_mapping = {
        1: '/propsheet/goldenrabbit/single',
        2: '/propsheet/goldenrabbit/multi-unit',
    }
    new_url = db_mapping.get(db_id, '/propsheet/workspaces')
    return flask_redirect(new_url, code=301)


@bp.route('/workspaces')
@propsheet_login_required
def workspaces_list():
    """Render PropSheet workspaces overview page"""
    try:
        workspaces = _get_filtered_workspaces()

        # Get agent info for broker card
        agent_info = None
        try:
            from services.database_service import get_db_connection
            from psycopg2.extras import RealDictCursor
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    ue = session.get('user_email', '')
                    cur.execute("SELECT * FROM agents WHERE email = %s AND is_active = true", (ue,))
                    agent_info = cur.fetchone()
                    if not agent_info:
                        # propnet_users에서 agent_id 조회 (SSoT)
                        cur.execute("SELECT agent_id FROM propnet_users WHERE email = %s AND is_active = true", (ue,))
                        u = cur.fetchone()
                        if u and u.get('agent_id'):
                            cur.execute("SELECT * FROM agents WHERE id = %s AND is_active = true", (u['agent_id'],))
                            agent_info = cur.fetchone()
        except Exception:
            pass

        _agent_slug = agent_info.get('slug', '') if agent_info else ''
        response = make_response(render_template('propsheet/workspaces.html',
                                         workspaces=workspaces,
                                         agent_info=agent_info,
                                         agent_slug=_agent_slug,
                                         primary_ws_slug=_agent_slug))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"Error loading workspaces: {e}")
        return f"Error loading workspaces: {e}", 500


@bp.route('/workspace/<slug>')
def workspace_detail_redirect(slug):
    """301 리다이렉트: 기존 workspace URL → agent_slug URL"""
    agent_slug = _get_agent_slug_for_workspace(slug)
    if agent_slug:
        return redirect(f'/propsheet/{agent_slug}/', code=301)
    return redirect('/propsheet/workspaces', code=301)


@bp.route('/workspace/<ws_slug>/database/<db_slug>')
def database_view_redirect(ws_slug, db_slug):
    """301 리다이렉트: 기존 database URL → agent_slug URL"""
    agent_slug = _get_agent_slug_for_workspace(ws_slug)
    if agent_slug:
        return redirect(f'/propsheet/{agent_slug}/{db_slug}', code=301)
    return redirect('/propsheet/workspaces', code=301)




@bp.route('/workspace/<ws_slug>/database/<db_slug>/calendar')
def calendar_view_redirect(ws_slug, db_slug):
    """301 리다이렉트: 기존 calendar URL → agent_slug URL"""
    agent_slug = _get_agent_slug_for_workspace(ws_slug)
    if agent_slug:
        return redirect(f'/propsheet/{agent_slug}/{db_slug}/calendar', code=301)
    return redirect('/propsheet/workspaces', code=301)


# API endpoints for workspace management

@bp.route('/api/workspaces', methods=['GET'])
@propsheet_login_required
def api_list_workspaces():
    """Get all workspaces with their databases"""
    try:
        workspaces = _get_filtered_workspaces()
        return jsonify({'success': True, 'workspaces': workspaces})
    except Exception as e:
        logger.error(f"Error listing workspaces: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/workspace', methods=['POST'])
@propsheet_login_required
def api_create_workspace():
    """Create a new workspace"""
    try:
        data = request.get_json()
        name = data.get('name')
        slug = data.get('slug')

        if not name:
            return jsonify({'success': False, 'error': '이름이 필요합니다'}), 400
        if not slug:
            return jsonify({'success': False, 'error': '영문 이름(slug)이 필요합니다'}), 400

        workspace_id = create_workspace(
            name=name,
            slug=slug,
            description=data.get('description'),
            icon=data.get('icon', '📁')
        )

        # Auto-register creator as owner
        user_id = session.get('user_id')
        if user_id:
            try:
                from services.workspace_member_service import add_member
                add_member(workspace_id=workspace_id, user_id=user_id,
                          role='owner', invited_by=user_id)
            except Exception as e:
                logger.warning(f"Failed to auto-add owner: {e}")

        return jsonify({'success': True, 'id': workspace_id, 'slug': slug})
    except ValueError as e:
        logger.error(f"Validation error creating workspace: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/workspace/<slug>/database', methods=['POST'])
@require_workspace_role('owner')
def api_create_database(slug):
    """Create a new database in workspace"""
    try:
        workspace = get_workspace_by_slug(slug)
        if not workspace:
            return jsonify({'success': False, 'error': '워크스페이스를 찾을 수 없습니다'}), 404

        data = request.get_json()
        name = data.get('name')
        db_slug = data.get('slug')
        mode = data.get('mode', 'empty')
        source_db_id = data.get('source_db_id')

        if not name:
            return jsonify({'success': False, 'error': '데이터베이스 이름이 필요합니다'}), 400
        if not db_slug:
            return jsonify({'success': False, 'error': '영문 이름(slug)이 필요합니다'}), 400

        table_name = db_slug

        database_id = create_database(
            workspace_id=workspace['id'],
            name=name,
            slug=db_slug,
            table_name=table_name,
            description=data.get('description'),
            icon=data.get('icon', '📊'),
            color=data.get('color', '#667eea')
        )

        if mode == 'clone' and source_db_id:
            source_db = get_database(source_db_id)
            if not source_db:
                return jsonify({'success': False, 'error': '원본 데이터베이스를 찾을 수 없습니다'}), 404

            clone_database_table(
                source_table=source_db['table_name'],
                target_table=table_name,
                source_db_id=source_db_id,
                target_db_id=database_id
            )
            clone_database_views(source_db_id, database_id)
        elif data.get('template') == 'calendar':
            create_calendar_database_table(table_name, database_id)
            # Create default calendar view
            from services.view_service import create_view
            import json
            create_view(
                database_id=database_id,
                name='캘린더',
                slug='calendar',
                column_config={
                    'calendar': {
                        'date_field': '시작일',
                        'end_date_field': '종료일',
                        'title_field': '제목',
                        'color_field': '카테고리'
                    }
                },
                view_type='calendar'
            )
        elif data.get('template') == 'proptalk':
            # Proptalk 통화요약 DB
            room_id = data.get('room_id')
            room_name = data.get('room_name', '')
            if not room_id:
                return jsonify({'success': False, 'error': '채팅방을 선택해주세요'}), 400

            from services.proptalk_service import create_proptalk_database_table, import_all_audio_files

            # 테이블 + field_definitions 생성
            create_proptalk_database_table(table_name, database_id)

            # external_source 설정
            from services.database_service import get_db_connection as _get_conn
            from psycopg2.extras import Json as _Json
            with _get_conn() as _conn:
                with _conn.cursor() as _cur:
                    _cur.execute(
                        "UPDATE databases SET external_source = 'proptalk', external_config = %s WHERE id = %s",
                        (_Json({"room_id": room_id, "room_name": room_name}), database_id)
                    )
                    _conn.commit()

            # 기존 음성 파일 가져오기
            imported = import_all_audio_files(room_id, database_id, table_name)
            logger.info(f"Proptalk DB created: room={room_id}, imported={imported}")
        else:
            create_empty_database_table(table_name)

        return jsonify({'success': True, 'id': database_id, 'slug': db_slug})
    except ValueError as e:
        logger.error(f"Validation error creating database: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



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
            import secrets as _s
            import string as _str
            new_slug = slug + '-' + ''.join(_s.choice(_str.ascii_lowercase + _str.digits) for _ in range(4))

        # Create new workspace
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

        # Clone selected databases (or all if not specified)
        all_databases = workspace.get('databases', [])
        selected_ids = data.get('database_ids')
        if selected_ids:
            databases = [db for db in all_databases if db['id'] in selected_ids]
        else:
            databases = all_databases
        # Clean orphaned records first
        find_orphaned_databases(cleanup=True)

        results = {'cloned': [], 'failed': []}
        for db in databases:
            new_db_slug = db['slug']
            new_table_name = new_slug.replace('-', '_') + '_' + db['slug'].replace('-', '_')
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
                        pass

        cloned_count = len(results['cloned'])
        logger.info(f"Cloned workspace '{slug}' -> '{new_slug}' ({cloned_count} databases)")
        return jsonify({
            'success': True,
            'slug': new_slug,
            'databases_cloned': cloned_count,
            'databases_failed': len(results['failed']),
            'details': results
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error cloning workspace: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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


@bp.route('/api/workspace/<slug>', methods=['PUT', 'PATCH'])
@require_workspace_role('owner')
def api_update_workspace(slug):
    """Update workspace"""
    try:
        workspace = get_workspace_by_slug(slug)
        if not workspace:
            return jsonify({'success': False, 'error': '워크스페이스를 찾을 수 없습니다'}), 404

        data = request.get_json()
        success = update_workspace(workspace['id'], data)

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '업데이트 실패'}), 400
    except Exception as e:
        logger.error(f"Error updating workspace: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/workspace/<slug>', methods=['DELETE'])
@require_workspace_role('owner')
def api_delete_workspace(slug):
    """Delete workspace"""
    try:
        workspace = get_workspace_by_slug(slug)
        if not workspace:
            return jsonify({'success': False, 'error': '워크스페이스를 찾을 수 없습니다'}), 404

        success = delete_workspace(workspace['id'])
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '삭제 실패'}), 404
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/workspace/<ws_slug>/database/<db_slug>', methods=['PUT', 'PATCH'])
@require_workspace_role('owner')
def api_update_database(ws_slug, db_slug):
    """Update database"""
    try:
        database = get_database_by_slug(ws_slug, db_slug)
        if not database:
            return jsonify({'success': False, 'error': '데이터베이스를 찾을 수 없습니다'}), 404

        data = request.get_json()
        success = update_database(database['id'], data)

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '업데이트 실패'}), 400
    except Exception as e:
        logger.error(f"Error updating database: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/workspace/<ws_slug>/database/<db_slug>', methods=['DELETE'])
@require_workspace_role('owner')
def api_delete_database(ws_slug, db_slug):
    """Delete database"""
    try:
        database = get_database_by_slug(ws_slug, db_slug)
        if not database:
            return jsonify({'success': False, 'error': '데이터베이스를 찾을 수 없습니다'}), 404

        success = delete_database(database['id'])
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '삭제 실패'}), 404
    except Exception as e:
        logger.error(f"Error deleting database: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== Subagent Management =====

@bp.route('/api/agent/subagents', methods=['GET'])
@propsheet_login_required
def list_subagents():
    """List subagents for the current agent"""
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    user_id = session.get('user_id')
    # Find agent record for this user
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM agents WHERE email = %s AND is_active = true", (session.get('user_email'),))
            agent = cur.fetchone()
            if not agent:
                return jsonify({'success': False, 'error': 'Agent 권한이 없습니다'}), 403

            agent_id = agent['id']

            # Get subagents (propnet_users SSoT)
            cur.execute("""
                SELECT pu.id, pu.email, pu.name, pu.role, pu.avatar_url, pu.is_active, pu.created_at
                FROM propnet_users pu
                WHERE pu.agent_id = %s AND pu.role = 'subagent' AND pu.is_active = true
                ORDER BY pu.created_at
            """, (agent_id,))
            subagents = [dict(r) for r in cur.fetchall()]

            # Get pending/accepted invitations (subagent_invitations, propnet_user_id 기반)
            cur.execute("SELECT id FROM propnet_users WHERE email = %s AND is_active = true", (session.get('user_email'),))
            pu_agent = cur.fetchone()
            propnet_agent_id = pu_agent['id'] if pu_agent else None
            requests = []
            if propnet_agent_id:
                cur.execute("""
                    SELECT id, invited_email AS email, status, created_at AS requested_at
                    FROM subagent_invitations
                    WHERE agent_id = %s
                    ORDER BY created_at DESC
                """, (propnet_agent_id,))
                requests = [dict(r) for r in cur.fetchall()]
            for r in requests:
                if r.get('requested_at'):
                    r['requested_at'] = r['requested_at'].isoformat()
                if not r.get('name'):
                    r['name'] = r.get('email', '').split('@')[0]

            # Get agent info
            cur.execute("SELECT max_subagents, remaining_subagent_slots FROM agents WHERE id = %s", (agent_id,))
            agent_info = cur.fetchone()

    return jsonify({
        'success': True,
        'subagents': subagents,
        'requests': requests,
        'max_subagents': agent_info['max_subagents'] if agent_info else 2,
        'remaining_slots': agent_info['remaining_subagent_slots'] if agent_info else 0
    })


def _send_email_async(to_email, subject, html):
    """공통 이메일 발송 (비동기)"""
    import os
    import smtplib
    import threading
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    email_addr = os.environ.get('EMAIL_ADDRESS')
    email_pass = os.environ.get('EMAIL_PASSWORD')
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))

    if not email_addr or not email_pass or not to_email:
        logger.warning("[Email] config missing, skip")
        return

    def _send():
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email_addr
            msg['To'] = to_email
            msg.attach(MIMEText(html, 'html', 'utf-8'))
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_addr, email_pass)
            server.send_message(msg)
            server.quit()
            logger.info(f"[Email] Sent to {to_email}: {subject}")
        except Exception as e:
            logger.error(f"[Email] Failed to {to_email}: {e}")

    threading.Thread(target=_send, daemon=True).start()


def _send_subagent_invite_email(to_email, to_name, agency_name, token):
    """서브에이전트 초대 이메일 (수락/거절 버튼 포함)"""
    accept_url = f"https://propnet.kr/propsheet/api/invitation/accept?token={token}"
    reject_url = f"https://propnet.kr/propsheet/api/invitation/reject?token={token}"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:'Apple SD Gothic Neo',sans-serif;color:#333;">
      <div style="background:#2962FF;color:white;padding:24px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="margin:0;font-size:22px;">PropNet 보조중개사 초대</h1>
      </div>
      <div style="padding:24px;background:#fff;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 8px 8px;">
        <p style="font-size:16px;"><b>{to_name}</b>님, 안녕하세요!</p>
        <p style="font-size:15px;"><b>{agency_name}</b>에서 보조중개사로 초대하였습니다.</p>
        <p style="font-size:14px;color:#555;">수락하시면 해당 사무소의 매물 데이터베이스에 접근할 수 있으며,
          Propedia 앱에서 검색한 부동산 정보를 직접 저장할 수 있습니다.</p>
        <div style="text-align:center;margin:28px 0;">
          <a href="{accept_url}"
             style="display:inline-block;background:#2962FF;color:white;padding:14px 36px;
                    border-radius:8px;text-decoration:none;font-size:16px;font-weight:600;
                    margin-right:12px;">수락</a>
          <a href="{reject_url}"
             style="display:inline-block;background:#9e9e9e;color:white;padding:14px 36px;
                    border-radius:8px;text-decoration:none;font-size:16px;font-weight:600;">거절</a>
        </div>
        <p style="font-size:12px;color:#999;">이 초대는 7일 후 만료됩니다. 본 메일은 PropNet에서 자동 발송되었습니다.</p>
      </div>
    </div>
    """
    _send_email_async(to_email, f'[PropNet] {agency_name}에서 보조중개사로 초대하였습니다', html)


def _send_subagent_welcome_email(to_email, to_name, agency_name, agent_slug):
    """서브에이전트 수락 완료 후 환영 메일 (PropSheet 이동 버튼)"""
    from urllib.parse import quote
    propsheet_url = f"https://propnet.kr/propsheet/{agent_slug}/?login_hint={quote(to_email)}"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:'Apple SD Gothic Neo',sans-serif;color:#333;">
      <div style="background:#2962FF;color:white;padding:24px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="margin:0;font-size:22px;">환영합니다!</h1>
      </div>
      <div style="padding:24px;background:#fff;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 8px 8px;">
        <p style="font-size:16px;"><b>{to_name}</b>님, <b>{agency_name}</b> 팀에 합류하셨습니다.</p>
        <p style="font-size:14px;color:#555;">아래 버튼을 눌러 PropSheet에서 매물 데이터를 확인하세요.</p>
        <div style="text-align:center;margin:28px 0;">
          <a href="{propsheet_url}"
             style="display:inline-block;background:#2962FF;color:white;padding:14px 40px;
                    border-radius:8px;text-decoration:none;font-size:16px;font-weight:600;">
            PropSheet 열기
          </a>
        </div>
        <div style="background:#fff3e0;border-radius:6px;padding:12px 16px;margin-top:8px;">
          <p style="font-size:13px;color:#e65100;margin:0;">⚠ 로그인 시 반드시 <b>{to_email}</b> 계정으로 로그인해주세요.</p>
        </div>
        <p style="font-size:12px;color:#999;margin-top:16px;">본 메일은 PropNet에서 자동 발송되었습니다.</p>
      </div>
    </div>
    """
    _send_email_async(to_email, f'[PropNet] {agency_name} 팀에 합류하셨습니다', html)


def _send_agent_subagent_accepted_email(agent_email, agent_name, subagent_email, subagent_name, agent_slug):
    """Agent에게 보조중개사 수락 알림 메일"""
    propsheet_url = f"https://propnet.kr/propsheet/{agent_slug}/"

    html = f"""
    <div style="max-width:600px;margin:0 auto;font-family:'Apple SD Gothic Neo',sans-serif;color:#333;">
      <div style="background:#2962FF;color:white;padding:24px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="margin:0;font-size:22px;">보조중개사 합류 알림</h1>
      </div>
      <div style="padding:24px;background:#fff;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 8px 8px;">
        <p style="font-size:16px;"><b>{agent_name}</b>님, 안녕하세요!</p>
        <p style="font-size:15px;"><b>{subagent_name}</b> ({subagent_email})님이 보조중개사 초대를 수락했습니다.</p>
        <div style="text-align:center;margin:28px 0;">
          <a href="{propsheet_url}"
             style="display:inline-block;background:#2962FF;color:white;padding:14px 40px;
                    border-radius:8px;text-decoration:none;font-size:16px;font-weight:600;">
            PropSheet에서 확인
          </a>
        </div>
        <p style="font-size:12px;color:#999;">본 메일은 PropNet에서 자동 발송되었습니다.</p>
      </div>
    </div>
    """
    _send_email_async(agent_email, f'[PropNet] {subagent_name}님이 보조중개사 초대를 수락했습니다', html)


@bp.route('/api/agent/invite-subagent', methods=['POST'])
@propsheet_login_required
def invite_subagent():
    """Invite a subagent by email - subagent_invitations 테이블 사용"""
    import sys
    sys.path.insert(0, '/home/webapp/goldenrabbit/backend/shared')
    from propnet_auth.invitation import create_invitation
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    data = request.get_json()
    invite_email = data.get('email', '').strip().lower()
    invite_name = data.get('name', '').strip()

    if not invite_email:
        return jsonify({'success': False, 'error': '이메일을 입력해주세요'}), 400

    # 구독 활성 상태에서만 초대 가능
    propnet_uid = session.get('propnet_user_id')
    if propnet_uid:
        try:
            from propnet_auth.billing_check import check_propsheet_access
            allowed, reason = check_propsheet_access(propnet_uid)
            if not allowed:
                return jsonify({'success': False, 'error': '구독이 활성 상태일 때만 보조중개사를 초대할 수 있습니다.'}), 403
        except Exception as e:
            logger.warning(f"Billing check in invite_subagent failed: {e}")

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verify caller is agent
            cur.execute("SELECT id, remaining_subagent_slots, agency_name, slug FROM agents WHERE email = %s AND is_active = true",
                        (session.get('user_email'),))
            agent = cur.fetchone()
            if not agent:
                return jsonify({'success': False, 'error': 'Agent 권한이 없습니다'}), 403

            if agent['remaining_subagent_slots'] <= 0:
                return jsonify({'success': False, 'error': '보조중개사 슬롯이 부족합니다'}), 400

            agent_id = agent['id']

            # Check if already exists as subagent (propnet_users SSoT, Gmail 점 정규화 포함)
            from utils.email_utils import find_user_by_email
            _existing_pu = find_user_by_email(cur, 'propnet_users', invite_email, 'AND agent_id = %s AND role = %s', (agent_id, 'subagent'))
            if _existing_pu:
                return jsonify({'success': False, 'error': '이미 등록된 보조중개사입니다'}), 400

    # propnet_auth로 초대 생성 (subagent_invitations 테이블)
    if not propnet_uid:
        return jsonify({'success': False, 'error': '인증 정보가 없습니다'}), 401

    invitation = create_invitation(propnet_uid, invite_email)
    if not invitation:
        return jsonify({'success': False, 'error': '초대 생성에 실패했습니다 (이미 대기 중이거나 권한 부족)'}), 400

    # 슬롯 차감
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE agents SET remaining_subagent_slots = remaining_subagent_slots - 1 WHERE id = %s",
                        (agent['id'],))
            conn.commit()

    # 초대 이메일 발송 (수락/거절 버튼)
    _send_subagent_invite_email(
        invite_email,
        invite_name or invite_email.split('@')[0],
        agent.get('agency_name', ''),
        invitation['token']
    )

    return jsonify({'success': True, 'message': f'{invite_email}에 초대를 보냈습니다'})


@bp.route('/api/agent/remove-subagent/<int:user_id>', methods=['DELETE'])
@propsheet_login_required
def remove_subagent(user_id):
    """Remove a subagent"""
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM agents WHERE email = %s AND is_active = true",
                        (session.get('user_email'),))
            agent = cur.fetchone()
            if not agent:
                return jsonify({'success': False, 'error': 'Agent 권한이 없습니다'}), 403

            # Remove subagent role (propnet_users SSoT)
            # user_id here is propnet_users.id from the subagent list
            cur.execute("""
                UPDATE propnet_users SET role = 'user', agent_id = NULL
                WHERE id = %s AND agent_id = %s AND role = 'subagent'
            """, (user_id, agent['id']))

            if cur.rowcount > 0:
                # Remove from workspace_members (service_user_links로 local_user_id 조회)
                cur.execute(
                    "SELECT local_user_id FROM service_user_links WHERE propnet_user_id = %s AND service = 'propsheet'",
                    (user_id,))
                link = cur.fetchone()
                if link:
                    cur.execute("""
                        DELETE FROM workspace_members
                        WHERE user_id = %s AND workspace_id IN (
                            SELECT w.id FROM workspaces w WHERE w.agent_id = %s
                        )
                    """, (link['local_user_id'], agent['id']))

                # Restore slot
                cur.execute("UPDATE agents SET remaining_subagent_slots = remaining_subagent_slots + 1 WHERE id = %s",
                            (agent['id'],))

            conn.commit()

    return jsonify({'success': True, 'message': '서브에이전트가 해제되었습니다'})


@bp.route('/api/agent/cancel-invite/<int:request_id>', methods=['DELETE'])
@propsheet_login_required
def cancel_subagent_invite(request_id):
    """Cancel a pending subagent invitation (subagent_invitations)"""
    import sys
    sys.path.insert(0, '/home/webapp/goldenrabbit/backend/shared')
    from propnet_auth.invitation import cancel_invitation
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    propnet_uid = session.get('propnet_user_id')
    if not propnet_uid:
        return jsonify({'success': False, 'error': '인증 정보가 없습니다'}), 401

    deleted = cancel_invitation(request_id, propnet_uid)
    if deleted:
        # 슬롯 복원
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM agents WHERE email = %s AND is_active = true",
                            (session.get('user_email'),))
                agent = cur.fetchone()
                if agent:
                    cur.execute("UPDATE agents SET remaining_subagent_slots = remaining_subagent_slots + 1 WHERE id = %s",
                                (agent['id'],))
                conn.commit()

    return jsonify({'success': True, 'message': '초대가 취소되었습니다'})


# ===== Invitation Accept/Reject (email link) =====

def _invitation_result_page(title, message, button_text=None, button_url=None, is_error=False):
    """초대 결과 페이지 HTML 생성"""
    color = '#d32f2f' if is_error else '#2962FF'
    button_html = ''
    if button_text and button_url:
        button_html = f"""
        <div style="text-align:center;margin:28px 0;">
          <a href="{button_url}"
             style="display:inline-block;background:{color};color:white;padding:14px 40px;
                    border-radius:8px;text-decoration:none;font-size:16px;font-weight:600;">
            {button_text}
          </a>
        </div>
        """
    return f"""
    <!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{title} - PropNet</title>
    <link rel="icon" href="/static/images/propnet-icon.png" type="image/png">
    </head><body style="margin:0;background:#f5f5f5;font-family:'Apple SD Gothic Neo',sans-serif;">
    <div style="max-width:500px;margin:60px auto;">
      <div style="background:{color};color:white;padding:24px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="margin:0;font-size:22px;">{title}</h1>
      </div>
      <div style="padding:24px;background:#fff;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 8px 8px;">
        <p style="font-size:15px;color:#333;line-height:1.6;">{message}</p>
        {button_html}
      </div>
    </div></body></html>
    """


@bp.route('/api/invitation/accept')
def accept_invitation_email():
    """이메일 수락 링크 클릭 시 초대 수락 처리"""
    import sys
    sys.path.insert(0, '/home/webapp/goldenrabbit/backend/shared')
    from propnet_auth.invitation import accept_invitation_by_token
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    token = request.args.get('token', '')
    if not token:
        return _invitation_result_page('초대 오류', '유효하지 않은 링크입니다.', is_error=True), 400

    result = accept_invitation_by_token(token)
    if not result:
        return _invitation_result_page(
            '초대 오류',
            '유효하지 않거나 만료된 초대 링크입니다.<br><br>이미 수락/거절한 초대이거나 7일이 지나 만료되었을 수 있습니다.',
            is_error=True
        ), 400

    agency_name = result.get('agency_name', '')
    agent_slug = result.get('agent_slug', '')
    agent_email = result.get('agent_email', '')
    agent_name = result.get('agent_name', '')
    invited_email = result['invitation']['invited_email']

    if result['user_exists']:
        # 이미 가입된 유저: workspace_members 자동 추가
        propnet_user_id = result['propnet_user_id']
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT id FROM agents WHERE slug = %s AND is_active = true", (agent_slug,))
                    agent_row = cur.fetchone()
                    if agent_row:
                        agents_table_id = agent_row['id']
                        cur.execute(
                            "SELECT local_user_id FROM service_user_links WHERE propnet_user_id = %s AND service = 'propsheet'",
                            (propnet_user_id,))
                        link = cur.fetchone()
                        if link:
                            cur.execute("SELECT id FROM workspaces WHERE agent_id = %s", (agents_table_id,))
                            for ws in cur.fetchall():
                                cur.execute("""
                                    INSERT INTO workspace_members (workspace_id, user_id, role, accepted_at)
                                    VALUES (%s, %s, 'editor', NOW())
                                    ON CONFLICT (workspace_id, user_id) DO NOTHING
                                """, (ws['id'], link['local_user_id']))
                    conn.commit()
        except Exception as e:
            logger.error(f"[Invitation Accept] workspace_members error: {e}")

        # 환영 메일 + Agent 알림
        _send_subagent_welcome_email(invited_email, invited_email.split('@')[0], agency_name, agent_slug)
        _send_agent_subagent_accepted_email(agent_email, agent_name, invited_email, invited_email.split('@')[0], agent_slug)

        from urllib.parse import quote
        propsheet_url = f"https://propnet.kr/propsheet/{agent_slug}/?login_hint={quote(invited_email)}"
        return _invitation_result_page(
            '초대 수락 완료',
            f'<b>{agency_name}</b> 팀에 합류하셨습니다!<br><br>PropSheet에서 매물 데이터를 확인하세요.'
            f'<br><br><span style="background:#fff3e0;padding:8px 12px;border-radius:4px;font-size:13px;color:#e65100;">'
            f'⚠ 로그인 시 <b>{invited_email}</b> 계정을 사용해주세요.</span>',
            button_text='PropSheet 열기',
            button_url=propsheet_url
        )
    else:
        # 미가입 유저: 회원가입 안내
        register_url = "https://propnet.kr/register/?role=subagent"
        return _invitation_result_page(
            '초대 수락 완료',
            f'<b>{agency_name}</b>의 보조중개사 초대를 수락하셨습니다.<br><br>PropNet 회원가입 후 자동으로 팀에 합류됩니다.',
            button_text='회원가입',
            button_url=register_url
        )


@bp.route('/api/invitation/reject')
def reject_invitation_email():
    """이메일 거절 링크 클릭 시 초대 거절 처리"""
    import sys
    sys.path.insert(0, '/home/webapp/goldenrabbit/backend/shared')
    from propnet_auth.invitation import reject_invitation_by_token

    token = request.args.get('token', '')
    if not token:
        return _invitation_result_page('초대 오류', '유효하지 않은 링크입니다.', is_error=True), 400

    result = reject_invitation_by_token(token)
    if not result:
        return _invitation_result_page(
            '초대 오류',
            '유효하지 않거나 만료된 초대 링크입니다.',
            is_error=True
        ), 400

    return _invitation_result_page(
        '초대 거절',
        '초대를 거절하셨습니다.<br><br>나중에 마음이 바뀌시면 초대를 다시 요청해주세요.'
    )


def _get_agent_room_ids():
    """현재 로그인 유저의 agent proptalk room_id 목록 조회 (agent 격리용, SSoT=propnet_users)"""
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor
    propnet_uid = session.get('propnet_user_id')
    if not propnet_uid:
        return []  # None이면 전체 조회되므로 빈 리스트 반환
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT a.proptalk_room_id FROM agents a
                    JOIN propnet_users pu ON pu.agent_id = a.id
                    WHERE pu.id = %s AND a.proptalk_room_id IS NOT NULL
                """, (propnet_uid,))
                row = cur.fetchone()
                return [row['proptalk_room_id']] if row else []
    except Exception:
        return []  # 에러 시에도 빈 리스트 (전체 노출 방지)


@bp.route('/api/proptalk/check-phones', methods=['GET', 'POST'])
@propsheet_login_required
def api_proptalk_check_phones():
    """Check which phone numbers have Proptalk audio records (agent 격리)"""
    try:
        from services.proptalk_service import check_matched_phones
        if request.method == 'GET':
            # GET: accept comma-separated phones via query param
            phones_param = request.args.get('phones', '')
            phones = [p.strip() for p in phones_param.split(',') if p.strip()] if phones_param else []
        else:
            data = request.get_json()
            phones = data.get('phones', []) if data else []
        room_ids = _get_agent_room_ids()
        matched = check_matched_phones(phones, room_ids=room_ids)
        return jsonify({'success': True, 'matched': matched})
    except Exception as e:
        logger.error(f"Error checking phones: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/proptalk/audio-by-phone', methods=['GET'])
@propsheet_login_required
def api_proptalk_audio_by_phone():
    """Get audio files for a specific phone number (agent 격리)"""
    try:
        from services.proptalk_service import get_audio_by_phone
        phone = request.args.get('phone', '')
        if not phone:
            return jsonify({'success': False, 'error': '전화번호가 필요합니다'}), 400
        room_ids = _get_agent_room_ids()
        audios = get_audio_by_phone(phone, room_ids=room_ids)
        return jsonify({'success': True, 'phone': phone, 'audios': audios, 'total': len(audios)})
    except Exception as e:
        logger.error(f"Error getting audio by phone: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/proptalk/rooms', methods=['GET'])
@propsheet_login_required
def api_proptalk_rooms():
    """Get Proptalk chat rooms for current user"""
    try:
        from services.proptalk_service import get_proptalk_rooms
        user_email = session.get('user_email', '')
        rooms = get_proptalk_rooms(user_email)
        return jsonify({'success': True, 'rooms': rooms})
    except Exception as e:
        logger.error(f"Error fetching Proptalk rooms: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/agent/assignees', methods=['GET'])
@propsheet_login_required
def get_assignees():
    """Get list of agent + subagent names for assignee dropdown"""
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    names = []
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get all agents
                cur.execute("SELECT name FROM agents WHERE is_active = true ORDER BY name")
                for r in cur.fetchall():
                    if r['name'] and r['name'] not in names:
                        names.append(r['name'])

                # Get all active web_users with agent/subagent role
                cur.execute("""
                    SELECT wu.name FROM web_users wu
                    WHERE wu.role IN ('agent', 'subagent') AND wu.is_active = true
                    ORDER BY wu.name
                """)
                for r in cur.fetchall():
                    if r['name'] and r['name'] not in names:
                        names.append(r['name'])
    except Exception as e:
        logger.warning(f"Could not load assignees: {e}")

    return jsonify({'success': True, 'assignees': names})


@bp.route('/api/agent/info', methods=['GET'])
@propsheet_login_required
def get_agent_info():
    """Get agent info for the current user (or their agent)"""
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            user_email = session.get('user_email')

            # Check if user is an agent directly
            cur.execute("SELECT * FROM agents WHERE email = %s AND is_active = true", (user_email,))
            agent = cur.fetchone()

            if not agent:
                # Check if user is a subagent
                cur.execute("SELECT agent_id FROM web_users WHERE email = %s AND role = 'subagent'", (user_email,))
                user = cur.fetchone()
                if user and user['agent_id']:
                    cur.execute("SELECT * FROM agents WHERE id = %s AND is_active = true", (user['agent_id'],))
                    agent = cur.fetchone()

            if agent:
                return jsonify({
                    'success': True,
                    'agent': {
                        'name': agent['name'],
                        'agency_name': agent['agency_name'],
                        'slug': agent['slug'],
                        'phone': agent['phone'],
                        'address': agent['address'],
                        'license_no': agent['license_no'],
                    }
                })

    return jsonify({'success': True, 'agent': None})




@bp.route('/api/propsheet/agents-public', methods=['GET'])
def agents_public():
    """활성 agent 목록 반환 (공개 API, 인증 불필요)"""
    from decimal import Decimal
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT slug, agency_name, name, phone, address, license_no,
                           latitude, longitude, logo_url
                    FROM agents
                    WHERE is_active = true
                    ORDER BY agency_name
                """)
                agents = []
                for row in cur.fetchall():
                    a = dict(row)
                    if a.get('latitude'):
                        a['latitude'] = float(a['latitude'])
                    if a.get('longitude'):
                        a['longitude'] = float(a['longitude'])
                    agents.append(a)
        return jsonify({'success': True, 'agents': agents, 'total': len(agents)})
    except Exception as e:
        logger.error(f"agents-public error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/propsheet/map-data', methods=['GET'])
def get_map_data():
    """PropSheet DB에서 매물 데이터를 좌표와 함께 반환 (3개 테이블: 단일/집합/부분)"""
    from decimal import Decimal
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor
    import re as _re

    def to_float(val):
        if val is None:
            return 0
        return float(val) if isinstance(val, Decimal) else (float(val) if val else 0)

    def extract_photo(raw):
        if not raw:
            return ''
        m = _re.search(r'\((/uploads/[^)]+)\)', raw)
        return m.group(1) if m else ''

    def format_price_label(transaction_type, price, deposit, monthly):
        def to_display(v):
            if not v or v <= 0:
                return '미정'
            if v >= 10000:
                eok = v / 10000
                return f"{eok:.0f}억" if eok == int(eok) else f"{eok:.1f}억"
            return f"{int(v)}만"

        if transaction_type == '월세':
            dep_str = to_display(deposit) if deposit and deposit > 0 else '0'
            mon_str = f"{int(monthly)}" if monthly and monthly > 0 else '0'
            return f"월세{dep_str}/{mon_str}"
        elif transaction_type == '전세':
            return f"전세{to_display(deposit)}"
        else:
            return f"매매{to_display(price)}"

    status_filter = request.args.get('status', '')
    types_param = request.args.get('types', 'danil,jibhap,bubun')
    txn_param = request.args.get('txn', '')
    agent_slug = request.args.get('agent_slug', '')
    valid_types = ('danil', 'jibhap', 'bubun')
    requested_types = [t.strip() for t in types_param.split(',') if t.strip() in valid_types]
    requested_txns = [t.strip() for t in txn_param.split(',') if t.strip()] if txn_param else []

    # 테이블명 결정: agent_slug=all이면 모든 활성 agent, 아니면 단일 agent
    agents_tables = []  # [(slug, {type: (table_name, db_id)})]

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if agent_slug == 'all':
                    cur.execute("""
                        SELECT a.slug as agent_slug, d.id, d.table_name, d.name, d.slug as db_slug
                        FROM databases d
                        JOIN workspaces w ON d.workspace_id = w.id
                        JOIN agents a ON w.agent_id = a.id
                        WHERE a.is_active = true AND w.slug != 'template'
                        ORDER BY a.slug, d.id
                    """)
                else:
                    resolved = agent_slug or 'goldenrabbit'
                    cur.execute("""
                        SELECT a.slug as agent_slug, d.id, d.table_name, d.name, d.slug as db_slug
                        FROM databases d
                        JOIN workspaces w ON d.workspace_id = w.id
                        JOIN agents a ON w.agent_id = a.id
                        WHERE a.slug = %s AND a.is_active = true AND w.slug != 'template'
                        ORDER BY d.id
                    """, (resolved,))

                dbs = cur.fetchall()
                agent_map = {}
                for db in dbs:
                    aslug = db['agent_slug']
                    if aslug not in agent_map:
                        agent_map[aslug] = {}
                    dslug = (db['db_slug'] or '').lower()
                    dname = (db['name'] or '').lower()
                    if dslug == 'single' or '단일' in dname:
                        agent_map[aslug]['danil'] = (db['table_name'], db['id'])
                    elif dslug == 'multi-unit' or '집합' in dname:
                        agent_map[aslug]['jibhap'] = (db['table_name'], db['id'])
                    elif dslug == 'part' or '부분' in dname:
                        agent_map[aslug]['bubun'] = (db['table_name'], db['id'])

                agents_tables = [(s, m) for s, m in agent_map.items() if m]
                if not agents_tables:
                    logger.warning(f"No property databases found for agent_slug='{agent_slug}'")
    except Exception as e:
        logger.warning(f"Failed to resolve tables: {e}")

    # Explicit column lists (SELECT * → needed columns only, ~73% data reduction)
    _DANIL_COLS = ('coordinates_lat, coordinates_lon, "지번 주소", "도로명주소", "건물명", '
                   '"매가(만원)", "토지면적(㎡)", "연면적(㎡)", "건폐율(%%)", "용적률(%%)", '
                   '"층수", "주용도", "용도지역", "현황", "사용승인일", '
                   '"보증금(만원)", "월세(만원)", "융자(만원)", "실투자금", '
                   '"융자제외수익률(%%)", "광고(자동완성)", "대표사진", "인접역", '
                   '"거리(m)", record_id, "매물종류"')
    _JIBHAP_COLS = ('coordinates_lat, coordinates_lon, "지번 주소", "도로명주소", "건물명", '
                    '"매가(만원)", "토지면적(㎡)", "대지면적(㎡)", "연면적(㎡)", '
                    '"전용면적(㎡)", "공급면적(㎡)", "건폐율(%%)", "용적률(%%)", '
                    '"총층수", "주용도", "용도지역", "현황", "사용승인일", '
                    '"보증금(만원)", "월세(만원)", "융자(만원)", '
                    '"방", "화", "호수", "물건종류", "관리비(만원)", "입주가능일", '
                    '"종류", "광고(자동완성)", "대표사진", "인접역", '
                    '"거리(m)", record_id')
    _BUBUN_COLS = ('coordinates_lat, coordinates_lon, "지번 주소", "도로명주소", "건물명", '
                   '"토지면적(㎡)", "연면적(㎡)", "전용면적", "공급면적(㎡)", '
                   '"건폐율(%%)", "용적률(%%)", '
                   '"층수", "주용도", "용도지역", "현황", "사용승인일", '
                   '"보증금(만원)", "월세(만원)", "융자(만원)", '
                   '"방", "화", "호수", "룸형태", "관리비", "입주가능일", '
                   '"종류", "광고(자동완성)", "대표사진", "인접역", '
                   '"거리(m)", record_id')

    def _safe_query(cur, cols, table, extra_where='', params=None):
        """Execute SELECT with explicit cols, fallback to SELECT * on column error."""
        base = 'SELECT ' + cols + ' FROM ' + table + ' WHERE coordinates_lat IS NOT NULL AND coordinates_lon IS NOT NULL'
        if extra_where:
            base += ' AND ' + extra_where
        try:
            cur.execute('SAVEPOINT sp_map')
            if params:
                cur.execute(base, params)
            else:
                cur.execute(base.replace('%%', '%'))
        except Exception:
            cur.execute('ROLLBACK TO SAVEPOINT sp_map')
            base_fallback = 'SELECT * FROM ' + table + ' WHERE coordinates_lat IS NOT NULL AND coordinates_lon IS NOT NULL'
            if extra_where:
                base_fallback += ' AND ' + extra_where
            if params:
                cur.execute(base_fallback, params)
            else:
                cur.execute(base_fallback.replace('%%', '%'))

    markers = []
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
              for current_slug, table_map in agents_tables:
                # === 단일부동산 ===
                if 'danil' in requested_types and 'danil' in table_map:
                    danil_table, danil_db_id = table_map['danil']
                    if not requested_txns or '매매' in requested_txns:
                        extra = '"현황" = %s' if status_filter else ''
                        p = [status_filter] if status_filter else None
                        _safe_query(cur, _DANIL_COLS, danil_table, extra, p)

                        for row in cur.fetchall():
                            price = to_float(row.get('매가(만원)'))
                            markers.append({
                                'lat': to_float(row['coordinates_lat']),
                                'lon': to_float(row['coordinates_lon']),
                                'address': row.get('지번 주소', ''),
                                'road_address': row.get('도로명주소', '') or '',
                                'building_name': row.get('건물명', '') or '',
                                'price': price,
                                'land_area': to_float(row.get('토지면적(㎡)')),
                                'total_area': to_float(row.get('연면적(㎡)')),
                                'bcr': to_float(row.get('건폐율(%)')),
                                'far': to_float(row.get('용적률(%)')),
                                'floors': row.get('층수', '') or '',
                                'usage': row.get('주용도', '') or '',
                                'zoning': row.get('용도지역', '') or '',
                                'status': row.get('현황', '') or '',
                                'approval_date': str(row.get('사용승인일', '') or ''),
                                'deposit': to_float(row.get('보증금(만원)')),
                                'rent': to_float(row.get('월세(만원)')),
                                'loan': to_float(row.get('융자(만원)')),
                                'investment': to_float(row.get('실투자금')),
                                'yield_rate': to_float(row.get('융자제외수익률(%)')),
                                'description': row.get('광고(자동완성)', '') or '',
                                'photo': extract_photo(row.get('대표사진', '')),
                                'station': row.get('인접역', '') or '',
                                'distance': to_float(row.get('거리(m)')),
                                'record_id': row.get('record_id', ''),
                                'property_type': 'danil',
                                'property_subtype': row.get('매물종류', '') or '',
                                'transaction_type': '매매',
                                'agent_slug': current_slug,
                                'db_id': danil_db_id,
                                'price_label': format_price_label('매매', price, 0, 0),
                            })

                # === 집합부동산 ===
                if 'jibhap' in requested_types and 'jibhap' in table_map:
                    jibhap_table, jibhap_db_id = table_map['jibhap']
                    extra = '"현황" = %s' if status_filter else ''
                    p = [status_filter] if status_filter else None
                    _safe_query(cur, _JIBHAP_COLS, jibhap_table, extra, p)

                    for row in cur.fetchall():
                        kind = (row.get('종류', '') or '').strip()
                        txn = '전세' if kind == '전세' else ('월세' if kind == '월세' else '매매')
                        if requested_txns and txn not in requested_txns:
                            continue
                        price = to_float(row.get('매가(만원)'))
                        deposit = to_float(row.get('보증금(만원)'))
                        monthly = to_float(row.get('월세(만원)'))
                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'address': row.get('지번 주소', ''),
                            'road_address': row.get('도로명주소', '') or '',
                            'building_name': row.get('건물명', '') or '',
                            'price': price,
                            'land_area': to_float(row.get('토지면적(㎡)') or row.get('대지면적(㎡)')),
                            'total_area': to_float(row.get('연면적(㎡)')),
                            'exclusive_area': to_float(row.get('전용면적(㎡)')),
                            'supply_area': to_float(row.get('공급면적(㎡)')),
                            'bcr': to_float(row.get('건폐율(%)')),
                            'far': to_float(row.get('용적률(%)')),
                            'floors': row.get('층수', '') or row.get('총층수', '') or '',
                            'usage': row.get('주용도', '') or '',
                            'zoning': row.get('용도지역', '') or '',
                            'status': row.get('현황', '') or '',
                            'approval_date': str(row.get('사용승인일', '') or ''),
                            'deposit': deposit,
                            'rent': monthly,
                            'loan': to_float(row.get('융자(만원)')),
                            'rooms': to_float(row.get('방')),
                            'bathrooms': to_float(row.get('화')),
                            'unit_no': row.get('호수', '') or '',
                            'property_subtype': row.get('물건종류', '') or '',
                            'maintenance_fee': to_float(row.get('관리비(만원)')),
                            'move_in_date': row.get('입주가능일', '') or '',
                            'description': row.get('광고(자동완성)', '') or '',
                            'photo': extract_photo(row.get('대표사진', '')),
                            'station': row.get('인접역', '') or '',
                            'distance': to_float(row.get('거리(m)')),
                            'record_id': row.get('record_id', ''),
                            'property_type': 'jibhap',
                            'transaction_type': txn,
                            'agent_slug': current_slug,
                            'db_id': jibhap_db_id,
                            'price_label': format_price_label(txn, price, deposit, monthly),
                        })

                # === 부분부동산 ===
                if 'bubun' in requested_types and 'bubun' in table_map:
                    bubun_table, bubun_db_id = table_map['bubun']
                    extra = '"현황" = %s' if status_filter else ''
                    p = [status_filter] if status_filter else None
                    _safe_query(cur, _BUBUN_COLS, bubun_table, extra, p)

                    for row in cur.fetchall():
                        kind = (row.get('종류', '') or '').strip()
                        txn = '전세' if kind == '전세' else ('월세' if kind == '월세' else '매매')
                        if requested_txns and txn not in requested_txns:
                            continue
                        deposit = to_float(row.get('보증금(만원)'))
                        monthly = to_float(row.get('월세(만원)'))
                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'address': row.get('지번 주소', ''),
                            'road_address': row.get('도로명주소', '') or '',
                            'building_name': row.get('건물명', '') or '',
                            'price': 0,
                            'land_area': to_float(row.get('토지면적(㎡)')),
                            'total_area': to_float(row.get('연면적(㎡)')),
                            'exclusive_area': to_float(row.get('전용면적')),
                            'supply_area': to_float(row.get('공급면적(㎡)')),
                            'bcr': to_float(row.get('건폐율(%)')),
                            'far': to_float(row.get('용적률(%)')),
                            'floors': row.get('층수', '') or '',
                            'usage': row.get('주용도', '') or '',
                            'zoning': row.get('용도지역', '') or '',
                            'status': row.get('현황', '') or '',
                            'approval_date': str(row.get('사용승인일', '') or ''),
                            'deposit': deposit,
                            'rent': monthly,
                            'loan': to_float(row.get('융자(만원)')),
                            'rooms': to_float(row.get('방')),
                            'bathrooms': to_float(row.get('화')),
                            'unit_no': row.get('호수', '') or '',
                            'property_subtype': row.get('룸형태', '') or '',
                            'room_type': row.get('룸형태', '') or '',
                            'maintenance_fee': to_float(row.get('관리비')),
                            'move_in_date': row.get('입주가능일', '') or '',
                            'description': row.get('광고(자동완성)', '') or '',
                            'photo': extract_photo(row.get('대표사진', '')),
                            'station': row.get('인접역', '') or '',
                            'distance': to_float(row.get('거리(m)')),
                            'record_id': row.get('record_id', ''),
                            'property_type': 'bubun',
                            'transaction_type': txn,
                            'agent_slug': current_slug,
                            'db_id': bubun_db_id,
                            'price_label': format_price_label(txn, 0, deposit, monthly),
                        })

    except Exception as e:
        import traceback
        logger.error(f"map-data 조회 실패: {e}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

    # 에이전트 정보
    agents_info = []
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if agent_slug == 'all':
                    cur.execute(
                        'SELECT a.name, a.agency_name, a.phone, a.address, '
                        'a.license_no, a.slug, a.latitude, a.longitude, a.logo_url '
                        'FROM agents a WHERE a.is_active = true ORDER BY a.agency_name'
                    )
                else:
                    resolved = agent_slug or 'goldenrabbit'
                    cur.execute(
                        'SELECT a.name, a.agency_name, a.phone, a.address, '
                        'a.license_no, a.slug, a.latitude, a.longitude, a.logo_url '
                        'FROM agents a WHERE a.slug = %s AND a.is_active = true LIMIT 1',
                        (resolved,)
                    )
                for row in cur.fetchall():
                    a = dict(row)
                    if a.get('latitude'):
                        a['latitude'] = float(a['latitude'])
                    if a.get('longitude'):
                        a['longitude'] = float(a['longitude'])
                    agents_info.append(a)
    except Exception:
        pass

    result = {'success': True, 'markers': markers, 'total': len(markers)}
    if agent_slug == 'all':
        result['agents'] = agents_info
    else:
        result['agent'] = agents_info[0] if agents_info else None
    return jsonify(result)





@bp.route("/api/propsheet/category-properties", methods=["GET"])
def category_properties():
    """PropSheet DB view-based category properties (no auth required)"""
    import re as _re
    import json as _json
    from decimal import Decimal
    from services.database_service import get_db_connection, list_properties
    from services.view_service import get_view
    from psycopg2.extras import RealDictCursor

    view_id = request.args.get("view_id", type=int)
    if not view_id:
        return jsonify({"error": "view_id parameter is required"}), 400

    # 1. Load view config
    view = get_view(view_id)
    if not view:
        return jsonify({"error": "View not found"}), 404

    database_id = view["database_id"]

    # Get table name
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT table_name FROM databases WHERE id = %s", (database_id,))
                db_row = cur.fetchone()
                if not db_row:
                    return jsonify({"error": "Database not found"}), 404
                table_name = db_row["table_name"]
    except Exception as e:
        logger.error(f"category-properties DB lookup failed: {e}")
        return jsonify({"error": str(e)}), 500

    # 2. Extract filter/sort from view
    filter_config = view.get("filter_config") or []
    if isinstance(filter_config, str):
        filter_config = _json.loads(filter_config)

    sort_config = view.get("sort_config") or {}
    if isinstance(sort_config, str):
        sort_config = _json.loads(sort_config)

    sort_by = sort_config.get("sort_by", "레코드생성일자")
    sort_order = sort_config.get("sort_order", "desc")

    # 3. Query via list_properties (no pagination)
    try:
        result = list_properties(
            database_id=database_id,
            page=1,
            per_page=9999,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filter_config,
            table_name=table_name,
            filter_logic="and"
        )
    except Exception as e:
        logger.error(f"category-properties query failed: {e}")
        return jsonify({"error": str(e)}), 500

    items = result.get("items", [])

    # 4. Convert to Airtable-compatible format
    def to_serializable(val):
        if val is None:
            return None
        if isinstance(val, Decimal):
            return float(val)
        if hasattr(val, "isoformat"):
            return val.isoformat()
        return val

    records = []
    for row in items:
        record_id = row.get("record_id") or str(row.get("id", ""))

        # Extract photo URL (same pattern as map-data API)
        photo_url = ""
        photo_raw = str(row.get("대표사진", "") or "")
        if photo_raw:
            m = _re.search(r'\(/uploads/[^)\s]+\)', photo_raw)
            if m:
                photo_url = m.group(0)[1:-1]  # Remove surrounding parentheses

        fields = {}
        skip_keys = {"id", "database_id", "record_id", "created_at", "updated_at",
                      "fields_hash", "synced_at", "airtable_id"}
        for k, v in row.items():
            if k in skip_keys:
                continue
            if k == "대표사진":
                fields[k] = [{"url": photo_url}] if photo_url else None
            else:
                fields[k] = to_serializable(v)

        records.append({"id": record_id, "fields": fields})

    return jsonify({
        "records": records,
        "view_id": str(view_id),
        "total_count": len(records),
        "source": "propsheet_db"
    })


@bp.route('/api/propsheet/search-map', methods=['POST'])
def search_map_db():
    """PropSheet DB 기반 매물 검색 (3개 테이블 지원)"""
    from decimal import Decimal
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor
    import html as html_module

    def to_float(val):
        if val is None:
            return 0
        return float(val) if isinstance(val, Decimal) else (float(val) if val else 0)

    search = request.json or {}
    property_type = search.get('property_type', 'danil')
    search_agent_slug = search.get('agent_slug', 'goldenrabbit')

    # databases 테이블에서 agent_slug 기반 동적 조회
    _slug_to_type = {'single': 'danil', 'multi-unit': 'jibhap', 'part': 'bubun'}
    _type_to_slug = {'danil': 'single', 'jibhap': 'multi-unit', 'bubun': 'part'}
    target_db_slug = _type_to_slug.get(property_type, 'single')

    table_name = None
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT d.table_name FROM databases d
                    JOIN workspaces w ON d.workspace_id = w.id
                    JOIN agents a ON w.agent_id = a.id
                    WHERE a.slug = %s AND d.slug = %s AND a.is_active = true
                      AND w.slug != 'template'
                    LIMIT 1
                """, (search_agent_slug, target_db_slug))
                row = cur.fetchone()
                if row:
                    table_name = row['table_name']
    except Exception as e:
        logger.warning(f"search-map table lookup failed: {e}")

    if not table_name:
        return jsonify({'markers': [], 'total': 0})
    markers = []

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                conditions = [
                    'coordinates_lat IS NOT NULL',
                    'coordinates_lon IS NOT NULL',
                    '"현황" = %s'
                ]
                params = ['등록']

                if property_type == 'danil':
                    price_val = search.get('price_value', '').strip()
                    price_cond = search.get('price_condition', 'all')
                    if price_val and price_cond != 'all':
                        op = '>= %s' if price_cond == 'above' else '<= %s'
                        conditions.append('"매가(만원)" ' + op)
                        params.append(float(price_val))

                    inv_val = search.get('investment_value', '').strip()
                    inv_cond = search.get('investment_condition', 'all')
                    if inv_val and inv_cond != 'all':
                        op = '>= %s' if inv_cond == 'above' else '<= %s'
                        conditions.append('"실투자금" ' + op)
                        params.append(float(inv_val))

                    yield_val = search.get('yield_value', '').strip()
                    yield_cond = search.get('yield_condition', 'all')
                    if yield_val and yield_cond != 'all':
                        op = '>= %s' if yield_cond == 'above' else '<= %s'
                        conditions.append('"융자제외수익률(%%)" ' + op)
                        params.append(float(yield_val))

                    area_val = search.get('area_value', '').strip()
                    area_cond = search.get('area_condition', 'all')
                    if area_val and area_cond != 'all':
                        op = '>= %s' if area_cond == 'above' else '<= %s'
                        conditions.append('"토지면적(㎡)" ' + op)
                        params.append(float(area_val))

                    subtype_vals = search.get('subtype_values', [])
                    subtype_val = search.get('subtype_value', '').strip()
                    if subtype_vals:
                        ph = ','.join(['%s'] * len(subtype_vals))
                        conditions.append('"매물종류" IN (' + ph + ')')
                        params.extend(subtype_vals)
                    elif subtype_val:
                        conditions.append('"매물종류" = %s')
                        params.append(subtype_val)

                    query = (
                        'SELECT "지번 주소", "매가(만원)", "토지면적(㎡)", "층수", "주용도", "매물종류",'
                        ' "record_id", coordinates_lat, coordinates_lon'
                        ' FROM ' + table_name +
                        ' WHERE ' + ' AND '.join(conditions)
                    )

                elif property_type == 'jibhap':
                    price_val = search.get('price_value', '').strip()
                    price_cond = search.get('price_condition', 'all')
                    if price_val and price_cond != 'all':
                        op = '>= %s' if price_cond == 'above' else '<= %s'
                        conditions.append('"매가(만원)" ' + op)
                        params.append(float(price_val))

                    dep_val = search.get('deposit_value', '').strip()
                    dep_cond = search.get('deposit_condition', 'all')
                    if dep_val and dep_cond != 'all':
                        op = '>= %s' if dep_cond == 'above' else '<= %s'
                        conditions.append('"보증금(만원)" ' + op)
                        params.append(float(dep_val))

                    rent_val = search.get('rent_value', '').strip()
                    rent_cond = search.get('rent_condition', 'all')
                    if rent_val and rent_cond != 'all':
                        op = '>= %s' if rent_cond == 'above' else '<= %s'
                        conditions.append('"월세(만원)" ' + op)
                        params.append(float(rent_val))

                    area_val = search.get('exclusive_area_value', '').strip()
                    area_cond = search.get('exclusive_area_condition', 'all')
                    if area_val and area_cond != 'all':
                        op = '>= %s' if area_cond == 'above' else '<= %s'
                        conditions.append('"전용면적(㎡)" ' + op)
                        params.append(float(area_val))

                    rooms_val = search.get('rooms_value', '').strip()
                    rooms_cond = search.get('rooms_condition', 'all')
                    if rooms_val and rooms_cond != 'all':
                        op = '>= %s' if rooms_cond == 'above' else '<= %s'
                        conditions.append('"방" ' + op)
                        params.append(float(rooms_val))

                    subtype_vals = search.get('subtype_values', [])
                    subtype_val = search.get('subtype_value', '').strip()
                    if subtype_vals:
                        ph = ','.join(['%s'] * len(subtype_vals))
                        conditions.append('"물건종류" IN (' + ph + ')')
                        params.extend(subtype_vals)
                    elif subtype_val:
                        conditions.append('"물건종류" = %s')
                        params.append(subtype_val)

                    query = (
                        'SELECT "지번 주소", "매가(만원)", "보증금(만원)", "월세(만원)",'
                        ' "전용면적(㎡)", "종류", "방", "물건종류",'
                        ' "record_id", coordinates_lat, coordinates_lon'
                        ' FROM ' + table_name +
                        ' WHERE ' + ' AND '.join(conditions)
                    )

                else:  # bubun
                    dep_val = search.get('deposit_value', '').strip()
                    dep_cond = search.get('deposit_condition', 'all')
                    if dep_val and dep_cond != 'all':
                        op = '>= %s' if dep_cond == 'above' else '<= %s'
                        conditions.append('"보증금(만원)" ' + op)
                        params.append(float(dep_val))

                    rent_val = search.get('rent_value', '').strip()
                    rent_cond = search.get('rent_condition', 'all')
                    if rent_val and rent_cond != 'all':
                        op = '>= %s' if rent_cond == 'above' else '<= %s'
                        conditions.append('"월세(만원)" ' + op)
                        params.append(float(rent_val))

                    area_val = search.get('exclusive_area_value', '').strip()
                    area_cond = search.get('exclusive_area_condition', 'all')
                    if area_val and area_cond != 'all':
                        op = '>= %s' if area_cond == 'above' else '<= %s'
                        conditions.append('"전용면적" ' + op)
                        params.append(float(area_val))

                    subtype_vals = search.get('subtype_values', [])
                    subtype_val = search.get('subtype_value', '').strip()
                    if subtype_vals:
                        ph = ','.join(['%s'] * len(subtype_vals))
                        conditions.append('"룸형태" IN (' + ph + ')')
                        params.extend(subtype_vals)
                    elif subtype_val:
                        conditions.append('"룸형태" = %s')
                        params.append(subtype_val)

                    rooms_val = search.get('rooms_value', '').strip()
                    rooms_cond = search.get('rooms_condition', 'all')
                    if rooms_val and rooms_cond != 'all':
                        op = '>= %s' if rooms_cond == 'above' else '<= %s'
                        conditions.append('"방" ' + op)
                        params.append(float(rooms_val))

                    query = (
                        'SELECT "지번 주소", "보증금(만원)", "월세(만원)",'
                        ' "전용면적", "종류", "룸형태", "방",'
                        ' "record_id", coordinates_lat, coordinates_lon'
                        ' FROM ' + table_name +
                        ' WHERE ' + ' AND '.join(conditions)
                    )

                cur.execute(query, params)

                for row in cur.fetchall():
                    address = row.get('지번 주소', '') or ''
                    record_id = row.get('record_id', '')
                    addr_esc = html_module.escape(address, quote=True)

                    if property_type == 'danil':
                        price_num = to_float(row.get('매가(만원)'))
                        price_eok = price_num / 10000
                        if price_eok >= 1:
                            price_display = f"{price_eok:.1f}억원"
                        else:
                            price_display = f"{price_num:.0f}만원" if price_num else "가격미정"
                        land_area = to_float(row.get('토지면적(㎡)'))
                        land_pyeong = land_area / 3.3058 if land_area else 0
                        land_str = f"{land_pyeong:.0f}평 ({land_area:.1f}㎡)" if land_area else "면적미정"
                        floors = str(row.get('층수', '') or '')
                        usage = str(row.get('주용도', '') or '')
                        popup = (
                            '<button class="close-btn">&times;</button>'
                            + f'<div class="address">{addr_esc}</div>'
                            + f'<div class="info-row">매가: {price_display}</div>'
                            + f'<div class="info-row">토지: {land_str}</div>'
                            + f'<div class="info-row">층수: {html_module.escape(floors)}</div>'
                            + f'<div class="info-row">용도: {html_module.escape(usage)}</div>'
                            + f'<button class="btn-detail" data-record="{record_id}">상세내역보기</button>'
                            + f'<button class="btn-consult" data-address="{addr_esc}">이 매물 문의하기</button>'
                        )
                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'price': price_num,
                            'price_display': price_display,
                            'popup': popup,
                            'record_id': record_id,
                            'address': address,
                            'property_type': 'danil',
                            'transaction_type': '매매',
                            'db_id': 39,
                        })
                    elif property_type == 'jibhap':
                        kind = (row.get('종류', '') or '').strip()
                        txn = '전세' if kind == '전세' else ('월세' if kind == '월세' else '매매')
                        price_num = to_float(row.get('매가(만원)'))
                        deposit = to_float(row.get('보증금(만원)'))
                        monthly = to_float(row.get('월세(만원)'))
                        excl = to_float(row.get('전용면적(㎡)'))
                        rooms = to_float(row.get('방'))
                        if txn == '월세':
                            pd = f"월세 {deposit:.0f}/{monthly:.0f}만"
                        elif txn == '전세':
                            pd = f"전세 {deposit/10000:.1f}억" if deposit >= 10000 else f"전세 {deposit:.0f}만"
                        else:
                            pe = price_num / 10000
                            pd = f"매매 {pe:.1f}억" if pe >= 1 else (f"매매 {price_num:.0f}만" if price_num else "가격미정")
                        excl_str = f"{excl/3.3058:.0f}평 ({excl:.1f}㎡)" if excl else ""
                        popup = (
                            '<button class="close-btn">&times;</button>'
                            + f'<div class="address">{addr_esc}</div>'
                            + f'<div class="info-row">{pd}</div>'
                            + (f'<div class="info-row">전용: {excl_str}</div>' if excl_str else '')
                            + (f'<div class="info-row">방: {int(rooms)}개</div>' if rooms else '')
                            + f'<button class="btn-detail" data-record="{record_id}">상세내역보기</button>'
                            + f'<button class="btn-consult" data-address="{addr_esc}">이 매물 문의하기</button>'
                        )
                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'price': price_num or deposit,
                            'price_display': pd,
                            'popup': popup,
                            'record_id': record_id,
                            'address': address,
                            'property_type': 'jibhap',
                            'transaction_type': txn,
                            'db_id': 38,
                        })
                    else:  # bubun
                        kind = (row.get('종류', '') or '').strip()
                        txn = '전세' if kind == '전세' else ('월세' if kind == '월세' else '매매')
                        deposit = to_float(row.get('보증금(만원)'))
                        monthly = to_float(row.get('월세(만원)'))
                        excl = to_float(row.get('전용면적'))
                        rooms = to_float(row.get('방'))
                        subtype = row.get('룸형태', '') or ''
                        if txn == '월세':
                            pd = f"월세 {deposit:.0f}/{monthly:.0f}만"
                        elif txn == '전세':
                            pd = f"전세 {deposit/10000:.1f}억" if deposit >= 10000 else f"전세 {deposit:.0f}만"
                        else:
                            pd = "매매"
                        excl_str = f"{excl/3.3058:.0f}평 ({excl:.1f}㎡)" if excl else ""
                        popup = (
                            '<button class="close-btn">&times;</button>'
                            + f'<div class="address">{addr_esc}</div>'
                            + f'<div class="info-row">{pd}</div>'
                            + (f'<div class="info-row">전용: {excl_str}</div>' if excl_str else '')
                            + (f'<div class="info-row">종류: {html_module.escape(subtype)}</div>' if subtype else '')
                            + (f'<div class="info-row">방: {int(rooms)}개</div>' if rooms else '')
                            + f'<button class="btn-detail" data-record="{record_id}">상세내역보기</button>'
                            + f'<button class="btn-consult" data-address="{addr_esc}">이 매물 문의하기</button>'
                        )
                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'price': deposit,
                            'price_display': pd,
                            'popup': popup,
                            'record_id': record_id,
                            'address': address,
                            'property_type': 'bubun',
                            'transaction_type': txn,
                            'db_id': 43,
                        })

    except Exception as e:
        import traceback
        logger.error(f"search-map DB 조회 실패: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

    import json as json_module
    kakao_key = import_kakao_key()
    map_html = _generate_search_map_html(kakao_key, markers)

    return jsonify({
        'map_html': map_html,
        'markers': markers,
        'count': len(markers),
        'statistics': {
            'markers_added': len(markers),
            'source': 'propsheet_db',
            'property_type': property_type
        }
    })



def import_kakao_key():
    import os
    return os.environ.get("KAKAO_JAVASCRIPT_KEY", "")


def _generate_search_map_html(kakao_key, markers_data):
    """검색 결과 카카오맵 HTML 생성"""
    import json as json_module
    markers_json = json_module.dumps(markers_data, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={kakao_key}&autoload=false"></script>
    <style>
        html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
        #map {{ width: 100%; height: 100%; }}
        .price-marker {{
            border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            padding: 3px 8px; font-size: 11px; font-weight: bold; color: white;
            white-space: nowrap; text-align: center; position: relative;
            cursor: pointer; transition: all 0.15s; font-family: -apple-system, sans-serif;
        }}
        .price-marker:hover {{ transform: scale(1.1); z-index: 5; }}
        .price-marker::after {{
            content: ''; position: absolute; bottom: -7px; left: 50%; margin-left: -5px;
            width: 0; height: 0; border-left: 5px solid transparent;
            border-right: 5px solid transparent;
        }}
        .price-marker.danil-매매 {{ background: #1D4ED8; }}
        .price-marker.danil-매매::after {{ border-top: 7px solid #1D4ED8; }}
        .price-marker.jibhap-매매 {{ background: #15803D; }}
        .price-marker.jibhap-매매::after {{ border-top: 7px solid #15803D; }}
        .price-marker.jibhap-전세 {{ background: #22C55E; }}
        .price-marker.jibhap-전세::after {{ border-top: 7px solid #22C55E; }}
        .price-marker.jibhap-월세 {{ background: #86EFAC; color: #14532d; }}
        .price-marker.jibhap-월세::after {{ border-top: 7px solid #86EFAC; }}
        .price-marker.bubun-매매 {{ background: #C2410C; }}
        .price-marker.bubun-매매::after {{ border-top: 7px solid #C2410C; }}
        .price-marker.bubun-전세 {{ background: #EA580C; }}
        .price-marker.bubun-전세::after {{ border-top: 7px solid #EA580C; }}
        .price-marker.bubun-월세 {{ background: #FB923C; color: #431407; }}
        .price-marker.bubun-월세::after {{ border-top: 7px solid #FB923C; }}
        .map-type-control {{
            position: absolute; top: 8px; right: 8px; z-index: 1000; display: flex;
            gap: 2px; background: white; border-radius: 6px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.2); padding: 3px;
        }}
        .map-type-btn {{
            padding: 4px 10px; border: none; background: white; cursor: pointer;
            font-size: 11px; font-weight: 600; border-radius: 4px; transition: background 0.2s;
            font-family: -apple-system, sans-serif;
        }}
        .map-type-btn:hover {{ background: #f0f0f0; }}
        .map-type-btn.active {{ background: #e38000; color: white; }}
        .info-popup {{
            position: relative; background: #fff; border-radius: 10px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.2); padding: 10px 12px;
            min-width: 170px; max-width: 210px; font-family: -apple-system, sans-serif;
        }}
        .info-popup .close-btn {{
            position: absolute; top: 6px; right: 8px; font-size: 15px; color: #999;
            cursor: pointer; border: none; background: none; padding: 2px; line-height: 1;
        }}
        .info-popup .close-btn:hover {{ color: #333; }}
        .info-popup .address {{ font-size: 11px; font-weight: 700; margin-bottom: 6px; padding-right: 20px; color: #333; }}
        .info-popup .info-row {{ font-size: 11px; color: #555; margin: 2px 0; }}
        .info-popup .btn-detail {{
            display: block; margin-top: 8px; padding: 6px; background: #f5f5f5;
            text-align: center; font-weight: 700; color: #e38000; border-radius: 6px;
            border: none; cursor: pointer; font-size: 11px; width: 100%%; box-sizing: border-box;
        }}
        .info-popup .btn-detail:hover {{ background: #fef3e0; }}
        .info-popup .btn-consult {{
            display: block; margin-top: 4px; padding: 6px; background: #2962FF; color: white;
            text-align: center; font-weight: 700; border-radius: 6px; border: none;
            cursor: pointer; font-size: 11px; width: 100%%; box-sizing: border-box;
        }}
        .info-popup .btn-consult:hover {{ background: #1e4fcc; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="map-type-control">
        <button class="map-type-btn active" data-type="roadmap">지도</button>
        <button class="map-type-btn" data-type="skyview">위성</button>
        <button class="map-type-btn" data-type="hybrid">중첩</button>
    </div>
    <script>
        var markersData = {markers_json};
        kakao.maps.load(function() {{
            var container = document.getElementById('map');
            var options = {{ center: new kakao.maps.LatLng(37.4834, 126.9702), level: 8 }};
            var map = new kakao.maps.Map(container, options);
            var bounds = new kakao.maps.LatLngBounds();
            var currentPopup = null;
            function closePopup() {{ if (currentPopup) {{ currentPopup.setMap(null); currentPopup = null; }} }}
            function panToBottom(pos) {{
                var node = map.getNode(); var h = node.offsetHeight;
                var sw = map.getBounds().getSouthWest(); var ne = map.getBounds().getNorthEast();
                var latPerPx = (ne.getLat() - sw.getLat()) / h;
                var offsetLat = latPerPx * h * 0.25;
                map.panTo(new kakao.maps.LatLng(pos.getLat() + offsetLat, pos.getLng()));
            }}
            markersData.forEach(function(m) {{
                var position = new kakao.maps.LatLng(m.lat, m.lon);
                bounds.extend(position);
                var el = document.createElement('div');
                el.className = 'price-marker ' + (m.property_type || 'danil') + '-' + (m.transaction_type || '매매'); el.textContent = m.price_display;
                el.addEventListener('click', function(e) {{
                    e.stopPropagation(); closePopup();
                    var popupEl = document.createElement('div');
                    popupEl.className = 'info-popup'; popupEl.innerHTML = m.popup;
                    var closeBtn = popupEl.querySelector('.close-btn');
                    if (closeBtn) {{ closeBtn.onclick = function() {{ closePopup(); }}; }}
                    var detailBtn = popupEl.querySelector('.btn-detail');
                    if (detailBtn) {{ detailBtn.onclick = function(e) {{
                        e.preventDefault(); e.stopPropagation();
                        parent.postMessage({{action: 'openPropertyDetail', recordId: m.record_id, dbId: m.db_id}}, '*');
                    }}; }}
                    var consultBtn = popupEl.querySelector('.btn-consult');
                    if (consultBtn) {{ consultBtn.onclick = function(e) {{
                        e.preventDefault(); e.stopPropagation();
                        parent.postMessage({{action: 'openConsultModal', address: m.address || ''}}, '*');
                    }}; }}
                    var popup = new kakao.maps.CustomOverlay({{
                        position: position, content: popupEl, yAnchor: 1.4, xAnchor: 0.5,
                        zIndex: 10, clickable: true
                    }});
                    popup.setMap(map); currentPopup = popup; panToBottom(position);
                }});
                var overlay = new kakao.maps.CustomOverlay({{ position: position, content: el, yAnchor: 1.3, zIndex: 1 }});
                overlay.setMap(map);
            }});
            kakao.maps.event.addListener(map, 'click', function() {{ closePopup(); }});
            if (markersData.length > 0) {{ map.setBounds(bounds); }}
            var btns = document.querySelectorAll('.map-type-btn');
            btns.forEach(function(btn) {{
                btn.addEventListener('click', function() {{
                    var type = this.getAttribute('data-type');
                    if (type === 'roadmap') map.setMapTypeId(kakao.maps.MapTypeId.ROADMAP);
                    else if (type === 'skyview') map.setMapTypeId(kakao.maps.MapTypeId.SKYVIEW);
                    else if (type === 'hybrid') map.setMapTypeId(kakao.maps.MapTypeId.HYBRID);
                    btns.forEach(function(b) {{ b.classList.remove('active'); }});
                    this.classList.add('active');
                }});
            }});
        }});
    </script>
</body>
</html>"""


@bp.route('/api/propsheet/property-detail', methods=['GET'])
def get_property_detail():
    """PropSheet DB에서 매물 상세 정보 반환 (3개 테이블 지원)"""
    from decimal import Decimal
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor
    import re as _re

    record_id = request.args.get('id', '')
    db_id = request.args.get('db_id', '')

    if not record_id:
        return jsonify({'error': 'record_id 필수'}), 400
    if not db_id:
        return jsonify({'error': 'db_id 필수'}), 400

    # databases 테이블에서 동적으로 table_name 조회 (agent 격리)
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT table_name, slug as db_slug FROM databases WHERE id = %s", (db_id,))
                db_row = cur.fetchone()
                if not db_row:
                    return jsonify({'error': '데이터베이스를 찾을 수 없습니다.'}), 404
                table_name = db_row['table_name']
                _db_slug = db_row.get('db_slug', '')
    except Exception as e:
        return jsonify({'error': f'DB 조회 실패: {e}'}), 500

    def to_float(val):
        if val is None:
            return 0
        return float(val) if isinstance(val, Decimal) else (float(val) if val else 0)

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f'SELECT * FROM {table_name} WHERE "record_id" = %s LIMIT 1',
                    (record_id,)
                )
                row = cur.fetchone()
                if not row:
                    return jsonify({'error': '매물을 찾을 수 없습니다.'}), 404

                photo_url = ''
                photo_raw = row.get('대표사진', '') or ''
                if photo_raw:
                    m = _re.search(r'\((/uploads/[^)]+)\)', photo_raw)
                    if m:
                        photo_url = m.group(1)

                kind = (row.get('종류', '') or '').strip()
                if kind == '전세':
                    txn = '전세'
                elif kind == '월세':
                    txn = '월세'
                else:
                    txn = '매매'

                if _db_slug == 'multi-unit':
                    prop_type = 'jibhap'
                elif _db_slug == 'part':
                    prop_type = 'bubun'
                else:
                    prop_type = 'danil'

                property_data = {
                    'address': row.get('지번 주소', '') or '',
                    'road_address': row.get('도로명주소', '') or '',
                    'building_name': row.get('건물명', '') or '',
                    'price': to_float(row.get('매가(만원)')),
                    'land_area': to_float(row.get('토지면적(㎡)')),
                    'total_area': to_float(row.get('연면적(㎡)')),
                    'bcr': to_float(row.get('건폐율(%)')),
                    'far': to_float(row.get('용적률(%)')),
                    'floors': row.get('층수', '') or row.get('총층수', '') or '',
                    'usage': row.get('주용도', '') or '',
                    'zoning': row.get('용도지역', '') or '',
                    'status': row.get('현황', '') or '',
                    'approval_date': str(row.get('사용승인일', '') or ''),
                    'deposit': to_float(row.get('보증금(만원)')),
                    'rent': to_float(row.get('월세(만원)')),
                    'loan': to_float(row.get('융자(만원)')),
                    'investment': to_float(row.get('실투자금')),
                    'yield_rate': to_float(row.get('융자제외수익률(%)')),
                    'description': row.get('광고(자동완성)', '') or '',
                    'photo': photo_url,
                    'station': row.get('인접역', '') or '',
                    'distance': to_float(row.get('거리(m)')),
                    'record_id': record_id,
                    'property_type': prop_type,
                    'transaction_type': txn,
                    'db_id': int(db_id),
                    'exclusive_area': to_float(row.get('전용면적(㎡)') or row.get('전용면적')),
                    'supply_area': to_float(row.get('공급면적(㎡)')),
                    'rooms': to_float(row.get('방')),
                    'bathrooms': to_float(row.get('화')),
                    'unit_no': row.get('호수', '') or '',
                    'property_subtype': row.get('물건종류', '') or '',
                    'room_type': row.get('룸형태', '') or '',
                    'maintenance_fee': to_float(row.get('관리비(만원)') or row.get('관리비')),
                    'move_in_date': row.get('입주가능일', '') or '',
                    'lat': to_float(row.get('coordinates_lat')),
                    'lon': to_float(row.get('coordinates_lon')),
                }

        agent = None
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        'SELECT a.name, a.agency_name, a.phone, a.address, a.license_no, a.slug '
                        'FROM agents a '
                        'JOIN workspaces w ON w.agent_id = a.id '
                        'JOIN databases d ON d.workspace_id = w.id '
                        'WHERE d.id = %s AND a.is_active = true LIMIT 1',
                        (db_id,)
                    )
                    r = cur.fetchone()
                    if r:
                        agent = dict(r)
        except Exception:
            pass

        return jsonify({'success': True, 'property': property_data, 'agent': agent})

    except Exception as e:
        import traceback
        logger.error(f"property-detail 조회 실패: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# ========================================
# Agent Slug 멀티테넌트 라우트 (Phase 2)
# /propsheet/<agent_slug>/ → agent의 기본 WS DB 목록
# /propsheet/<agent_slug>/<db_slug> → 기본 WS의 특정 DB
# /propsheet/<agent_slug>/w/<ws_slug>/<db_slug> → 추가 WS의 특정 DB
# ========================================

# 기존 라우트와 충돌하지 않는 예약어 목록
_RESERVED_SLUGS = {
    'workspaces', 'workspace', 'api', 'legacy', 'share', 'static',
    'health', 'oauth', 'login', 'logout', 'callback', 'guide',
}


def _resolve_agent(slug):
    """Resolve agent_slug to agent record. Returns dict or None."""
    if slug in _RESERVED_SLUGS:
        return None
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM agents WHERE slug = %s AND is_active = true",
                    (slug,)
                )
                return cur.fetchone()
    except Exception as e:
        logger.error(f"_resolve_agent error: {e}")
        return None


def _get_agent_default_workspace(agent_id):
    """Get the default (first) workspace for an agent."""
    from services.database_service import get_db_connection
    from psycopg2.extras import RealDictCursor
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT w.*, json_agg(
                    json_build_object('id', d.id, 'name', d.name, 'slug', d.slug,
                        'icon', d.icon, 'color', d.color, 'description', d.description,
                        'table_name', d.table_name)
                    ORDER BY d.display_order, d.id
                ) FILTER (WHERE d.id IS NOT NULL) AS databases
                FROM workspaces w
                LEFT JOIN databases d ON d.workspace_id = w.id
                WHERE w.agent_id = %s
                GROUP BY w.id
                ORDER BY w.display_order, w.id
                LIMIT 1
            """, (agent_id,))
            return cur.fetchone()


# ========================================
# Agent Slug 멀티테넌트 라우트 (Phase 2 - 폐쇄형)
# 로그인 필수 + agent/subagent 소속 검증
# ========================================

@bp.route('/<agent_slug>/')
@require_agent_access
def agent_workspace_home(agent_slug):
    """Agent의 기본 워크스페이스 DB 목록.
    /propsheet/goldenrabbit/ → 금토끼 기본 WS의 DB 목록
    """
    agent = _resolve_agent(agent_slug)
    if not agent:
        return "에이전트를 찾을 수 없습니다", 404

    try:
        workspace = _get_agent_default_workspace(agent['id'])
        if not workspace:
            return "워크스페이스가 아직 설정되지 않았습니다", 404

        databases = workspace.get('databases') or []
        return render_template('propsheet/workspaces.html',
                             workspaces=[dict(workspace)],
                             agent_info=dict(agent),
                             agent_slug=agent_slug)
    except Exception as e:
        logger.error(f"agent_workspace_home error ({agent_slug}): {e}")
        return f"Error: {e}", 500


@bp.route('/<agent_slug>/<db_slug>')
@require_agent_access
def agent_database_view(agent_slug, db_slug):
    """Agent 기본 워크스페이스의 특정 DB 뷰.
    /propsheet/goldenrabbit/sales_building → 금토끼의 단일부동산 DB
    """
    agent = _resolve_agent(agent_slug)
    if not agent:
        return "에이전트를 찾을 수 없습니다", 404

    try:
        workspace = _get_agent_default_workspace(agent['id'])
        if not workspace:
            return "워크스페이스가 아직 설정되지 않았습니다", 404

        database = get_database_by_slug(workspace['slug'], db_slug)
        if not database:
            return "데이터베이스를 찾을 수 없습니다", 404

        return render_template('propsheet/database_list.html',
                             workspace=dict(workspace),
                             database=database,
                             agent_info=dict(agent),
                             agent_slug=agent_slug)
    except Exception as e:
        logger.error(f"agent_database_view error ({agent_slug}/{db_slug}): {e}")
        return f"Error: {e}", 500


@bp.route('/<agent_slug>/<db_slug>/calendar')
@require_agent_access
def agent_calendar_view(agent_slug, db_slug):
    """Agent 기본 워크스페이스의 캘린더 뷰.
    /propsheet/goldenrabbit/sales_building/calendar
    """
    agent = _resolve_agent(agent_slug)
    if not agent:
        return "에이전트를 찾을 수 없습니다", 404

    try:
        workspace = _get_agent_default_workspace(agent['id'])
        if not workspace:
            return "워크스페이스가 아직 설정되지 않았습니다", 404

        database = get_database_by_slug(workspace['slug'], db_slug)
        if not database:
            return "데이터베이스를 찾을 수 없습니다", 404

        return render_template('propsheet/calendar.html',
                             workspace=dict(workspace),
                             database=database,
                             agent_info=dict(agent),
                             agent_slug=agent_slug)
    except Exception as e:
        logger.error(f"agent_calendar_view error ({agent_slug}/{db_slug}): {e}")
        return f"Error: {e}", 500


@bp.route('/<agent_slug>/w/<ws_slug>/<db_slug>')
@require_agent_access
def agent_extra_ws_database_view(agent_slug, ws_slug, db_slug):
    """Agent 추가 워크스페이스의 특정 DB 뷰.
    /propsheet/goldenrabbit/w/workspace2/some_db
    """
    agent = _resolve_agent(agent_slug)
    if not agent:
        return "에이전트를 찾을 수 없습니다", 404

    try:
        from services.database_service import get_db_connection
        from psycopg2.extras import RealDictCursor
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM workspaces WHERE slug = %s AND agent_id = %s",
                    (ws_slug, agent['id'])
                )
                workspace = cur.fetchone()

        if not workspace:
            return "워크스페이스를 찾을 수 없습니다", 404

        database = get_database_by_slug(ws_slug, db_slug)
        if not database:
            return "데이터베이스를 찾을 수 없습니다", 404

        return render_template('propsheet/database_list.html',
                             workspace=dict(workspace),
                             database=database,
                             agent_info=dict(agent),
                             agent_slug=agent_slug)
    except Exception as e:
        logger.error(f"agent_extra_ws_database_view error ({agent_slug}/w/{ws_slug}/{db_slug}): {e}")
        return f"Error: {e}", 500


@bp.route('/<agent_slug>/w/<ws_slug>/<db_slug>/calendar')
@require_agent_access
def agent_extra_ws_calendar_view(agent_slug, ws_slug, db_slug):
    """Agent 추가 워크스페이스의 캘린더 뷰.
    /propsheet/goldenrabbit/w/workspace2/some_db/calendar
    """
    agent = _resolve_agent(agent_slug)
    if not agent:
        return "에이전트를 찾을 수 없습니다", 404

    try:
        from services.database_service import get_db_connection
        from psycopg2.extras import RealDictCursor
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM workspaces WHERE slug = %s AND agent_id = %s",
                    (ws_slug, agent['id'])
                )
                workspace = cur.fetchone()

        if not workspace:
            return "워크스페이스를 찾을 수 없습니다", 404

        database = get_database_by_slug(ws_slug, db_slug)
        if not database:
            return "데이터베이스를 찾을 수 없습니다", 404

        return render_template('propsheet/calendar.html',
                             workspace=dict(workspace),
                             database=database,
                             agent_info=dict(agent),
                             agent_slug=agent_slug)
    except Exception as e:
        logger.error(f"agent_extra_ws_calendar_view error ({agent_slug}/w/{ws_slug}/{db_slug}): {e}")
        return f"Error: {e}", 500


# ============================================================
# 과금 필요 페이지
# ============================================================

@bp.route('/<agent_slug>/billing-required')
def billing_required_page(agent_slug):
    """PropSheet 구독이 필요한 경우 표시"""
    reason = request.args.get('reason', '')
    return render_template('propsheet/billing_required.html',
                           agent_slug=agent_slug, reason=reason)


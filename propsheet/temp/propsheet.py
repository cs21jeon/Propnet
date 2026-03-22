#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PropSheet Routes - Slug-based workspace and database management
"""

import logging
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, session

from services.permission_service import (
    propsheet_login_required,
    require_workspace_role
)
from services.workspace_service import (
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
    clone_database_table,
    clone_database_views,
    get_database
)

logger = logging.getLogger(__name__)

bp = Blueprint('propsheet', __name__)


def _get_filtered_workspaces():
    """Get workspaces filtered by current user's membership. Admin sees all."""
    if session.get('is_admin', False):
        return list_workspaces()

    user_id = session.get('user_id')
    if not user_id:
        return []

    from services.workspace_member_service import get_user_workspaces
    from services.database_service import get_db_connection, get_db_cursor
    from psycopg2.extras import RealDictCursor as RDC

    workspaces = get_user_workspaces(user_id)

    # Attach databases to each workspace
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RDC) as cursor:
            for ws in workspaces:
                cursor.execute(
                    'SELECT * FROM databases WHERE workspace_id = %s ORDER BY display_order, id',
                    (ws['id'],)
                )
                ws['databases'] = [dict(row) for row in cursor.fetchall()]

    return workspaces


# ========================================
# Legacy URL redirects (backward compatibility)
# ========================================

from flask import redirect as flask_redirect

@bp.route('/legacy/workspace-view')
def legacy_workspace_view():
    """Redirect old workspace-view URL to new PropSheet workspaces"""
    return flask_redirect('/propsheet/workspaces', code=301)


@bp.route('/legacy/database')
def legacy_database():
    """Redirect old database URL to new slug-based URL"""
    db_id = request.args.get('db', type=int)
    db_mapping = {
        1: '/propsheet/workspace/goldenrabbit/database/sales_building',
        2: '/propsheet/workspace/goldenrabbit/database/sales_multi_unit',
    }
    new_url = db_mapping.get(db_id, '/propsheet/workspaces')
    return flask_redirect(new_url, code=301)


@bp.route('/workspaces')
@propsheet_login_required
def workspaces_list():
    """Render PropSheet workspaces overview page"""
    try:
        workspaces = _get_filtered_workspaces()
        response = make_response(render_template('propsheet/workspaces.html', workspaces=workspaces))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"Error loading workspaces: {e}")
        return f"Error loading workspaces: {e}", 500


@bp.route('/workspace/<slug>')
@require_workspace_role('viewer')
def workspace_detail(slug):
    """Render workspace detail page"""
    try:
        workspace = get_workspace_by_slug(slug)
        if not workspace:
            return "워크스페이스를 찾을 수 없습니다", 404
        return render_template('propsheet/workspace_detail.html', workspace=workspace)
    except Exception as e:
        logger.error(f"Error loading workspace {slug}: {e}")
        return f"Error loading workspace: {e}", 500


@bp.route('/workspace/<ws_slug>/database/<db_slug>')
@require_workspace_role('viewer')
def database_view(ws_slug, db_slug):
    """Render database list/detail page"""
    try:
        workspace = get_workspace_by_slug(ws_slug)
        if not workspace:
            return "워크스페이스를 찾을 수 없습니다", 404

        database = get_database_by_slug(ws_slug, db_slug)
        if not database:
            return "데이터베이스를 찾을 수 없습니다", 404

        return render_template('propsheet/database_list.html',
                             workspace=workspace,
                             database=database)
    except Exception as e:
        logger.error(f"Error loading database {ws_slug}/{db_slug}: {e}")
        return f"Error loading database: {e}", 500


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
        else:
            create_empty_database_table(table_name)

        return jsonify({'success': True, 'id': database_id, 'slug': db_slug})
    except ValueError as e:
        logger.error(f"Validation error creating database: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating database: {e}")
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

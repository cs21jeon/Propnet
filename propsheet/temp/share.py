#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Share Routes - Database sharing and cloning via token links"""

import logging
from flask import Blueprint, request, jsonify, render_template, redirect, session

from services.permission_service import propsheet_login_required, require_workspace_role
from services.share_service import (
    create_share, get_share, deactivate_share,
    increment_clone_count, list_shares
)
from services.workspace_service import (
    get_workspace_by_slug, get_database_by_slug,
    create_database, clone_database_table, clone_database_views, get_database
)

logger = logging.getLogger(__name__)

bp = Blueprint('share', __name__)


@bp.route('/api/workspace/<ws_slug>/database/<db_slug>/shares', methods=['GET'])
@require_workspace_role('owner')
def api_list_shares(ws_slug, db_slug):
    """List all share links for a database"""
    try:
        database = get_database_by_slug(ws_slug, db_slug)
        if not database:
            return jsonify({'success': False, 'error': '데이터베이스를 찾을 수 없습니다'}), 404

        shares = list_shares(database['id'])
        return jsonify({'success': True, 'shares': shares})
    except Exception as e:
        logger.error(f"Error listing shares for {ws_slug}/{db_slug}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/workspace/<ws_slug>/database/<db_slug>/share', methods=['POST'])
@require_workspace_role('owner')
def api_create_share(ws_slug, db_slug):
    """Create a share link for a database (7-day expiry)"""
    try:
        database = get_database_by_slug(ws_slug, db_slug)
        if not database:
            return jsonify({'success': False, 'error': '데이터베이스를 찾을 수 없습니다'}), 404

        user_id = session.get('user_id')
        share = create_share(database['id'], user_id, expires_days=7)

        # Serialize datetime
        for key in ('expires_at', 'created_at'):
            if share.get(key) and hasattr(share[key], 'isoformat'):
                share[key] = share[key].isoformat()

        share['share_url'] = f'/propsheet/share/{share["share_token"]}'

        return jsonify({'success': True, 'share': share})
    except Exception as e:
        logger.error(f"Error creating share for {ws_slug}/{db_slug}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/share/<int:share_id>', methods=['DELETE'])
@propsheet_login_required
def api_deactivate_share(share_id):
    """Deactivate a share link"""
    try:
        user_id = session.get('user_id')
        success = deactivate_share(share_id, user_id)
        if success:
            return jsonify({'success': True, 'message': '공유 링크가 비활성화되었습니다'})
        else:
            return jsonify({'success': False, 'error': '권한이 없거나 링크를 찾을 수 없습니다'}), 404
    except Exception as e:
        logger.error(f"Error deactivating share {share_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/share/<token>')
@propsheet_login_required
def share_page(token):
    """Render share preview page"""
    share = get_share(token)
    if not share:
        return render_template('propsheet/share.html', share=None, error='존재하지 않는 공유 링크입니다')

    if share['status'] == 'expired':
        return render_template('propsheet/share.html', share=share, error='만료된 공유 링크입니다')

    if share['status'] == 'inactive':
        return render_template('propsheet/share.html', share=share, error='비활성화된 공유 링크입니다')

    # Get user's workspaces for clone target selection
    user_id = session.get('user_id')
    from services.workspace_member_service import get_user_workspaces
    workspaces = get_user_workspaces(user_id)
    # Only show workspaces where user is owner
    owner_workspaces = [ws for ws in workspaces if ws.get('role') == 'owner']

    return render_template('propsheet/share.html',
                         share=share,
                         error=None,
                         workspaces=owner_workspaces)


@bp.route('/share/<token>/clone', methods=['POST'])
@propsheet_login_required
def clone_shared_db(token):
    """Clone a shared database into user's workspace"""
    try:
        share = get_share(token)
        if not share or share['status'] != 'active':
            return jsonify({'success': False, 'error': '유효하지 않은 공유 링크입니다'}), 400

        data = request.get_json()
        target_ws_id = data.get('workspace_id')
        db_name = data.get('name', '').strip()
        db_slug = data.get('slug', '').strip()

        if not target_ws_id or not db_name or not db_slug:
            return jsonify({'success': False, 'error': '워크스페이스, 이름, slug를 모두 입력해주세요'}), 400

        # Verify user is owner of target workspace
        user_id = session.get('user_id')
        from services.workspace_member_service import get_user_role
        role = get_user_role(target_ws_id, user_id)
        if role != 'owner' and not session.get('is_admin'):
            return jsonify({'success': False, 'error': '대상 워크스페이스의 소유자만 복제할 수 있습니다'}), 403

        # Create new database record
        table_name = db_slug
        database_id = create_database(
            workspace_id=target_ws_id,
            name=db_name,
            slug=db_slug,
            table_name=table_name,
            description=share.get('db_description', ''),
            icon=share.get('db_icon', '📊'),
            color=share.get('db_color', '#667eea')
        )

        # Clone table structure + data
        source_db = get_database(share['database_id'])
        clone_database_table(
            source_table=source_db['table_name'],
            target_table=table_name,
            source_db_id=share['database_id'],
            target_db_id=database_id
        )

        # Clone views
        clone_database_views(share['database_id'], database_id)

        # Increment clone count
        increment_clone_count(share['id'])

        logger.info(f"User {user_id} cloned shared db {share['database_id']} to workspace {target_ws_id} as {db_slug}")

        return jsonify({
            'success': True,
            'database_id': database_id,
            'message': f'"{db_name}" 데이터베이스가 복제되었습니다'
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error cloning shared db {token}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

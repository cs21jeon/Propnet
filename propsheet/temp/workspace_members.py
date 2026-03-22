#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Workspace Members Routes - Invitation and member management"""

import logging
from flask import Blueprint, request, jsonify, session
from services.permission_service import require_workspace_role
from services.workspace_service import get_workspace_by_slug
from services.workspace_member_service import (
    add_member, remove_member, get_members,
    get_user_role, update_member_role
)
from services.web_user_service import get_web_user_by_email, create_web_user

logger = logging.getLogger(__name__)

bp = Blueprint('workspace_members', __name__)


@bp.route('/workspace/<ws_slug>/members', methods=['GET'])
@require_workspace_role('viewer')
def list_members(ws_slug):
    """Get all members of a workspace"""
    try:
        workspace = get_workspace_by_slug(ws_slug)
        if not workspace:
            return jsonify({'success': False, 'error': '워크스페이스를 찾을 수 없습니다'}), 404

        members = get_members(workspace['id'])

        for m in members:
            if m.get('invited_at'):
                m['invited_at'] = m['invited_at'].isoformat()
            if m.get('accepted_at'):
                m['accepted_at'] = m['accepted_at'].isoformat()

        return jsonify({'success': True, 'members': members})
    except Exception as e:
        logger.error(f"Error listing members for {ws_slug}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/workspace/<ws_slug>/members', methods=['POST'])
@require_workspace_role('owner')
def invite_member(ws_slug):
    """Invite a user by email"""
    try:
        workspace = get_workspace_by_slug(ws_slug)
        if not workspace:
            return jsonify({'success': False, 'error': '워크스페이스를 찾을 수 없습니다'}), 404

        data = request.get_json()
        email = data.get('email', '').strip().lower()
        role = data.get('role', 'editor')

        if not email:
            return jsonify({'success': False, 'error': '이메일을 입력해주세요'}), 400
        if role not in ('editor', 'viewer'):
            return jsonify({'success': False, 'error': '유효하지 않은 역할입니다'}), 400

        # Find or create user
        user = get_web_user_by_email(email)
        if not user:
            # Create account without password (will login via Google)
            user = create_web_user(email=email, name=None, is_active=True)

        invited_by = session.get('user_id')
        member_id = add_member(
            workspace_id=workspace['id'],
            user_id=user['id'],
            role=role,
            invited_by=invited_by
        )

        return jsonify({
            'success': True,
            'member_id': member_id,
            'message': f'{email}님을 초대했습니다'
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error inviting member to {ws_slug}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/workspace/<ws_slug>/members/<int:user_id>', methods=['DELETE'])
@require_workspace_role('owner')
def remove_member_route(ws_slug, user_id):
    """Remove a member from workspace"""
    try:
        workspace = get_workspace_by_slug(ws_slug)
        if not workspace:
            return jsonify({'success': False, 'error': '워크스페이스를 찾을 수 없습니다'}), 404

        removed = remove_member(workspace['id'], user_id)
        if removed:
            return jsonify({'success': True, 'message': '멤버가 제거되었습니다'})
        else:
            return jsonify({'success': False, 'error': '멤버를 찾을 수 없습니다'}), 404
    except Exception as e:
        logger.error(f"Error removing member from {ws_slug}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/workspace/<ws_slug>/members/<int:user_id>/role', methods=['PATCH'])
@require_workspace_role('owner')
def update_role(ws_slug, user_id):
    """Update a member's role"""
    try:
        workspace = get_workspace_by_slug(ws_slug)
        if not workspace:
            return jsonify({'success': False, 'error': '워크스페이스를 찾을 수 없습니다'}), 404

        data = request.get_json()
        new_role = data.get('role')
        if new_role not in ('owner', 'editor', 'viewer'):
            return jsonify({'success': False, 'error': '유효하지 않은 역할입니다'}), 400

        updated = update_member_role(workspace['id'], user_id, new_role)
        if updated:
            return jsonify({'success': True, 'message': '역할이 변경되었습니다'})
        else:
            return jsonify({'success': False, 'error': '멤버를 찾을 수 없습니다'}), 404
    except Exception as e:
        logger.error(f"Error updating role in {ws_slug}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

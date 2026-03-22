#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Share Service - Database sharing via token-based links"""

import secrets
import logging
from datetime import datetime, timedelta
from services.database_service import get_db_connection, get_db_cursor
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def create_share(database_id, user_id, expires_days=7):
    """Create a share link for a database. Returns share dict."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=expires_days)

    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute('''
                INSERT INTO database_shares (database_id, share_token, created_by, expires_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id, share_token, expires_at, created_at
            ''', (database_id, token, user_id, expires_at))
            result = dict(cursor.fetchone())
            conn.commit()
            return result


def get_share(token):
    """Get share info by token. Returns None if expired or inactive."""
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute('''
                SELECT ds.*, d.name AS db_name, d.slug AS db_slug,
                       d.table_name, d.description AS db_description,
                       d.icon AS db_icon, d.color AS db_color,
                       d.workspace_id,
                       w.name AS ws_name, w.slug AS ws_slug,
                       wu.email AS creator_email, wu.name AS creator_name
                FROM database_shares ds
                JOIN databases d ON ds.database_id = d.id
                JOIN workspaces w ON d.workspace_id = w.id
                LEFT JOIN web_users wu ON ds.created_by = wu.id
                WHERE ds.share_token = %s
            ''', (token,))
            share = cursor.fetchone()

            if not share:
                return None

            share = dict(share)

            # Check active and not expired
            if not share['is_active']:
                share['status'] = 'inactive'
                return share

            if share['expires_at'] < datetime.now():
                share['status'] = 'expired'
                return share

            # Get record count and field count
            try:
                cursor.execute(f'SELECT COUNT(*) AS cnt FROM "{share["table_name"]}"')
                share['record_count'] = cursor.fetchone()['cnt']
            except Exception:
                share['record_count'] = 0

            try:
                cursor.execute('''
                    SELECT COUNT(*) AS cnt FROM information_schema.columns
                    WHERE table_name = %s AND column_name NOT IN ('id', 'database_id', 'created_at', 'updated_at', 'airtable_id')
                ''', (share['table_name'],))
                share['field_count'] = cursor.fetchone()['cnt']
            except Exception:
                share['field_count'] = 0

            share['status'] = 'active'
            return share


def deactivate_share(share_id, user_id):
    """Deactivate a share link. Only creator can deactivate."""
    with get_db_connection() as conn:
        with get_db_cursor(conn) as cursor:
            cursor.execute('''
                UPDATE database_shares SET is_active = FALSE
                WHERE id = %s AND created_by = %s
            ''', (share_id, user_id))
            conn.commit()
            return cursor.rowcount > 0


def increment_clone_count(share_id):
    """Increment the clone count for a share."""
    with get_db_connection() as conn:
        with get_db_cursor(conn) as cursor:
            cursor.execute('''
                UPDATE database_shares SET clone_count = clone_count + 1
                WHERE id = %s
            ''', (share_id,))
            conn.commit()


def list_shares(database_id):
    """List all share links for a database."""
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute('''
                SELECT ds.*, wu.email AS creator_email
                FROM database_shares ds
                LEFT JOIN web_users wu ON ds.created_by = wu.id
                WHERE ds.database_id = %s
                ORDER BY ds.created_at DESC
            ''', (database_id,))
            shares = [dict(row) for row in cursor.fetchall()]

            now = datetime.now()
            for s in shares:
                if not s['is_active']:
                    s['status'] = 'inactive'
                elif s['expires_at'] < now:
                    s['status'] = 'expired'
                else:
                    s['status'] = 'active'
                # Serialize datetimes
                for key in ('expires_at', 'created_at'):
                    if s.get(key) and hasattr(s[key], 'isoformat'):
                        s[key] = s[key].isoformat()

            return shares

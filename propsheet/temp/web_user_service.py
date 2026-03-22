#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Web User Service - User management for Propsheet web app"""

import logging
import bcrypt
from services.database_service import get_db_connection, get_db_cursor
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def create_web_user(email: str, password: str = None, name: str = None,
                    is_active: bool = True, google_id: str = None, avatar_url: str = None) -> dict:
    """Create a new web user. Password is optional for Google OAuth users."""
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT id FROM web_users WHERE email = %s', (email,))
            if cursor.fetchone():
                raise ValueError(f'이미 등록된 이메일입니다: {email}')

            pw_hash = hash_password(password) if password else None
            cursor.execute('''
                INSERT INTO web_users (email, password_hash, name, is_active, google_id, avatar_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, email, name, is_active, google_id, avatar_url, created_at
            ''', (email, pw_hash, name, is_active, google_id, avatar_url))
            user = dict(cursor.fetchone())
            conn.commit()
            logger.info(f"Created web user: {email} (id={user['id']})")
            return user


def update_web_user(user_id: int, **kwargs) -> bool:
    """Update web user fields. Supported: name, google_id, avatar_url, is_active."""
    allowed = {'name', 'google_id', 'avatar_url', 'is_active'}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False

    set_clauses = ', '.join(f'{k} = %s' for k in updates)
    values = list(updates.values()) + [user_id]

    with get_db_connection() as conn:
        with get_db_cursor(conn) as cursor:
            cursor.execute(
                f'UPDATE web_users SET {set_clauses}, updated_at = NOW() WHERE id = %s',
                values
            )
            conn.commit()
            return cursor.rowcount > 0


def authenticate_web_user(email: str, password: str) -> dict:
    """Authenticate user. Returns user dict or None."""
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, email, password_hash, name, is_active, google_id, avatar_url FROM web_users WHERE email = %s',
                (email,)
            )
            user = cursor.fetchone()
            if not user:
                return None
            if not user['is_active']:
                return None
            if not user['password_hash']:
                return None  # Google-only user, no password login
            if not verify_password(password, user['password_hash']):
                return None

            result = dict(user)
            del result['password_hash']
            return result


def get_web_user_by_id(user_id: int) -> dict:
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, email, name, is_active, google_id, avatar_url, created_at FROM web_users WHERE id = %s',
                (user_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None


def get_web_user_by_email(email: str) -> dict:
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, email, name, is_active, google_id, avatar_url, created_at FROM web_users WHERE email = %s',
                (email,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None


def get_web_user_by_google_id(google_id: str) -> dict:
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, email, name, is_active, google_id, avatar_url, created_at FROM web_users WHERE google_id = %s',
                (google_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None


def list_web_users() -> list:
    with get_db_connection() as conn:
        with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, email, name, is_active, google_id, avatar_url, created_at FROM web_users ORDER BY id'
            )
            return [dict(row) for row in cursor.fetchall()]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Google OAuth Service - Google login flow for Propsheet"""

import os
import logging
import requests
from google_auth_oauthlib.flow import Flow

logger = logging.getLogger(__name__)

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]
REDIRECT_URI = 'https://goldenrabbit.biz/propsheet/auth/google/callback'


def get_flow():
    """Create Google OAuth Flow instance from env vars."""
    client_config = {
        'web': {
            'client_id': os.environ.get('GOOGLE_OAUTH_CLIENT_ID'),
            'client_secret': os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET'),
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'redirect_uris': [REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI
    return flow


def get_authorization_url():
    """Generate Google OAuth authorization URL with state."""
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='select_account'
    )
    return authorization_url, state


def exchange_code_for_user_info(authorization_response, state=None):
    """Exchange authorization code for tokens and fetch user profile."""
    flow = get_flow()
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    userinfo_response = requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        headers={'Authorization': f'Bearer {credentials.token}'}
    )
    userinfo_response.raise_for_status()
    return userinfo_response.json()
    # Returns: {'sub': google_id, 'email': ..., 'name': ..., 'picture': ...}


def find_or_create_user(userinfo):
    """Find existing user by email or create new. Returns (user_dict, is_new_user)."""
    from services.web_user_service import (
        get_web_user_by_email, create_web_user, update_web_user
    )

    google_id = userinfo.get('sub')
    email = userinfo.get('email', '').lower()
    name = userinfo.get('name', '')
    avatar_url = userinfo.get('picture', '')

    # Try to find by email (covers pre-existing invited users)
    user = get_web_user_by_email(email)

    if user:
        # Update google_id and avatar if not set
        updates = {}
        if not user.get('google_id') and google_id:
            updates['google_id'] = google_id
        if avatar_url:
            updates['avatar_url'] = avatar_url
        if name and not user.get('name'):
            updates['name'] = name
        if updates:
            update_web_user(user['id'], **updates)
            user.update(updates)
        return user, False

    # Create new user (no password needed for Google OAuth)
    user = create_web_user(
        email=email,
        name=name,
        google_id=google_id,
        avatar_url=avatar_url
    )
    return user, True

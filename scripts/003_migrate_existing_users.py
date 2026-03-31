#!/usr/bin/env python3
"""
003_migrate_existing_users.py
Migrate existing users from app_users, web_users, voiceroom.users into propnet_users.
Email-based matching: same email = same propnet_user.
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load env
load_dotenv('/home/webapp/goldenrabbit/backend/.env')

DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME', 'goldenrabbit_db')
VOICEROOM_DB = 'voiceroom'

ADMIN_EMAIL = 'cs21.jeon@gmail.com'


def get_conn(dbname):
    return psycopg2.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
        dbname=dbname
    )


def main():
    conn_main = get_conn(DB_NAME)
    conn_voice = get_conn(VOICEROOM_DB)
    conn_main.autocommit = False
    conn_voice.autocommit = False

    try:
        cur_main = conn_main.cursor(cursor_factory=RealDictCursor)
        cur_voice = conn_voice.cursor(cursor_factory=RealDictCursor)

        # == Step 1: Collect all users by email ==
        # Dict: email -> { google_id, name, avatar_url, role, sources: {service: local_id} }
        email_map = {}

        # 1a. app_users
        cur_main.execute("SELECT id, email, name, provider, provider_id, role FROM app_users")
        app_rows = cur_main.fetchall()
        print(f"[INFO] app_users: {len(app_rows)} rows")

        for row in app_rows:
            email = row['email'].lower().strip()
            google_id = row['provider_id'] if row['provider'] == 'google' else None
            if email not in email_map:
                email_map[email] = {
                    'google_id': google_id,
                    'name': row['name'],
                    'avatar_url': None,
                    'role': row['role'] or 'user',
                    'sources': {}
                }
            else:
                # Merge: prefer google_id if we do not have one yet
                if google_id and not email_map[email]['google_id']:
                    email_map[email]['google_id'] = google_id
                # Keep more privileged role
                existing_role = email_map[email]['role']
                new_role = row['role'] or 'user'
                if new_role in ('admin', 'agent', 'subagent') and existing_role == 'user':
                    email_map[email]['role'] = new_role
            email_map[email]['sources']['propedia'] = row['id']

        # 1b. web_users
        cur_main.execute("SELECT id, email, name, google_id, avatar_url, role FROM web_users")
        web_rows = cur_main.fetchall()
        print(f"[INFO] web_users: {len(web_rows)} rows")

        for row in web_rows:
            email = row['email'].lower().strip()
            google_id = row['google_id']
            if email not in email_map:
                email_map[email] = {
                    'google_id': google_id,
                    'name': row['name'],
                    'avatar_url': row['avatar_url'],
                    'role': row['role'] or 'user',
                    'sources': {}
                }
            else:
                if google_id and not email_map[email]['google_id']:
                    email_map[email]['google_id'] = google_id
                if row['avatar_url'] and not email_map[email]['avatar_url']:
                    email_map[email]['avatar_url'] = row['avatar_url']
                existing_role = email_map[email]['role']
                new_role = row['role'] or 'user'
                if new_role in ('admin', 'agent', 'subagent') and existing_role == 'user':
                    email_map[email]['role'] = new_role
            email_map[email]['sources']['propsheet'] = row['id']

        # 1c. voiceroom.users
        cur_voice.execute("SELECT id, email, name, google_id, avatar_url FROM users")
        voice_rows = cur_voice.fetchall()
        print(f"[INFO] voiceroom.users: {len(voice_rows)} rows")

        for row in voice_rows:
            email = row['email'].lower().strip()
            google_id = row['google_id']
            if email not in email_map:
                email_map[email] = {
                    'google_id': google_id,
                    'name': row['name'],
                    'avatar_url': row['avatar_url'],
                    'role': 'user',
                    'sources': {}
                }
            else:
                if google_id and not email_map[email]['google_id']:
                    email_map[email]['google_id'] = google_id
                if row['avatar_url'] and not email_map[email]['avatar_url']:
                    email_map[email]['avatar_url'] = row['avatar_url']
            email_map[email]['sources']['proptalk'] = row['id']

        # Admin override
        if ADMIN_EMAIL in email_map:
            email_map[ADMIN_EMAIL]['role'] = 'admin'

        print(f"\n[INFO] Unique emails (propnet_users to create): {len(email_map)}")

        # Count overlaps
        multi_service = sum(1 for v in email_map.values() if len(v['sources']) > 1)
        print(f"[INFO] Users in multiple services: {multi_service}")

        # == Step 2: Insert into propnet_users + service_user_links ==
        propnet_count = 0
        link_count = 0

        for email, info in email_map.items():
            cur_main.execute(
                "INSERT INTO propnet_users (google_id, email, name, avatar_url, role) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON CONFLICT (email) DO UPDATE SET "
                "  google_id = COALESCE(propnet_users.google_id, EXCLUDED.google_id), "
                "  name = COALESCE(EXCLUDED.name, propnet_users.name), "
                "  avatar_url = COALESCE(EXCLUDED.avatar_url, propnet_users.avatar_url), "
                "  role = EXCLUDED.role "
                "RETURNING id",
                (info['google_id'], email, info['name'], info['avatar_url'], info['role'])
            )
            propnet_user_id = cur_main.fetchone()['id']
            propnet_count += 1

            # service_user_links
            for service, local_id in info['sources'].items():
                cur_main.execute(
                    "INSERT INTO service_user_links (propnet_user_id, service, local_user_id) "
                    "VALUES (%s, %s, %s) "
                    "ON CONFLICT (service, local_user_id) DO NOTHING",
                    (propnet_user_id, service, local_id)
                )
                link_count += 1

            # Update propnet_user_id in source tables
            if 'propedia' in info['sources']:
                cur_main.execute(
                    "UPDATE app_users SET propnet_user_id = %s WHERE id = %s",
                    (propnet_user_id, info['sources']['propedia'])
                )
            if 'propsheet' in info['sources']:
                cur_main.execute(
                    "UPDATE web_users SET propnet_user_id = %s WHERE id = %s",
                    (propnet_user_id, info['sources']['propsheet'])
                )
            if 'proptalk' in info['sources']:
                cur_voice.execute(
                    "UPDATE users SET propnet_user_id = %s WHERE id = %s",
                    (propnet_user_id, info['sources']['proptalk'])
                )

        # == Step 3: Commit ==
        conn_main.commit()
        conn_voice.commit()

        print(f"\n{'='*50}")
        print(f"[DONE] propnet_users created/updated: {propnet_count}")
        print(f"[DONE] service_user_links created: {link_count}")

        # == Step 4: Verification ==
        cur_main.execute("SELECT count(*) as cnt FROM propnet_users")
        print(f"[VERIFY] propnet_users total: {cur_main.fetchone()['cnt']}")

        cur_main.execute("SELECT count(*) as cnt FROM service_user_links")
        print(f"[VERIFY] service_user_links total: {cur_main.fetchone()['cnt']}")

        cur_main.execute("SELECT count(*) as cnt FROM app_users WHERE propnet_user_id IS NOT NULL")
        print(f"[VERIFY] app_users with propnet_user_id: {cur_main.fetchone()['cnt']}")

        cur_main.execute("SELECT count(*) as cnt FROM web_users WHERE propnet_user_id IS NOT NULL")
        print(f"[VERIFY] web_users with propnet_user_id: {cur_main.fetchone()['cnt']}")

        cur_voice.execute("SELECT count(*) as cnt FROM users WHERE propnet_user_id IS NOT NULL")
        print(f"[VERIFY] voiceroom.users with propnet_user_id: {cur_voice.fetchone()['cnt']}")

        cur_main.execute(
            "SELECT email, role FROM propnet_users WHERE role != 'user' ORDER BY role, email"
        )
        special_roles = cur_main.fetchall()
        print(f"\n[VERIFY] Non-user roles:")
        for r in special_roles:
            print(f"  {r['role']:10s} {r['email']}")

        # Show multi-service users
        cur_main.execute(
            "SELECT pu.email, array_agg(sul.service ORDER BY sul.service) as services "
            "FROM propnet_users pu "
            "JOIN service_user_links sul ON sul.propnet_user_id = pu.id "
            "GROUP BY pu.email "
            "HAVING count(*) > 1 "
            "ORDER BY pu.email"
        )
        multi = cur_main.fetchall()
        print(f"\n[VERIFY] Multi-service users ({len(multi)}):")
        for r in multi:
            print(f"  {r['email']:35s} {r['services']}")

    except Exception as e:
        conn_main.rollback()
        conn_voice.rollback()
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn_main.close()
        conn_voice.close()


if __name__ == '__main__':
    main()

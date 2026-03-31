#!/usr/bin/env python3
"""
004_migrate_proptalk_consents.py
Migrate voiceroom.user_consents -> propnet_consents (service='proptalk').
Must run AFTER 003_migrate_existing_users.py (needs service_user_links).
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


def get_conn(dbname):
    return psycopg2.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
        dbname=dbname
    )


def main():
    conn_main = get_conn(DB_NAME)
    conn_voice = get_conn(VOICEROOM_DB)
    conn_main.autocommit = False

    try:
        cur_main = conn_main.cursor(cursor_factory=RealDictCursor)
        cur_voice = conn_voice.cursor(cursor_factory=RealDictCursor)

        # == Step 1: Build voiceroom user_id -> propnet_user_id mapping ==
        cur_main.execute(
            "SELECT propnet_user_id, local_user_id FROM service_user_links "
            "WHERE service = 'proptalk'"
        )
        link_rows = cur_main.fetchall()
        voice_to_propnet = {row['local_user_id']: row['propnet_user_id'] for row in link_rows}
        print(f"[INFO] Proptalk user links found: {len(voice_to_propnet)}")

        if not voice_to_propnet:
            print("[ERROR] No proptalk links found. Run 003 first!")
            sys.exit(1)

        # == Step 2: Read voiceroom.user_consents ==
        cur_voice.execute(
            "SELECT id, user_id, consent_type, version, agreed, agreed_at, "
            "withdrawn_at, ip_address, user_agent FROM user_consents ORDER BY id"
        )
        consent_rows = cur_voice.fetchall()
        print(f"[INFO] voiceroom.user_consents: {len(consent_rows)} rows")

        # == Step 2.5: Deduplicate - keep only the latest consent per (user, type, version) ==
        # The original table has many duplicate audio_processing entries per session
        seen = {}  # (propnet_user_id, consent_type, version) -> row (keep latest)
        skipped_no_mapping = 0

        for row in consent_rows:
            propnet_user_id = voice_to_propnet.get(row['user_id'])
            if not propnet_user_id:
                print(f"  [WARN] No propnet mapping for voiceroom user_id={row['user_id']}, skipping consent id={row['id']}")
                skipped_no_mapping += 1
                continue

            key = (propnet_user_id, row['consent_type'], row['version'])
            # Keep the latest agreed_at for each unique key
            if key not in seen or (row['agreed_at'] and (not seen[key]['agreed_at'] or row['agreed_at'] > seen[key]['agreed_at'])):
                seen[key] = dict(row)
                seen[key]['_propnet_user_id'] = propnet_user_id

        print(f"[INFO] Unique consents to migrate (after dedup): {len(seen)}")
        print(f"[INFO] Skipped (no mapping): {skipped_no_mapping}")

        # == Step 3: Clear existing proptalk consents and insert fresh ==
        cur_main.execute("DELETE FROM propnet_consents WHERE service = 'proptalk'")
        deleted = cur_main.rowcount
        if deleted > 0:
            print(f"[INFO] Cleared {deleted} existing proptalk consents")

        inserted = 0
        for key, row in seen.items():
            propnet_user_id = row['_propnet_user_id']
            cur_main.execute(
                "INSERT INTO propnet_consents "
                "(propnet_user_id, consent_type, version, service, agreed, agreed_at, "
                " withdrawn_at, ip_address, user_agent) "
                "VALUES (%s, %s, %s, 'proptalk', %s, %s, %s, %s, %s)",
                (
                    propnet_user_id,
                    row['consent_type'],
                    row['version'],
                    row['agreed'],
                    row['agreed_at'],
                    row['withdrawn_at'],
                    row['ip_address'],
                    row['user_agent'],
                )
            )
            inserted += 1

        # == Step 4: Commit ==
        conn_main.commit()

        print(f"\n{'='*50}")
        print(f"[DONE] Consents migrated: {inserted}")
        print(f"[DONE] Skipped (no mapping): {skipped_no_mapping}")

        # == Step 5: Verification ==
        cur_main.execute("SELECT count(*) as cnt FROM propnet_consents")
        print(f"[VERIFY] propnet_consents total: {cur_main.fetchone()['cnt']}")

        cur_main.execute(
            "SELECT consent_type, count(*) as cnt FROM propnet_consents "
            "WHERE service = 'proptalk' GROUP BY consent_type ORDER BY consent_type"
        )
        by_type = cur_main.fetchall()
        print(f"[VERIFY] By consent_type:")
        for r in by_type:
            print(f"  {r['consent_type']:25s} {r['cnt']}")

    except Exception as e:
        conn_main.rollback()
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn_main.close()
        conn_voice.close()


if __name__ == '__main__':
    main()

"""
DB 모델 및 헬퍼 함수 (psycopg2 기반)
"""
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from config import Config

# ============================================================
# DB 연결 풀
# ============================================================
from psycopg2 import pool

db_pool = pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    dsn=Config.DATABASE_URL
)


@contextmanager
def get_db():
    """DB 커넥션 컨텍스트 매니저"""
    conn = db_pool.getconn()
    try:
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)


def query_one(sql, params=None):
    """단일 행 조회"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def query_all(sql, params=None):
    """다중 행 조회"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def execute(sql, params=None):
    """INSERT/UPDATE/DELETE 실행, 반환값 있으면 반환"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            try:
                return cur.fetchone()
            except psycopg2.ProgrammingError:
                return None


# ============================================================
# User 모델
# ============================================================
class User:
    @staticmethod
    def find_by_google_id(google_id):
        return query_one("SELECT * FROM users WHERE google_id = %s", (google_id,))
    
    @staticmethod
    def find_by_id(user_id):
        return query_one("SELECT * FROM users WHERE id = %s", (user_id,))
    
    @staticmethod
    def create(google_id, email, name, avatar_url=None):
        return execute(
            """INSERT INTO users (google_id, email, name, avatar_url)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (google_id) DO UPDATE
               SET name = EXCLUDED.name, avatar_url = EXCLUDED.avatar_url
               RETURNING *""",
            (google_id, email, name, avatar_url)
        )

    @staticmethod
    def update_name(user_id, name):
        return execute(
            "UPDATE users SET name = %s WHERE id = %s RETURNING *",
            (name, user_id)
        )

    @staticmethod
    def update_google_tokens(user_id, tokens):
        import json
        return execute(
            "UPDATE users SET google_tokens = %s WHERE id = %s RETURNING *",
            (json.dumps(tokens), user_id)
        )

    @staticmethod
    def get_google_tokens(user_id):
        result = query_one("SELECT google_tokens FROM users WHERE id = %s", (user_id,))
        return result['google_tokens'] if result else None

    @staticmethod
    def list_all():
        return query_all("SELECT * FROM users ORDER BY created_at DESC")


# ============================================================
# Room 모델
# ============================================================
class Room:
    @staticmethod
    def create(name, description, created_by, invite_code,
               enable_drive_backup=True, enable_sheets_logging=True):
        return execute(
            """INSERT INTO rooms (name, description, created_by, invite_code,
               enable_drive_backup, enable_sheets_logging)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING *""",
            (name, description, created_by, invite_code,
             enable_drive_backup, enable_sheets_logging)
        )

    @staticmethod
    def update_settings(room_id, enable_drive_backup=None, enable_sheets_logging=None):
        updates = []
        params = []
        if enable_drive_backup is not None:
            updates.append("enable_drive_backup = %s")
            params.append(enable_drive_backup)
        if enable_sheets_logging is not None:
            updates.append("enable_sheets_logging = %s")
            params.append(enable_sheets_logging)
        if not updates:
            return Room.find_by_id(room_id)
        params.append(room_id)
        return execute(
            f"UPDATE rooms SET {', '.join(updates)} WHERE id = %s RETURNING *",
            tuple(params)
        )
    
    @staticmethod
    def find_by_id(room_id):
        return query_one("SELECT * FROM rooms WHERE id = %s", (room_id,))
    
    @staticmethod
    def find_by_invite_code(code):
        return query_one("SELECT * FROM rooms WHERE invite_code = %s", (code,))
    
    @staticmethod
    def list_for_user(user_id):
        return query_all(
            """SELECT r.*, rm.role,
                      (SELECT COUNT(*) FROM room_members WHERE room_id = r.id) as member_count,
                      (SELECT content FROM messages WHERE room_id = r.id ORDER BY created_at DESC LIMIT 1) as last_message
               FROM rooms r
               JOIN room_members rm ON r.id = rm.room_id
               WHERE rm.user_id = %s
               ORDER BY r.updated_at DESC""",
            (user_id,)
        )
    
    @staticmethod
    def add_member(room_id, user_id, role='member'):
        return execute(
            """INSERT INTO room_members (room_id, user_id, role)
               VALUES (%s, %s, %s)
               ON CONFLICT (room_id, user_id) DO NOTHING
               RETURNING *""",
            (room_id, user_id, role)
        )
    
    @staticmethod
    def get_members(room_id):
        return query_all(
            """SELECT u.id, u.name, u.email, u.avatar_url, rm.role, rm.joined_at
               FROM room_members rm
               JOIN users u ON rm.user_id = u.id
               WHERE rm.room_id = %s
               ORDER BY rm.joined_at""",
            (room_id,)
        )
    
    @staticmethod
    def is_member(room_id, user_id):
        result = query_one(
            "SELECT 1 FROM room_members WHERE room_id = %s AND user_id = %s",
            (room_id, user_id)
        )
        return result is not None

    @staticmethod
    def remove_member(room_id, user_id):
        return execute(
            """DELETE FROM room_members
               WHERE room_id = %s AND user_id = %s
               RETURNING drive_permission_id""",
            (room_id, user_id)
        )

    @staticmethod
    def update_drive_permission(room_id, user_id, permission_id):
        return execute(
            """UPDATE room_members SET drive_permission_id = %s
               WHERE room_id = %s AND user_id = %s""",
            (permission_id, room_id, user_id)
        )

    @staticmethod
    def get_drive_folder_id(room_id):
        result = query_one(
            "SELECT drive_folder_id FROM rooms WHERE id = %s",
            (room_id,)
        )
        return result['drive_folder_id'] if result else None

    @staticmethod
    def get_owner(room_id):
        return query_one(
            """SELECT u.* FROM users u
               JOIN room_members rm ON u.id = rm.user_id
               WHERE rm.room_id = %s AND rm.role = 'admin'""",
            (room_id,)
        )

    @staticmethod
    def rename(room_id, new_name):
        return execute(
            "UPDATE rooms SET name = %s WHERE id = %s RETURNING *",
            (new_name, room_id)
        )

    @staticmethod
    def delete(room_id):
        """채팅방 삭제 (CASCADE로 멤버/메시지/음성파일도 삭제)"""
        execute("DELETE FROM rooms WHERE id = %s", (room_id,))


# ============================================================
# Message 모델
# ============================================================
class Message:
    @staticmethod
    def create(room_id, user_id, msg_type, content, parent_id=None):
        return execute(
            """INSERT INTO messages (room_id, user_id, type, content, parent_id)
               VALUES (%s, %s, %s, %s, %s) RETURNING *""",
            (room_id, user_id, msg_type, content, parent_id)
        )
    
    @staticmethod
    def list_for_room(room_id, limit=50, before_id=None):
        if before_id:
            return query_all(
                """SELECT m.*, u.name as user_name, u.avatar_url as user_avatar,
                          af.id as audio_id, af.drive_url, af.drive_file_id, af.status as audio_status,
                          fa.id as file_id, fa.original_filename as file_name,
                          fa.file_size as file_size, fa.file_type as file_type,
                          fa.drive_url as file_drive_url, fa.status as file_status,
                          (SELECT json_agg(json_build_object(
                              'id', r.id, 'type', r.type, 'content', r.content,
                              'user_name', ru.name, 'created_at', r.created_at
                          ) ORDER BY r.created_at)
                          FROM messages r JOIN users ru ON r.user_id = ru.id
                          WHERE r.parent_id = m.id) as replies
                   FROM messages m
                   JOIN users u ON m.user_id = u.id
                   LEFT JOIN audio_files af ON af.message_id = m.id
                   LEFT JOIN file_attachments fa ON fa.message_id = m.id
                   WHERE m.room_id = %s AND m.id < %s AND m.parent_id IS NULL
                   ORDER BY m.created_at DESC
                   LIMIT %s""",
                (room_id, before_id, limit)
            )
        return query_all(
            """SELECT m.*, u.name as user_name, u.avatar_url as user_avatar,
                      af.id as audio_id, af.drive_url, af.drive_file_id, af.status as audio_status,
                      fa.id as file_id, fa.original_filename as file_name,
                      fa.file_size as file_size, fa.file_type as file_type,
                      fa.drive_url as file_drive_url, fa.status as file_status,
                      (SELECT json_agg(json_build_object(
                          'id', r.id, 'type', r.type, 'content', r.content,
                          'user_name', ru.name, 'created_at', r.created_at
                      ) ORDER BY r.created_at)
                      FROM messages r JOIN users ru ON r.user_id = ru.id
                      WHERE r.parent_id = m.id) as replies
               FROM messages m
               JOIN users u ON m.user_id = u.id
               LEFT JOIN audio_files af ON af.message_id = m.id
               LEFT JOIN file_attachments fa ON fa.message_id = m.id
               WHERE m.room_id = %s AND m.parent_id IS NULL
               ORDER BY m.created_at DESC
               LIMIT %s""",
            (room_id, limit)
        )
    
    @staticmethod
    def get_replies(message_id):
        return query_all(
            """SELECT m.*, u.name as user_name, u.avatar_url as user_avatar
               FROM messages m
               JOIN users u ON m.user_id = u.id
               WHERE m.parent_id = %s
               ORDER BY m.created_at""",
            (message_id,)
        )

    @staticmethod
    def search(room_id, query, limit=100):
        """메시지 내용 + 음성파일명 + 변환/요약 텍스트 검색"""
        like_pattern = f'%{query}%'
        return query_all(
            """SELECT DISTINCT m.id, m.room_id, m.user_id, m.type, m.content,
                      m.parent_id, m.created_at,
                      u.name as user_name, u.avatar_url as user_avatar
               FROM messages m
               JOIN users u ON m.user_id = u.id
               LEFT JOIN audio_files af ON af.message_id = m.id
               LEFT JOIN messages r ON r.parent_id = m.id
               WHERE m.room_id = %s AND m.parent_id IS NULL
                 AND (m.content ILIKE %s
                      OR af.original_filename ILIKE %s
                      OR af.transcript_text ILIKE %s
                      OR af.transcript_summary ILIKE %s
                      OR r.content ILIKE %s)
               ORDER BY m.created_at DESC
               LIMIT %s""",
            (room_id, like_pattern, like_pattern, like_pattern,
             like_pattern, like_pattern, limit)
        )


# ============================================================
# AudioFile 모델
# ============================================================
class AudioFile:
    @staticmethod
    def create(message_id, room_id, user_id, original_filename, file_size=0):
        return execute(
            """INSERT INTO audio_files 
               (message_id, room_id, user_id, original_filename, file_size, status)
               VALUES (%s, %s, %s, %s, %s, 'uploading') RETURNING *""",
            (message_id, room_id, user_id, original_filename, file_size)
        )
    
    @staticmethod
    def update_parsed(audio_id, phone_number=None, record_date=None, 
                      parsed_name=None, parsed_memo=None):
        return execute(
            """UPDATE audio_files 
               SET phone_number = %s, record_date = %s, 
                   parsed_name = %s, parsed_memo = %s
               WHERE id = %s RETURNING *""",
            (phone_number, record_date, parsed_name, parsed_memo, audio_id)
        )
    
    @staticmethod
    def update_transcript(audio_id, transcript_text, transcript_summary=None, 
                          transcript_segments=None):
        import json
        return execute(
            """UPDATE audio_files 
               SET transcript_text = %s, transcript_summary = %s,
                   transcript_segments = %s, status = 'completed', completed_at = NOW()
               WHERE id = %s RETURNING *""",
            (transcript_text, transcript_summary, 
             json.dumps(transcript_segments) if transcript_segments else None, 
             audio_id)
        )
    
    @staticmethod
    def update_drive(audio_id, drive_file_id, drive_url):
        return execute(
            """UPDATE audio_files
               SET drive_file_id = %s, drive_url = %s, drive_status = 'completed'
               WHERE id = %s RETURNING *""",
            (drive_file_id, drive_url, audio_id)
        )
    
    @staticmethod
    def update_status(audio_id, status, error_message=None):
        return execute(
            """UPDATE audio_files SET status = %s, error_message = %s
               WHERE id = %s RETURNING *""",
            (status, error_message, audio_id)
        )
    
    @staticmethod
    def find_by_id(audio_id):
        return query_one("SELECT * FROM audio_files WHERE id = %s", (audio_id,))
    
    @staticmethod
    def list_for_room(room_id, limit=50):
        return query_all(
            """SELECT af.*, u.name as user_name
               FROM audio_files af
               JOIN users u ON af.user_id = u.id
               WHERE af.room_id = %s
               ORDER BY af.created_at DESC
               LIMIT %s""",
            (room_id, limit)
        )
    
    @staticmethod
    def update_duration(audio_id, duration_seconds):
        return execute(
            "UPDATE audio_files SET duration_seconds = %s WHERE id = %s RETURNING *",
            (duration_seconds, audio_id)
        )

    @staticmethod
    def search(room_id=None, phone_number=None, date_from=None, date_to=None):
        """음성 파일 검색 (전화번호, 날짜 범위)"""
        conditions = []
        params = []
        
        if room_id:
            conditions.append("af.room_id = %s")
            params.append(room_id)
        if phone_number:
            conditions.append("af.phone_number LIKE %s")
            params.append(f"%{phone_number}%")
        if date_from:
            conditions.append("af.record_date >= %s")
            params.append(date_from)
        if date_to:
            conditions.append("af.record_date <= %s")
            params.append(date_to)
        
        where = " AND ".join(conditions) if conditions else "1=1"
        
        return query_all(
            f"""SELECT af.*, u.name as user_name
                FROM audio_files af
                JOIN users u ON af.user_id = u.id
                WHERE {where}
                ORDER BY af.created_at DESC
                LIMIT 100""",
            tuple(params)
        )


# ============================================================
# FileAttachment 모델
# ============================================================
class FileAttachment:
    @staticmethod
    def create(message_id, room_id, user_id, original_filename, file_size, file_type, mime_type=None):
        return execute(
            """INSERT INTO file_attachments
               (message_id, room_id, user_id, original_filename, file_size, file_type, mime_type, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'uploading') RETURNING *""",
            (message_id, room_id, user_id, original_filename, file_size, file_type, mime_type)
        )

    @staticmethod
    def update_drive(attachment_id, drive_file_id, drive_url):
        return execute(
            """UPDATE file_attachments
               SET drive_file_id = %s, drive_url = %s, status = 'completed', completed_at = NOW()
               WHERE id = %s RETURNING *""",
            (drive_file_id, drive_url, attachment_id)
        )

    @staticmethod
    def update_status(attachment_id, status, error_message=None):
        return execute(
            """UPDATE file_attachments SET status = %s, error_message = %s
               WHERE id = %s RETURNING *""",
            (status, error_message, attachment_id)
        )

    @staticmethod
    def find_by_id(attachment_id):
        return query_one("SELECT * FROM file_attachments WHERE id = %s", (attachment_id,))

    @staticmethod
    def find_by_message_id(message_id):
        return query_one("SELECT * FROM file_attachments WHERE message_id = %s", (message_id,))

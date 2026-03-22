# 🎙️ VoiceRoom - 음성 채팅방 STT 플랫폼

## 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                      Flutter App (Android/iOS)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Google   │  │ 채팅방    │  │ 음성파일  │  │ 실시간 메시지  │  │
│  │ 로그인   │  │ 목록/생성 │  │ 업로드   │  │ (WebSocket)   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬───────┘  │
└───────┼──────────────┼────────────┼─────────────────┼──────────┘
        │              │            │                 │
        ▼              ▼            ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Cafe24 서버 (goldenrabbit.biz)                  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Flask API Server                       │    │
│  │  /api/auth/*      - Google OAuth 인증                    │    │
│  │  /api/rooms/*     - 채팅방 CRUD                          │    │
│  │  /api/messages/*  - 메시지/댓글                           │    │
│  │  /api/stt/*       - 음성→텍스트 변환 (Whisper)           │    │
│  │  /ws              - WebSocket (실시간 메시지)             │    │
│  └────────────┬────────────────────┬───────────────────────┘    │
│               │                    │                             │
│  ┌────────────▼────┐  ┌───────────▼────────────┐               │
│  │  PostgreSQL DB  │  │  Whisper STT Engine    │               │
│  │  - users        │  │  - model: small        │               │
│  │  - rooms        │  │  - CPU 기반             │               │
│  │  - messages     │  │  - AI 파일명 파싱       │               │
│  │  - audio_files  │  └────────────────────────┘               │
│  │  - transcripts  │                                            │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────┐
│  Google Drive    │
│  API (음성 저장) │
└──────────────────┘
```

## DB 스키마

```sql
-- 사용자
users: id, google_id, email, name, avatar_url, created_at

-- 채팅방
rooms: id, name, description, created_by, created_at, updated_at

-- 채팅방 멤버
room_members: room_id, user_id, role(admin/member), joined_at

-- 메시지 (텍스트 + 음성 + 자동댓글)
messages: id, room_id, user_id, type(text/audio/transcript), 
          content, parent_id(댓글용), created_at

-- 음성 파일 기록
audio_files: id, message_id, room_id, user_id, 
             original_filename, drive_file_id, drive_url,
             phone_number, record_date, duration,
             transcript_text, status, created_at
```

## 핵심 플로우

### 1. 음성 파일 업로드 → 자동 변환 → 댓글
1) 사용자가 채팅방에서 음성파일 업로드
2) 서버에서 음성 메시지 생성 (채팅에 표시)
3) 백그라운드: Whisper로 STT 변환
4) 백그라운드: AI가 파일명에서 전화번호/날짜 파싱
5) 변환 완료 → 자동 댓글로 텍스트 달림
6) 음성파일 → Google Drive에 백업 저장
7) 메타데이터(전화번호, 날짜) DB에 저장

### 2. 파일명 AI 파싱 예시
- "홍길동_01012345678_상담.mp3" → 전화번호: 010-1234-5678, 이름: 홍길동
- "20250226 녹음.wav" → 기록날짜: 2025-02-26
- "상담녹음_2025년2월_010-9876-5432.m4a" → 전화번호: 010-9876-5432, 날짜: 2025-02
```

## 기술 스택

| 구분 | 기술 |
|------|------|
| 앱 | Flutter 3.x (Android + iOS) |
| 서버 | Flask + Flask-SocketIO |
| DB | PostgreSQL (기존 Cafe24 인프라 활용) |
| 인증 | Google Sign-In + JWT |
| STT | OpenAI Whisper (small, 무료) |
| 실시간 | WebSocket (Socket.IO) |
| 파일저장 | Google Drive API |
| 프로세스 | PM2 |

## 파일 구조

```
chat_stt/
├── server/
│   ├── app.py              # 메인 Flask 앱
│   ├── config.py           # 설정
│   ├── models.py           # DB 모델 (SQLAlchemy)
│   ├── auth.py             # Google OAuth + JWT
│   ├── routes_rooms.py     # 채팅방 API
│   ├── routes_messages.py  # 메시지/댓글 API
│   ├── routes_stt.py       # 음성변환 API
│   ├── stt_worker.py       # 백그라운드 STT 처리
│   ├── filename_parser.py  # AI 파일명 파싱
│   ├── drive_service.py    # Google Drive 업로드
│   ├── websocket.py        # 실시간 메시지
│   ├── init_db.sql         # DB 초기화
│   ├── requirements.txt
│   └── ecosystem.config.js # PM2 설정
│
└── flutter/
    └── (Flutter 프로젝트 전체)
```

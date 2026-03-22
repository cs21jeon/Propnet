# Proptalk Project Rules

## Architecture
- Flutter 3.x Android app + Flask backend (Cafe24 server 175.119.224.71:5060)
- PostgreSQL with psycopg2 connection pooling
- PM2 process management (ecosystem.config.js)
- SSH: `ssh cafe24-server` (root@175.119.224.71)

## CRITICAL: Whisper STT - OpenAI API ONLY
- **MUST use OpenAI Whisper API (`whisper-1` model) via `whisper_service.py`**
- **NEVER use local whisper model (import whisper / whisper.load_model)**
- The server has only 956MB RAM - local Whisper crashes with oneDNN errors
- `whisper_service.py` on server handles: format conversion, file splitting, API calls
- Usage: `from whisper_service import transcribe_audio`
- Returns: `{'text': '...', 'segments': [...]}`
- OPENAI_API_KEY is configured in ecosystem.config.js

## Deploy
- Server files: `/home/webapp/goldenrabbit/chat_stt/server/`
- SCP then `pm2 restart voiceroom`
- Config: `ecosystem.config.js` (env vars, PM2 settings)

## Key Server Files
- `routes_messages.py` - message/audio upload/download endpoints
- `whisper_service.py` - OpenAI Whisper API wrapper (DO NOT replace with local whisper)
- `claude_service.py` - Claude API for transcript summarization
- `models.py` - DB models (User, Room, Message, AudioFile)
- `billing_service.py` - usage billing/deduction

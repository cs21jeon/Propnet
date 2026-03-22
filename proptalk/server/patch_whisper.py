"""whisper_service.py 패치 - 비지원 포맷 자동 변환 추가"""
import sys

filepath = "/home/webapp/goldenrabbit/chat_stt/server/whisper_service.py"

with open(filepath, "r") as f:
    content = f.read()

# 1) 변환 함수 추가 (get_audio_duration 앞에)
convert_func = '''
# Whisper API 지원 포맷
WHISPER_SUPPORTED = {".flac", ".m4a", ".mp3", ".mp4", ".mpeg", ".mpga", ".oga", ".ogg", ".wav", ".webm"}

def convert_to_supported_format(file_path: str) -> str:
    """비지원 포맷(3gp, amr 등)을 mp3로 변환"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in WHISPER_SUPPORTED:
        return file_path

    converted_path = file_path.rsplit(".", 1)[0] + ".mp3"
    logger.info(f"[Whisper] 포맷 변환: {ext} -> .mp3")

    result = subprocess.run([
        "ffmpeg", "-i", file_path,
        "-vn", "-acodec", "libmp3lame", "-q:a", "2",
        "-y", converted_path
    ], capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"[Whisper] 포맷 변환 실패: {result.stderr}")
        return file_path

    if os.path.exists(converted_path) and os.path.getsize(converted_path) > 0:
        return converted_path

    return file_path

'''

content = content.replace(
    "\ndef get_audio_duration",
    convert_func + "\ndef get_audio_duration"
)

# 2) transcribe_audio 시작 부분에 변환 호출 추가
old = "    openai_client = get_client()\n    \n    file_size"
new = """    openai_client = get_client()

    # 비지원 포맷 변환 (3gp, amr 등)
    file_path = convert_to_supported_format(file_path)

    file_size"""

content = content.replace(old, new, 1)

with open(filepath, "w") as f:
    f.write(content)

print("OK - whisper_service.py patched successfully")

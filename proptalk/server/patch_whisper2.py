"""whisper_service.py 패치2 - 실제 파일 포맷 감지 후 변환"""

filepath = "/home/webapp/goldenrabbit/chat_stt/server/whisper_service.py"

with open(filepath, "r") as f:
    content = f.read()

# 기존 convert_to_supported_format 함수를 교체
old_func = '''def convert_to_supported_format(file_path: str) -> str:
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

    return file_path'''

new_func = '''def detect_actual_format(file_path: str) -> str:
    """ffprobe로 실제 컨테이너 포맷 감지"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=format_name',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ], capture_output=True, text=True)
        fmt = result.stdout.strip().lower()
        logger.info(f"[Whisper] 실제 포맷 감지: {fmt}")
        return fmt
    except Exception:
        return ""


# 실제 컨테이너가 Whisper 비호환인 포맷들
INCOMPATIBLE_FORMATS = {"3gp", "3g2", "amr", "3gpp"}

def convert_to_supported_format(file_path: str) -> str:
    """실제 파일 포맷을 감지하여 비지원 포맷이면 mp3로 변환"""
    actual_fmt = detect_actual_format(file_path)

    needs_convert = False
    for fmt in INCOMPATIBLE_FORMATS:
        if fmt in actual_fmt:
            needs_convert = True
            break

    if not needs_convert:
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in WHISPER_SUPPORTED:
            needs_convert = True

    if not needs_convert:
        return file_path

    converted_path = file_path.rsplit(".", 1)[0] + ".mp3"
    logger.info(f"[Whisper] 포맷 변환: {actual_fmt} -> mp3")

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

    return file_path'''

content = content.replace(old_func, new_func)

with open(filepath, "w") as f:
    f.write(content)

print("OK - whisper_service.py patched v2")

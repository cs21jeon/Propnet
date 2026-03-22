"""패치: reply_content 마크다운 형식 정리"""

filepath = "/home/webapp/goldenrabbit/chat_stt/server/routes_messages.py"

with open(filepath, "r") as f:
    content = f.read()

old = '''                reply_content = f"📝 **통화 요약**\\n\\n{summary_text}\\n\\n───────────────────\\n\\n⚠️ **{Config.AUDIO_RETENTION_HOURS}시간 후 파일 삭제됩니다.**\\n저장이 필요하면 지금 다운로드 받으세요."
            else:
                reply_content = f"📝 음성 변환 완료\\n\\n요약을 생성하지 못했습니다.\\n\\n⚠️ {Config.AUDIO_RETENTION_HOURS}시간 후 파일 삭제됩니다.\\n저장이 필요하면 지금 다운로드 받으세요."'''

new = '''                reply_content = f"{summary_text}\\n\\n---\\n\\n⚠️ **{Config.AUDIO_RETENTION_HOURS}시간 후 파일이 삭제됩니다.** 저장이 필요하면 다운로드하세요."
            else:
                reply_content = f"📝 음성 변환 완료\\n\\n요약을 생성하지 못했습니다.\\n\\n---\\n\\n⚠️ **{Config.AUDIO_RETENTION_HOURS}시간 후 파일이 삭제됩니다.** 저장이 필요하면 다운로드하세요."'''

content = content.replace(old, new)

with open(filepath, "w") as f:
    f.write(content)

print("OK - routes_messages.py: reply format updated")

"""패치: 진행 메시지(내용 정리 중입니다) 완료 후 삭제"""

# 1) models.py에 Message.delete 추가
models_path = "/home/webapp/goldenrabbit/chat_stt/server/models.py"

with open(models_path, "r") as f:
    content = f.read()

if "def delete(" not in content:
    delete_method = '''
    @staticmethod
    def delete(message_id):
        """메시지 삭제"""
        return execute(
            "DELETE FROM messages WHERE id = %s RETURNING *",
            (message_id,)
        )
'''
    # get_replies 메서드 앞에 삽입
    content = content.replace(
        "    @staticmethod\n    def get_replies(",
        delete_method + "\n    @staticmethod\n    def get_replies("
    )

    with open(models_path, "w") as f:
        f.write(content)
    print("OK - models.py: Message.delete() added")
else:
    print("SKIP - models.py: Message.delete() already exists")


# 2) routes_messages.py에서 완료 후 progress_msg 삭제 + 소켓 이벤트 추가
routes_path = "/home/webapp/goldenrabbit/chat_stt/server/routes_messages.py"

with open(routes_path, "r") as f:
    content = f.read()

# reply_msg 생성 직전에 progress_msg 삭제 코드 추가
old_reply = """            if summary_text:
                reply_content = f"""

new_reply = """            # 진행 메시지 삭제
            try:
                Message.delete(progress_msg['id'])
                socketio.emit('delete_message', {
                    'message_id': progress_msg['id'],
                    'room_id': room_id,
                }, room=f'room_{room_id}')
            except Exception as e:
                logger.warning(f"[cleanup] 진행 메시지 삭제 실패: {e}")

            if summary_text:
                reply_content = f"""

content = content.replace(old_reply, new_reply, 1)

with open(routes_path, "w") as f:
    f.write(content)
print("OK - routes_messages.py: progress_msg delete added")

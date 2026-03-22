"""패치: socketio.emit datetime 직렬화 오류 수정"""
from datetime import datetime

filepath = "/home/webapp/goldenrabbit/chat_stt/server/routes_messages.py"

with open(filepath, "r") as f:
    content = f.read()

# 1) datetime 변환 헬퍼 함수 추가 (import 후)
helper = '''
def _serialize_msg(msg):
    """메시지 dict의 datetime을 ISO 문자열로 변환"""
    result = {}
    for k, v in msg.items():
        if hasattr(v, 'isoformat'):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result

'''

content = content.replace(
    "logger = logging.getLogger(__name__)",
    "logger = logging.getLogger(__name__)\n" + helper
)

# 2) 모든 socketio.emit에서 **msg 사용하는 부분을 **_serialize_msg(msg)로 변환
# 패턴: **msg, **info_msg, **reply_msg, **progress_msg
import re
content = re.sub(
    r'\*\*(msg|info_msg|reply_msg|progress_msg)',
    r'**_serialize_msg(\1)',
    content
)

with open(filepath, "w") as f:
    f.write(content)

print("OK - routes_messages.py: datetime serialization fixed")

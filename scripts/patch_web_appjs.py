"""app.js에 deleteAccount 함수를 깨끗하게 추가"""

path = '/home/webapp/goldenrabbit/chat_stt/server/static/web/app.js'
with open(path, 'r') as f:
    content = f.read()

# 기존 한줄로 합쳐진 deleteAccount 제거
import re
content = re.sub(r'\ndeleteAccount\(\).*?\n        logout\(\)', '\n        deleteAccount() {\n'
    '            if (!confirm("정말 회원 탈퇴하시겠습니까?\\n모든 개인정보와 데이터가 즉시 삭제됩니다.")) return;\n'
    '            if (!confirm("이 작업은 되돌릴 수 없습니다.\\n정말 탈퇴하시겠습니까?")) return;\n'
    '            const token = localStorage.getItem("proptalk_token");\n'
    '            fetch("/voiceroom/api/auth/account", {\n'
    '                method: "DELETE",\n'
    '                headers: { "Authorization": "Bearer " + token },\n'
    '            })\n'
    '            .then(r => r.json())\n'
    '            .then(data => {\n'
    '                if (data.ok) {\n'
    '                    localStorage.removeItem("proptalk_token");\n'
    '                    localStorage.removeItem("proptalk_refresh_token");\n'
    '                    localStorage.removeItem("proptalk_user");\n'
    '                    alert("회원 탈퇴가 완료되었습니다.");\n'
    '                    window.location.href = "/proptalk/landing";\n'
    '                } else {\n'
    '                    alert("탈퇴 실패: " + (data.error || "알 수 없는 오류"));\n'
    '                }\n'
    '            })\n'
    '            .catch(() => alert("회원 탈퇴 중 오류가 발생했습니다."));\n'
    '        },\n'
    '\n'
    '        logout()', content, flags=re.DOTALL)

with open(path, 'w') as f:
    f.write(content)
print('Done')

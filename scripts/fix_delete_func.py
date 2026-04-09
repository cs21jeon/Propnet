"""deleteAccount 함수 영역을 깨끗하게 교체"""
path = '/home/webapp/goldenrabbit/chat_stt/server/static/web/app.js'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# deleteAccount 시작~logout 시작 사이를 찾아서 교체
start = None
end = None
for i, line in enumerate(lines):
    if 'deleteAccount()' in line and '{' in line:
        start = i
    if start is not None and 'logout()' in line and '{' in line and i > start:
        end = i
        break

if start is not None and end is not None:
    replacement = [
        '        deleteAccount() {\n',
        '            if (!confirm("정말 회원 탈퇴하시겠습니까?\\n모든 개인정보와 데이터가 즉시 삭제됩니다.")) return;\n',
        '            if (!confirm("이 작업은 되돌릴 수 없습니다.\\n정말 탈퇴하시겠습니까?")) return;\n',
        '            const token = localStorage.getItem("proptalk_token");\n',
        '            fetch("/voiceroom/api/auth/account", {\n',
        '                method: "DELETE",\n',
        '                headers: { "Authorization": "Bearer " + token },\n',
        '            })\n',
        '            .then(r => r.json())\n',
        '            .then(data => {\n',
        '                if (data.ok) {\n',
        '                    localStorage.removeItem("proptalk_token");\n',
        '                    localStorage.removeItem("proptalk_refresh_token");\n',
        '                    localStorage.removeItem("proptalk_user");\n',
        '                    alert("회원 탈퇴가 완료되었습니다.");\n',
        '                    window.location.href = "/proptalk/landing";\n',
        '                } else {\n',
        '                    alert("탈퇴 실패: " + (data.error || "알 수 없는 오류"));\n',
        '                }\n',
        '            })\n',
        '            .catch(() => alert("회원 탈퇴 중 오류가 발생했습니다."));\n',
        '        },\n',
        '\n',
    ]
    lines[start:end] = replacement
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f'Replaced lines {start+1}~{end+1} with clean deleteAccount()')
else:
    print(f'ERROR: start={start}, end={end}')

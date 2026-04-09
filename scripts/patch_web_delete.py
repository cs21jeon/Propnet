"""Proptalk 웹앱 설정 패널에 회원탈퇴 버튼 + deleteAccount() 함수 추가"""

path = '/home/webapp/goldenrabbit/chat_stt/server/templates/web/app.html'
with open(path, 'r') as f:
    content = f.read()

# 1. 설정 패널 로그아웃 버튼 뒤에 탈퇴 버튼 추가
old_logout = '''                </button>
            </div>
        </div>
    </div>

    <!-- Create Room Modal -->'''

new_logout = '''                </button>
                <button class="btn btn-ghost" @click="deleteAccount()" style="width:100%;margin-top:8px;color:#dc3545;font-size:13px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#dc3545" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg> 회원탈퇴
                </button>
            </div>
        </div>
    </div>

    <!-- Create Room Modal -->'''

if old_logout in content:
    content = content.replace(old_logout, new_logout, 1)
    print('Settings panel: delete button added')
else:
    print('ERROR: logout block not found')

# 2. deleteAccount() 함수 추가 (logout 함수 근처에)
if 'deleteAccount' not in content:
    old_func = '''            async logout() {'''
    new_func = '''            async deleteAccount() {
                if (!confirm('정말 회원 탈퇴하시겠습니까?\\n모든 개인정보와 데이터가 즉시 삭제됩니다.')) return;
                if (!confirm('이 작업은 되돌릴 수 없습니다.\\n정말 탈퇴하시겠습니까?')) return;
                try {
                    const res = await fetch(this.API_BASE + '/api/auth/account', {
                        method: 'DELETE',
                        headers: { 'Authorization': 'Bearer ' + this.token },
                    });
                    const data = await res.json();
                    if (data.ok) {
                        alert('회원 탈퇴가 완료되었습니다.');
                        localStorage.removeItem('proptalk_token');
                        localStorage.removeItem('proptalk_refresh');
                        window.location.href = '/proptalk/landing';
                    } else {
                        alert('탈퇴 실패: ' + (data.error || '알 수 없는 오류'));
                    }
                } catch (e) {
                    alert('회원 탈퇴 중 오류가 발생했습니다.');
                }
            },

            async logout() {'''

    if old_func in content:
        content = content.replace(old_func, new_func, 1)
        print('deleteAccount() function added')
    else:
        print('ERROR: logout function not found')
else:
    print('deleteAccount already exists')

with open(path, 'w') as f:
    f.write(content)
print('Done')

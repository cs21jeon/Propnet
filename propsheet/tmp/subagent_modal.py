#!/usr/bin/env python3
"""Add subagent management modal to workspaces page"""

HTML_PATH = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(HTML_PATH, 'r') as f:
    html = f.read()

# 1. Add "팀 관리" button next to user menu (agent only)
old_user_menu_end = """                        <a href="/propsheet/auth/logout" class="btn-logout" title="로그아웃">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 14H3a1 1 0 01-1-1V3a1 1 0 011-1h3M11 11l3-3-3-3M14 8H6"/></svg>
                        </a>
                    </div>"""

new_user_menu_end = """                        <a href="/propsheet/auth/logout" class="btn-logout" title="로그아웃">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 14H3a1 1 0 01-1-1V3a1 1 0 011-1h3M11 11l3-3-3-3M14 8H6"/></svg>
                        </a>
                    </div>
                    {% if agent_info %}
                    <button class="btn-team" @click="openTeamModal()" title="서브에이전트 관리" style="display:flex;align-items:center;gap:4px;padding:6px 12px;border:1px solid var(--border);border-radius:6px;background:var(--surface);cursor:pointer;font-size:13px;color:var(--text-secondary);">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="6" cy="5" r="2.5"/><path d="M1 14c0-2.8 2.2-5 5-5s5 2.2 5 5"/><circle cx="12" cy="5" r="2"/><path d="M16 14c0-2.2-1.8-4-4-4-.7 0-1.4.2-2 .5"/></svg>
                        팀 관리
                    </button>
                    {% endif %}"""

if old_user_menu_end in html:
    html = html.replace(old_user_menu_end, new_user_menu_end, 1)
    print("1. Added 팀 관리 button")
else:
    print("1. WARN: user menu pattern not found")

# 2. Add team management modal HTML (before </body>)
team_modal = """
    <!-- Subagent Management Modal -->
    <div class="modal-backdrop" x-show="showTeamModal" @click="showTeamModal = false" x-cloak style="position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:1000;display:flex;align-items:center;justify-content:center;">
        <div class="modal" @click.stop style="background:#fff;border-radius:12px;padding:24px;width:480px;max-width:90vw;max-height:80vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.2);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h2 style="margin:0;font-size:18px;">서브에이전트 관리</h2>
                <button @click="showTeamModal = false" style="border:none;background:none;font-size:20px;cursor:pointer;color:var(--text-muted);">&times;</button>
            </div>

            <div style="font-size:13px;color:var(--text-secondary);margin-bottom:16px;">
                슬롯: <strong x-text="teamData.remaining_slots"></strong>/<strong x-text="teamData.max_subagents"></strong> 사용 가능
            </div>

            <!-- Invite form -->
            <div style="border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:16px;background:var(--gray-50);">
                <div style="font-size:13px;font-weight:600;margin-bottom:8px;">이메일로 초대</div>
                <div style="display:flex;gap:8px;">
                    <input type="email" x-model="teamInviteEmail" placeholder="email@example.com"
                           style="flex:1;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:13px;">
                    <input type="text" x-model="teamInviteName" placeholder="이름 (선택)"
                           style="width:100px;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:13px;">
                    <button @click="inviteSubagent()" :disabled="!teamInviteEmail"
                            style="padding:8px 16px;background:var(--brand-blue,#667eea);color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;white-space:nowrap;">초대</button>
                </div>
                <div x-show="teamMessage" x-text="teamMessage"
                     style="margin-top:8px;font-size:12px;padding:6px 10px;border-radius:4px;"
                     :style="teamMessageType === 'error' ? 'background:#fee;color:#c00' : 'background:#efe;color:#060'"></div>
            </div>

            <!-- Active subagents -->
            <div style="margin-bottom:16px;">
                <div style="font-size:13px;font-weight:600;margin-bottom:8px;">활성 서브에이전트</div>
                <template x-if="teamData.subagents && teamData.subagents.length > 0">
                    <div>
                        <template x-for="sa in teamData.subagents" :key="sa.id">
                            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;border:1px solid var(--border);border-radius:6px;margin-bottom:6px;">
                                <div>
                                    <div style="font-size:13px;font-weight:500;" x-text="sa.name || sa.email"></div>
                                    <div style="font-size:11px;color:var(--text-muted);" x-text="sa.email"></div>
                                </div>
                                <button @click="removeSubagent(sa.id, sa.name || sa.email)"
                                        style="padding:4px 10px;border:1px solid #e57373;color:#c62828;background:#fff;border-radius:4px;cursor:pointer;font-size:12px;">해제</button>
                            </div>
                        </template>
                    </div>
                </template>
                <template x-if="!teamData.subagents || teamData.subagents.length === 0">
                    <div style="font-size:13px;color:var(--text-muted);padding:8px;">등록된 서브에이전트가 없습니다</div>
                </template>
            </div>

            <!-- Pending invites -->
            <div>
                <div style="font-size:13px;font-weight:600;margin-bottom:8px;">대기 중 초대</div>
                <template x-if="teamData.requests && teamData.requests.filter(r => r.status === 'pending').length > 0">
                    <div>
                        <template x-for="req in teamData.requests.filter(r => r.status === 'pending')" :key="req.id">
                            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;border:1px dashed var(--border);border-radius:6px;margin-bottom:6px;background:var(--gray-50);">
                                <div>
                                    <div style="font-size:13px;" x-text="req.email"></div>
                                    <div style="font-size:11px;color:var(--text-muted);" x-text="'초대일: ' + (req.requested_at || '').slice(0, 10)"></div>
                                </div>
                                <button @click="cancelInvite(req.id)"
                                        style="padding:4px 10px;border:1px solid var(--border);color:var(--text-secondary);background:#fff;border-radius:4px;cursor:pointer;font-size:12px;">취소</button>
                            </div>
                        </template>
                    </div>
                </template>
                <template x-if="!teamData.requests || teamData.requests.filter(r => r.status === 'pending').length === 0">
                    <div style="font-size:13px;color:var(--text-muted);padding:8px;">대기 중인 초대가 없습니다</div>
                </template>
            </div>
        </div>
    </div>

"""

if 'showTeamModal' not in html:
    html = html.replace('</body>', team_modal + '</body>', 1)
    print("2. Added team management modal HTML")
else:
    print("2. Modal already exists")

# 3. Add Alpine.js state and methods for team modal
# Find propSheetApp function and add state + methods
old_app_search = "showWorkspaceModal:"
app_idx = html.find(old_app_search)
if app_idx > 0:
    # Add team state after showWorkspaceModal
    team_state = """showTeamModal: false,
                teamData: { subagents: [], requests: [], max_subagents: 0, remaining_slots: 0 },
                teamInviteEmail: '',
                teamInviteName: '',
                teamMessage: '',
                teamMessageType: '',
                """
    if 'showTeamModal' not in html[:app_idx + 200]:
        html = html.replace(old_app_search, team_state + old_app_search, 1)
        print("3a. Added team state to Alpine data")

# Add team methods - find a good insertion point
# Look for loadWorkspaces or similar function
methods_code = """
                async openTeamModal() {
                    this.showTeamModal = true;
                    this.teamMessage = '';
                    try {
                        const res = await fetch('/propsheet/api/agent/subagents');
                        const data = await res.json();
                        if (data.success) {
                            this.teamData = data;
                        }
                    } catch (e) {
                        console.error('Failed to load team data:', e);
                    }
                },

                async inviteSubagent() {
                    if (!this.teamInviteEmail) return;
                    this.teamMessage = '';
                    try {
                        const res = await fetch('/propsheet/api/agent/invite-subagent', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email: this.teamInviteEmail, name: this.teamInviteName })
                        });
                        const data = await res.json();
                        if (data.success) {
                            this.teamMessage = data.message;
                            this.teamMessageType = 'success';
                            this.teamInviteEmail = '';
                            this.teamInviteName = '';
                            await this.openTeamModal(); // refresh
                        } else {
                            this.teamMessage = data.error;
                            this.teamMessageType = 'error';
                        }
                    } catch (e) {
                        this.teamMessage = '초대 실패: ' + e.message;
                        this.teamMessageType = 'error';
                    }
                },

                async removeSubagent(userId, name) {
                    if (!confirm(name + ' 서브에이전트를 해제하시겠습니까?')) return;
                    try {
                        const res = await fetch('/propsheet/api/agent/remove-subagent/' + userId, { method: 'DELETE' });
                        const data = await res.json();
                        if (data.success) {
                            await this.openTeamModal();
                        }
                    } catch (e) {}
                },

                async cancelInvite(requestId) {
                    if (!confirm('초대를 취소하시겠습니까?')) return;
                    try {
                        const res = await fetch('/propsheet/api/agent/cancel-invite/' + requestId, { method: 'DELETE' });
                        const data = await res.json();
                        if (data.success) {
                            await this.openTeamModal();
                        }
                    } catch (e) {}
                },

"""

if 'openTeamModal' not in html:
    # Insert before loadWorkspaces
    html = html.replace(
        '                async loadWorkspaces()',
        methods_code + '                async loadWorkspaces()',
        1
    )
    print("3b. Added team management methods")
else:
    print("3b. Team methods already exist")

with open(HTML_PATH, 'w') as f:
    f.write(html)

print("\nDone!")

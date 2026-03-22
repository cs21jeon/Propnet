#!/usr/bin/env python3
"""Add team modal state + methods to workspaces.js"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(path, 'r') as f:
    js = f.read()

# 1. Add team state to Alpine data
old_state = "                membersWorkspace: null,"
new_state = """                membersWorkspace: null,
                showTeamModal: false,
                teamData: { subagents: [], requests: [], max_subagents: 0, remaining_slots: 0 },
                teamInviteEmail: '',
                teamInviteName: '',
                teamMessage: '',
                teamMessageType: '',"""

if 'showTeamModal' not in js:
    js = js.replace(old_state, new_state, 1)
    print("1. Added team state to Alpine data")
else:
    print("1. Team state already exists")

# 2. Add team methods
team_methods = """
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
                            await this.openTeamModal();
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
                        if (data.success) await this.openTeamModal();
                    } catch (e) {}
                },

                async cancelInvite(requestId) {
                    if (!confirm('초대를 취소하시겠습니까?')) return;
                    try {
                        const res = await fetch('/propsheet/api/agent/cancel-invite/' + requestId, { method: 'DELETE' });
                        const data = await res.json();
                        if (data.success) await this.openTeamModal();
                    } catch (e) {}
                },

"""

if 'openTeamModal' not in js:
    # Insert before loadWorkspaces
    js = js.replace(
        '                async loadWorkspaces()',
        team_methods + '                async loadWorkspaces()',
        1
    )
    print("2. Added team methods to workspaces.js")
else:
    print("2. Team methods already exist")

# 3. Remove duplicate methods from workspaces.html if they were added there
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(html_path, 'r') as f:
    html = f.read()

# Remove the methods block that was incorrectly added to HTML
import re
# Find and remove the block between "async openTeamModal" and "async loadWorkspaces" in HTML
if 'async openTeamModal()' in html:
    pattern = r'\n\s*async openTeamModal\(\).*?async cancelInvite.*?\},\n'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        html = html.replace(match.group(0), '\n', 1)
        print("3. Removed duplicate methods from HTML")

with open(html_path, 'w') as f:
    f.write(html)

with open(path, 'w') as f:
    f.write(js)

# 4. Verify JS syntax
import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
if result.returncode == 0:
    print("\nJS syntax: OK")
else:
    print(f"\nJS ERROR:\n{result.stderr}")

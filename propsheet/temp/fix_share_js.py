#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(path, "r") as f:
    content = f.read()

changes = 0

# 1. Add share state variables
old_state = "                columnWidths: {},"
new_state = """                columnWidths: {},
                showShareModal: false,
                shareLinks: [],"""

if "showShareModal" not in content:
    content = content.replace(old_state, new_state, 1)
    changes += 1
    print("1. Added share state variables")

# 2. Add share functions before exportCSV
old_export = "                async exportCSV() {"
new_funcs = """                async createShareLink() {
                    try {
                        const wsSlug = window.WS_SLUG;
                        const dbSlug = window.DB_SLUG;
                        if (!wsSlug || !dbSlug) {
                            this.showToast('워크스페이스/DB 정보를 찾을 수 없습니다', 'error');
                            return;
                        }
                        const res = await fetch(`/propsheet/api/workspace/${wsSlug}/database/${dbSlug}/share`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' }
                        });
                        const data = await res.json();
                        if (data.success) {
                            this.showToast('공유 링크가 생성되었습니다', 'success');
                            await this.loadShareLinks();
                        } else {
                            this.showToast(data.error || '생성 실패', 'error');
                        }
                    } catch (err) {
                        this.showToast('오류: ' + err.message, 'error');
                    }
                },

                async loadShareLinks() {
                    try {
                        const wsSlug = window.WS_SLUG;
                        const dbSlug = window.DB_SLUG;
                        if (!wsSlug || !dbSlug) return;
                        const res = await fetch(`/propsheet/api/workspace/${wsSlug}/database/${dbSlug}/shares`);
                        const data = await res.json();
                        if (data.success) {
                            this.shareLinks = data.shares;
                        }
                    } catch (err) {
                        console.error('Failed to load share links:', err);
                    }
                },

                copyShareLink(token) {
                    const url = window.location.origin + '/propsheet/share/' + token;
                    navigator.clipboard.writeText(url).then(() => {
                        this.showToast('링크가 복사되었습니다', 'success');
                    }).catch(() => {
                        // Fallback
                        const input = document.createElement('input');
                        input.value = url;
                        document.body.appendChild(input);
                        input.select();
                        document.execCommand('copy');
                        document.body.removeChild(input);
                        this.showToast('링크가 복사되었습니다', 'success');
                    });
                },

                async deactivateShareLink(shareId) {
                    if (!confirm('이 공유 링크를 삭제하시겠습니까?')) return;
                    try {
                        const res = await fetch(`/propsheet/api/share/${shareId}`, { method: 'DELETE' });
                        const data = await res.json();
                        if (data.success) {
                            this.showToast('공유 링크가 삭제되었습니다', 'success');
                            await this.loadShareLinks();
                        } else {
                            this.showToast(data.error || '삭제 실패', 'error');
                        }
                    } catch (err) {
                        this.showToast('오류: ' + err.message, 'error');
                    }
                },

                async exportCSV() {"""

if "createShareLink" not in content:
    content = content.replace(old_export, new_funcs, 1)
    changes += 1
    print("2. Added share functions")

# 3. Load share links when modal opens - use Alpine watch via x-effect in template instead
# We'll add loadShareLinks() call in the showShareModal setter by modifying the init
# Simpler: just add a $watch in init
old_init_end = "                    this.loadData();"
new_init_end = """                    this.loadData();

                    // Watch for share modal open
                    this.$watch('showShareModal', (val) => {
                        if (val) this.loadShareLinks();
                    });"""

if "$watch('showShareModal'" not in content:
    # Find the last occurrence in init() - the one after applyColumnOrder / view loading
    # Let's find a more specific location
    pass

with open(path, "w") as f:
    f.write(content)

print(f"\nTotal changes: {changes}")

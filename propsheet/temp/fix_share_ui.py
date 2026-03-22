#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html"
with open(path, "r") as f:
    content = f.read()

changes = 0

# 1. Add workspace slug variables to JS globals
old_globals = "        window.DATABASE_ID = {{ database.id if database else 1 }};"
new_globals = """        window.DATABASE_ID = {{ database.id if database else 1 }};
        window.WS_SLUG = '{{ workspace.slug if workspace else "" }}';
        window.DB_SLUG = '{{ database.slug if database else "" }}';"""

if "WS_SLUG" not in content:
    content = content.replace(old_globals, new_globals, 1)
    changes += 1
    print("1. Added WS_SLUG/DB_SLUG globals")

# 2. Add share button next to CSV export
old_btns = """            <button class="btn-secondary" @click="exportCSV()">CSV 내보내기</button>
        </div>"""
new_btns = """            <button class="btn-secondary" @click="exportCSV()">CSV 내보내기</button>
            <button class="btn-secondary btn-share" @click="showShareModal = true" title="공유 링크 생성">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -2px; margin-right: 4px;"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>공유
            </button>
        </div>"""

if "btn-share" not in content:
    content = content.replace(old_btns, new_btns, 1)
    changes += 1
    print("2. Added share button")

# 3. Add share modal before closing </body>
share_modal = """
    <!-- Share Modal -->
    <div x-show="showShareModal" x-cloak
         style="position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:1000;display:flex;align-items:center;justify-content:center;"
         @click.self="showShareModal = false">
        <div style="background:#fff;border-radius:12px;width:480px;max-width:90vw;max-height:80vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,0.15);">
            <div style="padding:20px 24px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center;">
                <h3 style="font-size:16px;font-weight:600;margin:0;">데이터베이스 공유</h3>
                <button @click="showShareModal = false" style="background:none;border:none;font-size:20px;cursor:pointer;color:#999;">&times;</button>
            </div>
            <div style="padding:24px;">
                <!-- Create new share -->
                <button @click="createShareLink()" class="btn-primary"
                        style="width:100%;padding:12px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;background:#2E86DE;color:#fff;border:none;margin-bottom:20px;">
                    + 새 공유 링크 생성 (7일 유효)
                </button>

                <!-- Existing shares -->
                <div style="font-size:13px;color:#666;margin-bottom:12px;">활성 공유 링크</div>
                <template x-if="shareLinks.length === 0">
                    <div style="text-align:center;color:#999;padding:16px;font-size:13px;">공유 링크가 없습니다</div>
                </template>
                <template x-for="link in shareLinks" :key="link.id">
                    <div style="display:flex;align-items:center;gap:8px;padding:10px 12px;background:#f8f9fa;border-radius:8px;margin-bottom:8px;">
                        <span :style="'width:8px;height:8px;border-radius:50%;flex-shrink:0;background:' + (link.status === 'active' ? '#27ae60' : '#999')"></span>
                        <div style="flex:1;min-width:0;">
                            <div style="font-size:13px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                                 x-text="window.location.origin + '/propsheet/share/' + link.share_token"></div>
                            <div style="font-size:11px;color:#999;margin-top:2px;">
                                <span x-text="'복제 ' + link.clone_count + '회'"></span> ·
                                <span x-text="link.status === 'active' ? '만료: ' + new Date(link.expires_at).toLocaleDateString('ko') : (link.status === 'expired' ? '만료됨' : '비활성')"></span>
                            </div>
                        </div>
                        <button x-show="link.status === 'active'" @click="copyShareLink(link.share_token)"
                                style="padding:6px 10px;background:#2E86DE;color:#fff;border:none;border-radius:6px;font-size:12px;cursor:pointer;white-space:nowrap;">복사</button>
                        <button x-show="link.status === 'active'" @click="deactivateShareLink(link.id)"
                                style="padding:6px 10px;background:#e74c3c;color:#fff;border:none;border-radius:6px;font-size:12px;cursor:pointer;white-space:nowrap;">삭제</button>
                    </div>
                </template>
            </div>
        </div>
    </div>
"""

if "showShareModal" not in content:
    content = content.replace("</body>", share_modal + "\n</body>", 1)
    changes += 1
    print("3. Added share modal")

with open(path, "w") as f:
    f.write(content)

print(f"\nTotal changes: {changes}")

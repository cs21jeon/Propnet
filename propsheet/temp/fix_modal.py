#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html"
with open(path, "r") as f:
    content = f.read()

modal_html = '''
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
                <button @click="createShareLink()" class="btn-primary"
                        style="width:100%;padding:12px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;background:#2E86DE;color:#fff;border:none;margin-bottom:20px;">
                    + 새 공유 링크 생성 (7일 유효)
                </button>
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
                                <span x-text="'복제 ' + link.clone_count + '회'"></span> &middot;
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
'''

# Insert before </body>
if 'Share Modal' not in content:
    content = content.replace('\n</body>', modal_html + '\n</body>', 1)
    with open(path, "w") as f:
        f.write(content)
    print("OK - Share modal added")
else:
    print("Already exists")

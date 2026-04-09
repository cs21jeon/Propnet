#!/usr/bin/env python3
"""Patch homepage map.html: Add property classification guide popup"""
import shutil, sys

FILE = '/home/webapp/goldenrabbit/frontend/public/map.html'
with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

shutil.copy(FILE, FILE + '.bak_guide')

# 1. CSS
css_add = """
        /* 분류 안내 링크 */
        .guide-link {
            display: block; width: 100%; padding: 3px 0; border: none;
            background: none; cursor: pointer; font-size: 10px; font-weight: 600;
            color: #94a3b8; text-align: center; font-family: -apple-system, sans-serif;
            text-decoration: underline dotted; text-underline-offset: 2px;
        }
        .guide-link:hover { color: #64748b; }
        .guide-overlay {
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.45); z-index: 20000;
            display: none; align-items: center; justify-content: center; padding: 16px;
        }
        .guide-overlay.active { display: flex; }
        .guide-modal {
            background: white; border-radius: 14px; max-width: 380px; width: 100%;
            max-height: 80vh; overflow-y: auto; padding: 20px; position: relative;
            box-shadow: 0 8px 30px rgba(0,0,0,0.2);
        }
        .guide-close {
            position: absolute; top: 10px; right: 10px; width: 28px; height: 28px;
            border: none; background: #f1f5f9; border-radius: 6px; cursor: pointer;
            font-size: 14px; display: flex; align-items: center; justify-content: center; color: #64748b;
        }
        .guide-title { font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 14px; }
        .guide-card { border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin-bottom: 10px; }
        .guide-card-head { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
        .guide-badge { padding: 2px 8px; border-radius: 5px; font-size: 11px; font-weight: 700; color: white; }
        .guide-badge.danil { background: #1D4ED8; }
        .guide-badge.jibhap { background: #15803D; }
        .guide-badge.bubun { background: #EA580C; }
        .guide-card-name { font-size: 13px; font-weight: 700; color: #0f172a; }
        .guide-card-desc { font-size: 12px; color: #475569; line-height: 1.5; margin-bottom: 8px; }
        .guide-chips { display: flex; flex-wrap: wrap; gap: 4px; }
        .guide-chip { padding: 2px 7px; background: #f1f5f9; border-radius: 4px; font-size: 10px; font-weight: 600; color: #475569; }
        .guide-note { margin-top: 6px; font-size: 10px; color: #94a3b8; }
        .guide-footer { margin-top: 6px; padding-top: 10px; border-top: 1px solid #f1f5f9; font-size: 10px; color: #94a3b8; text-align: center; }
        .guide-footer a { color: #3b82f6; text-decoration: none; }

"""

old_css = '        /* \uc0c1\uc138 \ubaa8\ub2ec */\n        .detail-overlay {'
if old_css not in content:
    print('PATCH 1 CSS: FAIL'); sys.exit(1)
content = content.replace(old_css, css_add + old_css, 1)
print('PATCH 1 CSS: OK')

# 2. Button after bubun, before filter-divider
old_btn = '        </div>\n        <div class="filter-divider"></div>\n        <div class="filter-group-label">\uac70\ub798\uc720\ud615</div>'
new_btn = '        </div>\n        <button class="guide-link" id="btnGuide">\ubd80\ub3d9\uc0b0 \ubd84\ub958\ubc29\ubc95</button>\n        <div class="filter-divider"></div>\n        <div class="filter-group-label">\uac70\ub798\uc720\ud615</div>'
if old_btn not in content:
    print('PATCH 2 BTN: FAIL'); sys.exit(1)
content = content.replace(old_btn, new_btn, 1)
print('PATCH 2 BTN: OK')

# 3. Popup HTML before detail modal
popup_html = """
    <!-- \ubd84\ub958 \uc548\ub0b4 \ud31d\uc5c5 -->
    <div class="guide-overlay" id="guideOverlay">
        <div class="guide-modal">
            <button class="guide-close" id="guideClose">&#10005;</button>
            <div class="guide-title">\ubd80\ub3d9\uc0b0 \ubd84\ub958 \uccb4\uacc4</div>
            <div class="guide-card">
                <div class="guide-card-head">
                    <span class="guide-badge danil">\ub2e8\uc77c</span>
                    <span class="guide-card-name">\ub2e8\uc77c\ubd80\ub3d9\uc0b0</span>
                </div>
                <div class="guide-card-desc">\uc18c\uc720\uad8c\uc774 \ud558\ub098\uc778 \ud1a0\uc9c0 \ub610\ub294 \uac74\ubb3c. \ud1a0\uc9c0+\uac74\ubb3c\uc774 \ud568\uaed8 \uac70\ub798\ub429\ub2c8\ub2e4.</div>
                <div class="guide-chips">
                    <span class="guide-chip">\uc8fc\ud0dd</span>
                    <span class="guide-chip">\uac74\ubb3c</span>
                    <span class="guide-chip">\ud1a0\uc9c0</span>
                </div>
                <div class="guide-note">\ub4f1\uae30 1\uac74 | \ub9e4\ub9e4 \uc911\uc2ec</div>
            </div>
            <div class="guide-card">
                <div class="guide-card-head">
                    <span class="guide-badge jibhap">\uc9d1\ud569</span>
                    <span class="guide-card-name">\uc9d1\ud569\ubd80\ub3d9\uc0b0</span>
                </div>
                <div class="guide-card-desc">\uad6c\ubd84\uc18c\uc720\uad8c\uc774 \uc874\uc7ac\ud558\ub294 \ubd80\ub3d9\uc0b0. \uac01 \ud638\uc218\ub9c8\ub2e4 \ub3c5\ub9bd\ub41c \uc18c\uc720\uad8c\uc744 \uac00\uc9c0\uba70 \uac1c\ubcc4 \ub9e4\ub9e4\uac00 \uac00\ub2a5\ud569\ub2c8\ub2e4.</div>
                <div class="guide-chips">
                    <span class="guide-chip">\uc544\ud30c\ud2b8</span>
                    <span class="guide-chip">\ube4c\ub77c</span>
                    <span class="guide-chip">\uc624\ud53c\uc2a4\ud154</span>
                    <span class="guide-chip">\uc0c1\uac00</span>
                    <span class="guide-chip">\uc9c0\uc0b0</span>
                    <span class="guide-chip">\uae30\ud0c0</span>
                </div>
                <div class="guide-note">\ud638\uc218\ubcc4 \ubcc4\ub3c4 \ub4f1\uae30 | \ub9e4\ub9e4/\uc804\uc138/\uc6d4\uc138</div>
            </div>
            <div class="guide-card">
                <div class="guide-card-head">
                    <span class="guide-badge bubun">\ubd80\ubd84</span>
                    <span class="guide-card-name">\ubd80\ubd84\ubd80\ub3d9\uc0b0</span>
                </div>
                <div class="guide-card-desc">\ub2e8\uc77c\ubd80\ub3d9\uc0b0\uc758 \uc77c\ubd80\ub97c \uc784\ub300\ucc28\ud558\ub294 \uacbd\uc6b0. \uc784\ucc28\uad8c(\uc0ac\uc6a9 \uad8c\ub9ac)\uc774 \uac70\ub798 \ub300\uc0c1\uc774\uba70 \ubcf4\uc99d\uae08/\uc6d4\uc138\uac00 \ud575\uc2ec\uc785\ub2c8\ub2e4.</div>
                <div class="guide-chips">
                    <span class="guide-chip">\uc6d0\ub8f8</span>
                    <span class="guide-chip">1.5\ub8f8</span>
                    <span class="guide-chip">\ud22c\ub8f8</span>
                    <span class="guide-chip">3\ub8f8</span>
                    <span class="guide-chip">4\ub8f8\uc774\uc0c1</span>
                    <span class="guide-chip">\uc0c1\uac00</span>
                    <span class="guide-chip">\uc0ac\ubb34\uc2e4</span>
                </div>
                <div class="guide-note">\uc784\ucc28\uad8c \uac70\ub798 | \uc804\uc138/\uc6d4\uc138 \uc911\uc2ec</div>
            </div>
            <div class="guide-footer"><a href="https://propnet.kr/propsheet/guide/property-types" target="_blank">\uc790\uc138\ud55c \ubd84\ub958 \uac00\uc774\ub4dc \ubcf4\uae30</a></div>
        </div>
    </div>

"""

old_detail = '    <!-- \uc0c1\uc138 \ubaa8\ub2ec -->'
if old_detail not in content:
    print('PATCH 3 POPUP: FAIL'); sys.exit(1)
content = content.replace(old_detail, popup_html + old_detail, 1)
print('PATCH 3 POPUP: OK')

# 4. JS event handlers
old_js = """    document.getElementById('detailClose').onclick = closeDetail;
    document.getElementById('detailOverlay').onclick = function(e) {
        if (e.target === this) closeDetail();
    };
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeDetail();
    });"""

new_js = """    document.getElementById('detailClose').onclick = closeDetail;
    document.getElementById('detailOverlay').onclick = function(e) {
        if (e.target === this) closeDetail();
    };

    // \ubd84\ub958 \uc548\ub0b4 \ud31d\uc5c5
    document.getElementById('btnGuide').addEventListener('click', function() {
        document.getElementById('guideOverlay').classList.add('active');
    });
    document.getElementById('guideClose').onclick = function() {
        document.getElementById('guideOverlay').classList.remove('active');
    };
    document.getElementById('guideOverlay').onclick = function(e) {
        if (e.target === this) this.classList.remove('active');
    };

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeDetail();
            document.getElementById('guideOverlay').classList.remove('active');
        }
    });"""

if old_js not in content:
    print('PATCH 4 JS: FAIL'); sys.exit(1)
content = content.replace(old_js, new_js, 1)
print('PATCH 4 JS: OK')

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)
print('\nSUCCESS: All patches applied')

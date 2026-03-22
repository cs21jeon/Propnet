#!/usr/bin/env python3
"""Header: restore original center layout on left, broker card on right, vertical split"""
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(path, 'r') as f:
    html = f.read()

old_header = """        <div class="header" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;">
            <div class="header-left" style="display:flex;align-items:center;gap:16px;">
                <img src="{{ url_for('static', filename='images/propsheet-logo.png') }}" alt="Propsheet" class="header-logo">
                <div>
                    <h1 style="margin:0;">Propsheet</h1>
                    <p style="margin:0;">쉽게 관리하는 부동산 데이터베이스</p>
                </div>
                <button class="btn-add" @click="showWorkspaceModal = true" style="margin-left:8px;">
                    <span>+</span> 새 워크스페이스
                </button>
                <div class="user-menu" style="margin-left:8px;">
                    {% if session.get('avatar_url') %}
                    <img src="{{ session.get('avatar_url') }}" alt="avatar" class="user-avatar">
                    {% else %}
                    <div class="user-avatar-placeholder">{{ session.get('username', '?')[0] }}</div>
                    {% endif %}
                    <span class="user-name">{{ session.get('username', '') }}</span>
                    <a href="/propsheet/auth/logout" class="btn-logout" title="로그아웃">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 14H3a1 1 0 01-1-1V3a1 1 0 011-1h3M11 11l3-3-3-3M14 8H6"/></svg>
                    </a>
                </div>
            </div>
            <div class="broker-card">
                <div class="broker-card-inner">
                    <img src="{{ url_for('static', filename='images/logo_goldenrabbit.png') }}" alt="금토끼부동산" class="broker-logo">
                    <div class="broker-info">
                        <div class="broker-name">금토끼부동산</div>
                        <div class="broker-row">대표 전창성 · <a href="tel:0234717377">02.3471.7377</a></div>
                        <div class="broker-row">서울특별시 동작구 사당로16나길 55, 1층</div>
                        <div class="broker-row">등록번호 11590-2024-00048</div>
                    </div>
                </div>
            </div>
        </div>"""

new_header = """        <div class="header-wrapper">
            <div class="header">
                <div class="header-center">
                    <img src="{{ url_for('static', filename='images/propsheet-logo.png') }}" alt="Propsheet" class="header-logo">
                    <h1>Propsheet</h1>
                    <p>쉽게 관리하는 부동산 데이터베이스</p>
                </div>
                <div class="header-actions">
                    <button class="btn-add" @click="showWorkspaceModal = true">
                        <span>+</span> 새 워크스페이스
                    </button>
                    <div class="user-menu">
                        {% if session.get('avatar_url') %}
                        <img src="{{ session.get('avatar_url') }}" alt="avatar" class="user-avatar">
                        {% else %}
                        <div class="user-avatar-placeholder">{{ session.get('username', '?')[0] }}</div>
                        {% endif %}
                        <span class="user-name">{{ session.get('username', '') }}</span>
                        <a href="/propsheet/auth/logout" class="btn-logout" title="로그아웃">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 14H3a1 1 0 01-1-1V3a1 1 0 011-1h3M11 11l3-3-3-3M14 8H6"/></svg>
                        </a>
                    </div>
                </div>
            </div>
            <div class="broker-card">
                <img src="{{ url_for('static', filename='images/logo_goldenrabbit.png') }}" alt="금토끼부동산" class="broker-logo">
                <div class="broker-name">금토끼부동산</div>
                <div class="broker-row">대표 전창성</div>
                <div class="broker-row"><a href="tel:0234717377">02.3471.7377</a></div>
                <div class="broker-row">서울특별시 동작구<br>사당로16나길 55, 1층</div>
                <div class="broker-row">등록번호 11590-2024-00048</div>
            </div>
        </div>"""

if old_header in html:
    html = html.replace(old_header, new_header, 1)
    print("1. Replaced header with split layout")

with open(path, 'w') as f:
    f.write(html)

# CSS
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/workspaces.css'
with open(css_path, 'r') as f:
    css = f.read()

# Replace broker CSS with split layout
old_broker = """.broker-card {
    padding: 12px 16px;
    background: var(--gray-50, #f8f9fa);
    border: 1px solid var(--border, #e5e7eb);
    border-radius: 10px;
}
.broker-card-inner {
    display: flex;
    align-items: center;
    gap: 14px;
}
.broker-logo {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    object-fit: contain;
    flex-shrink: 0;
}
.broker-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.broker-name {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-primary, #1a1a1a);
}
.broker-row {
    font-size: 12px;
    color: var(--text-secondary, #666);
    line-height: 1.4;
}
.broker-row a {
    color: var(--brand-blue, #667eea);
    text-decoration: none;
}
.broker-row a:hover {
    text-decoration: underline;
}"""

new_broker = """.header-wrapper {
    display: flex;
    gap: 0;
    max-width: 1200px;
    margin: 0 auto 20px;
}
.header-wrapper > .header {
    flex: 1;
}
.broker-card {
    width: 200px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 16px;
    border-left: 1px solid var(--border, #e5e7eb);
    text-align: center;
}
.broker-logo {
    width: 52px;
    height: 52px;
    border-radius: 8px;
    object-fit: contain;
    margin-bottom: 4px;
}
.broker-name {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-primary, #1a1a1a);
}
.broker-row {
    font-size: 11px;
    color: var(--text-secondary, #666);
    line-height: 1.4;
}
.broker-row a {
    color: var(--brand-blue, #667eea);
    text-decoration: none;
}
.broker-row a:hover {
    text-decoration: underline;
}"""

if old_broker in css:
    css = css.replace(old_broker, new_broker, 1)
    print("2. Updated CSS for split layout")

with open(css_path, 'w') as f:
    f.write(css)

print("Done!")

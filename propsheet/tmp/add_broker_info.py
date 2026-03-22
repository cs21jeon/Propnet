#!/usr/bin/env python3
"""Add broker info card next to user menu"""
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(path, 'r') as f:
    html = f.read()

old_user_menu = """                <div class="user-menu">
                    {% if session.get('avatar_url') %}
                    <img src="{{ session.get('avatar_url') }}" alt="avatar" class="user-avatar">
                    {% else %}
                    <div class="user-avatar-placeholder">{{ session.get('username', '?')[0] }}</div>
                    {% endif %}
                    <span class="user-name">{{ session.get('username', '') }}</span>
                    <a href="/propsheet/auth/logout" class="btn-logout" title="로그아웃">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 14H3a1 1 0 01-1-1V3a1 1 0 011-1h3M11 11l3-3-3-3M14 8H6"/></svg>
                    </a>
                </div>"""

new_user_menu = """                <div class="broker-card">
                    <div class="broker-name">금토끼부동산</div>
                    <div class="broker-details">
                        <span>대표 전창성</span>
                        <span>·</span>
                        <a href="tel:0234717377">02.3471.7377</a>
                    </div>
                    <div class="broker-address">서울특별시 동작구 사당로16나길 55, 1층</div>
                </div>
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
                </div>"""

if 'broker-card' not in html:
    html = html.replace(old_user_menu, new_user_menu, 1)
    print("1. Added broker card to HTML")

with open(path, 'w') as f:
    f.write(html)

# CSS
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/workspaces.css'
with open(css_path, 'r') as f:
    css = f.read()

if '.broker-card' not in css:
    css += """
/* Broker info card */
.broker-card {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 8px 14px;
    background: var(--gray-50, #f8f9fa);
    border: 1px solid var(--border, #e5e7eb);
    border-radius: 8px;
    margin-right: 8px;
}
.broker-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary, #1a1a1a);
}
.broker-details {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--text-secondary, #666);
}
.broker-details a {
    color: var(--brand-blue, #667eea);
    text-decoration: none;
}
.broker-details a:hover {
    text-decoration: underline;
}
.broker-address {
    font-size: 11px;
    color: var(--text-muted, #999);
}
"""
    with open(css_path, 'w') as f:
        f.write(css)
    print("2. Added broker CSS")

print("Done!")

#!/usr/bin/env python3
import re

# === 1. HTML: Move favorite star outside database-actions (always visible) ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(html_path, 'r') as f:
    html = f.read()

# Remove fav button from inside database-actions
old_fav = """<div class="database-actions">
                                    <button @click.stop="toggleFavorite(db.id)" :title="isFavorite(db.id) ? '즐겨찾기 해제' : '즐겨찾기'" :class="{'fav-active': isFavorite(db.id)}" class="fav-btn">
                                        <span x-text="isFavorite(db.id) ? '★' : '☆'" style="font-size:16px;"></span>
                                    </button>
                                    <button @click.stop="duplicateDatabase(workspace, db)" title="복제">"""

new_actions_only = """<div class="database-actions">
                                    <button @click.stop="duplicateDatabase(workspace, db)" title="복제">"""

if old_fav in html:
    html = html.replace(old_fav, new_actions_only, 1)

# Add fav star as first child of database-card/database-list-item (always visible)
old_card_start = """:class="dbViewMode === 'list' ? 'database-list-item' : 'database-card'" @click="openDatabase(workspace.slug, db.slug, db.id)">"""
new_card_start = """:class="dbViewMode === 'list' ? 'database-list-item' : 'database-card'" @click="openDatabase(workspace.slug, db.slug, db.id)">
                                <button @click.stop="toggleFavorite(db.id)" class="fav-star" :class="{'fav-active': isFavorite(db.id)}" :title="isFavorite(db.id) ? '즐겨찾기 해제' : '즐겨찾기'">
                                    <span x-text="isFavorite(db.id) ? '★' : '☆'"></span>
                                </button>"""

if 'fav-star' not in html:
    html = html.replace(old_card_start, new_card_start, 1)
    print("1. HTML: Moved fav star to always-visible position")

# Bump
html = re.sub(r'workspaces\.js\?v=\w+', 'workspaces.js?v=20260317c', html)
html = re.sub(r'workspaces\.css\?v=\w+', 'workspaces.css?v=20260317c', html)

with open(html_path, 'w') as f:
    f.write(html)

# === 2. CSS: Always-visible star + list view left-aligned with actions on right ===
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/workspaces.css'
with open(css_path, 'r') as f:
    css = f.read()

# Remove old fav-btn styles and add new fav-star styles
css = css.replace(
    "/* Favorite button */\n.fav-btn { color: #ccc; transition: color 0.15s; }\n.fav-btn:hover, .fav-btn.fav-active { color: #f5a623; }",
    ""
)

if '.fav-star' not in css:
    css += """
/* Always-visible favorite star */
.fav-star {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 16px;
    color: #d0d0d0;
    padding: 0;
    line-height: 1;
    transition: color 0.15s, transform 0.15s;
    z-index: 2;
}
.fav-star:hover { color: #f5a623; transform: scale(1.2); }
.fav-star.fav-active { color: #f5a623; }

/* Card view: star in top-left corner */
.database-card .fav-star {
    position: absolute;
    top: 8px;
    left: 8px;
}

/* List view: star before icon, left-aligned */
.database-list-item .fav-star {
    flex-shrink: 0;
}
"""
    print("2a. Added fav-star CSS")

# Fix list view layout: left-aligned content, actions on right
css = css.replace(
    """.database-list-item .database-actions {
    position: static;
    display: flex;
    opacity: 0;
    transition: opacity 0.15s;
    gap: 4px;
}
.database-list-item:hover .database-actions { opacity: 1; }""",
    """.database-list-item .database-actions {
    position: static;
    display: flex;
    opacity: 0;
    transition: opacity 0.15s;
    gap: 4px;
    margin-left: auto;
    flex-shrink: 0;
}
.database-list-item:hover .database-actions { opacity: 1; }"""
)
print("2b. Fixed list view actions to right")

with open(css_path, 'w') as f:
    f.write(css)

print("\nDone!")

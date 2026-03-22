#!/usr/bin/env python3
"""Workspace UX: sort, view mode, favorites"""
import re

# === 1. JS: Add sort, view mode, favorites ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(js_path, 'r') as f:
    js = f.read()

# Add new state variables after error: ''
old_state = "error: '',"
new_state = """error: '',
                dbSortBy: localStorage.getItem('dbSortBy') || 'name',
                dbViewMode: localStorage.getItem('dbViewMode') || 'grid',
                favorites: JSON.parse(localStorage.getItem('dbFavorites') || '[]'),"""

if 'dbSortBy' not in js:
    js = js.replace(old_state, new_state, 1)
    print("1a. Added state vars")

# Add sort/favorite methods before loadWorkspaces
methods = '''
                toggleFavorite(dbId) {
                    const idx = this.favorites.indexOf(dbId);
                    if (idx >= 0) this.favorites.splice(idx, 1);
                    else this.favorites.push(dbId);
                    localStorage.setItem('dbFavorites', JSON.stringify(this.favorites));
                },

                isFavorite(dbId) {
                    return this.favorites.includes(dbId);
                },

                setDbSort(sort) {
                    this.dbSortBy = sort;
                    localStorage.setItem('dbSortBy', sort);
                    // Track last opened for "recent" sort
                },

                setDbView(mode) {
                    this.dbViewMode = mode;
                    localStorage.setItem('dbViewMode', mode);
                },

                trackOpen(dbId) {
                    const recent = JSON.parse(localStorage.getItem('dbRecent') || '{}');
                    recent[dbId] = Date.now();
                    localStorage.setItem('dbRecent', JSON.stringify(recent));
                },

                sortedDatabases(databases) {
                    if (!databases) return [];
                    const dbs = [...databases];
                    const favs = this.favorites;
                    const recent = JSON.parse(localStorage.getItem('dbRecent') || '{}');

                    // Sort
                    dbs.sort((a, b) => {
                        // Favorites always first
                        const aFav = favs.includes(a.id) ? 0 : 1;
                        const bFav = favs.includes(b.id) ? 0 : 1;
                        if (aFav !== bFav) return aFav - bFav;

                        if (this.dbSortBy === 'name') {
                            return (a.name || '').localeCompare(b.name || '', 'ko');
                        } else if (this.dbSortBy === 'recent') {
                            return (recent[b.id] || 0) - (recent[a.id] || 0);
                        } else if (this.dbSortBy === 'created') {
                            return (b.id || 0) - (a.id || 0);
                        }
                        return 0;
                    });
                    return dbs;
                },

'''

if 'toggleFavorite' not in js:
    js = js.replace('                async loadWorkspaces()', methods + '                async loadWorkspaces()')
    print("1b. Added methods")

# Update openDatabase to track recently opened
old_open = "openDatabase(workspaceSlug, dbSlug) {"
new_open = """openDatabase(workspaceSlug, dbSlug, dbId) {
                    if (dbId) this.trackOpen(dbId);"""
if 'trackOpen' not in js or 'dbId) {' not in js:
    js = js.replace(old_open, new_open, 1)
    print("1c. Updated openDatabase with tracking")

with open(js_path, 'w') as f:
    f.write(js)

# === 2. HTML: Add toolbar and update database rendering ===
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(html_path, 'r') as f:
    html = f.read()

# Add sort/view toolbar before workspaces-section
old_section = '<div class="workspaces-section">'
toolbar = """<div class="db-toolbar" style="display:flex;justify-content:flex-end;align-items:center;gap:12px;padding:0 20px 12px;max-width:1200px;margin:0 auto;">
            <div style="display:flex;align-items:center;gap:6px;">
                <span style="font-size:12px;color:var(--text-secondary);">정렬:</span>
                <button @click="setDbSort('name')" :class="{'active': dbSortBy==='name'}" class="tb-btn">이름순</button>
                <button @click="setDbSort('recent')" :class="{'active': dbSortBy==='recent'}" class="tb-btn">최근 열어본 순</button>
                <button @click="setDbSort('created')" :class="{'active': dbSortBy==='created'}" class="tb-btn">최근 생성순</button>
            </div>
            <div style="display:flex;align-items:center;gap:4px;">
                <button @click="setDbView('grid')" :class="{'active': dbViewMode==='grid'}" class="tb-btn" title="카드 보기">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="1" width="6" height="6" rx="1"/><rect x="9" y="1" width="6" height="6" rx="1"/><rect x="1" y="9" width="6" height="6" rx="1"/><rect x="9" y="9" width="6" height="6" rx="1"/></svg>
                </button>
                <button @click="setDbView('list')" :class="{'active': dbViewMode==='list'}" class="tb-btn" title="목록 보기">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="2" width="14" height="3" rx="1"/><rect x="1" y="7" width="14" height="3" rx="1"/><rect x="1" y="12" width="14" height="3" rx="1"/></svg>
                </button>
            </div>
        </div>
        <div class="workspaces-section">"""

if 'db-toolbar' not in html:
    html = html.replace(old_section, toolbar, 1)
    print("2a. Added toolbar")

# Update databases-grid to use sortedDatabases and support view modes
old_grid = """<div class="databases-grid" x-show="workspace.databases && workspace.databases.length > 0">
                        <template x-for="db in workspace.databases" :key="db.id">
                            <div class="database-card" @click="openDatabase(workspace.slug, db.slug)">"""

new_grid = """<div :class="dbViewMode === 'list' ? 'databases-list' : 'databases-grid'" x-show="workspace.databases && workspace.databases.length > 0">
                        <template x-for="db in sortedDatabases(workspace.databases)" :key="db.id">
                            <div :class="dbViewMode === 'list' ? 'database-list-item' : 'database-card'" @click="openDatabase(workspace.slug, db.slug, db.id)">"""

if 'sortedDatabases' not in html:
    html = html.replace(old_grid, new_grid, 1)
    print("2b. Updated grid with sort + view mode")

# Add favorite star button to database card
old_actions = """<div class="database-actions">
                                    <button @click.stop="duplicateDatabase(workspace, db)" title="복제">"""

new_actions = """<div class="database-actions">
                                    <button @click.stop="toggleFavorite(db.id)" :title="isFavorite(db.id) ? '즐겨찾기 해제' : '즐겨찾기'" :class="{'fav-active': isFavorite(db.id)}" class="fav-btn">
                                        <span x-text="isFavorite(db.id) ? '★' : '☆'" style="font-size:16px;"></span>
                                    </button>
                                    <button @click.stop="duplicateDatabase(workspace, db)" title="복제">"""

if 'toggleFavorite' not in html:
    html = html.replace(old_actions, new_actions, 1)
    print("2c. Added favorite button")

# Bump versions
html = re.sub(r'workspaces\.js\?v=\w+', 'workspaces.js?v=20260317b', html)
html = re.sub(r'workspaces\.css\?v=\w+', 'workspaces.css?v=20260317b', html)

with open(html_path, 'w') as f:
    f.write(html)

# === 3. CSS: Add toolbar + list view + favorite styles ===
css_path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/workspaces.css'
with open(css_path, 'r') as f:
    css = f.read()

if '.db-toolbar' not in css:
    css += """
/* Database toolbar */
.tb-btn {
    background: none;
    border: 1px solid transparent;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    color: var(--text-secondary, #888);
    cursor: pointer;
    transition: all 0.15s;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.tb-btn:hover { background: var(--gray-100, #f5f5f5); }
.tb-btn.active {
    background: var(--brand-blue, #667eea);
    color: white;
    border-color: var(--brand-blue, #667eea);
}

/* Favorite button */
.fav-btn { color: #ccc; transition: color 0.15s; }
.fav-btn:hover, .fav-btn.fav-active { color: #f5a623; }

/* List view */
.databases-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.database-list-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.15s;
    position: relative;
}
.database-list-item:hover { background: var(--gray-50, #fafafa); }
.database-list-item .database-icon { font-size: 20px; flex-shrink: 0; }
.database-list-item .database-name { font-size: 14px; font-weight: 500; flex: 1; }
.database-list-item .database-desc { font-size: 12px; color: var(--text-secondary, #888); flex: 2; }
.database-list-item .database-actions {
    position: static;
    display: flex;
    opacity: 0;
    transition: opacity 0.15s;
    gap: 4px;
}
.database-list-item:hover .database-actions { opacity: 1; }
"""
    with open(css_path, 'w') as f:
        f.write(css)
    print("3. Added CSS styles")

print("\nDone!")

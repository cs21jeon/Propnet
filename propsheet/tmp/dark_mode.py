#!/usr/bin/env python3
"""Implement dark mode for Propsheet"""

CSS_DB = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
CSS_WS = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/workspaces.css'
HTML_DB = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
HTML_WS = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
JS_DB = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'

DARK_VARS = """
/* ===== Dark Mode ===== */
[data-theme="dark"] {
    --primary: #5b9bf5;
    --primary-dark: #4a8ae4;
    --primary-light: #1e2a3a;
    --primary-50: #1a2535;

    --surface: #1a1d27;
    --background: #0f1117;

    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;

    --border: #2a2d3a;
    --border-light: #232636;

    --shadow-xs: 0 1px 2px rgba(0,0,0,0.2);
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
    --shadow-lg: 0 12px 40px rgba(0,0,0,0.5);

    --gray-50: #1e2130;
    --gray-100: #232636;
    --gray-200: #2a2d3a;
    --gray-300: #3a3d4a;
    --gray-400: #64748b;
    --gray-500: #94a3b8;
    --gray-600: #b0bec5;
    --gray-700: #cfd8dc;
    --gray-800: #e2e8f0;
    --gray-900: #f1f5f9;

    --brand-blue: #7c93ed;

    --success: #34d399;
    --success-light: #1a3a2a;
    --danger: #f87171;
    --danger-light: #3a1a1a;
    --warning: #fbbf24;

    color-scheme: dark;
}

[data-theme="dark"] body {
    background: var(--background);
    color: var(--text-primary);
}

[data-theme="dark"] .spreadsheet th {
    background: var(--gray-50) !important;
    color: var(--text-primary);
}

[data-theme="dark"] .spreadsheet td {
    background: var(--surface);
    color: var(--text-primary);
}

[data-theme="dark"] .spreadsheet tr:hover td {
    background: var(--primary-50) !important;
}

[data-theme="dark"] .detail-panel {
    background: var(--surface);
    color: var(--text-primary);
}

[data-theme="dark"] .detail-panel-overlay {
    background: rgba(0,0,0,0.7);
}

[data-theme="dark"] input,
[data-theme="dark"] select,
[data-theme="dark"] textarea {
    background: #252836;
    color: var(--text-primary);
    border-color: var(--gray-300);
}

[data-theme="dark"] .modal,
[data-theme="dark"] .modal-content {
    background: var(--surface);
    color: var(--text-primary);
}

[data-theme="dark"] .modal-backdrop {
    background: rgba(0,0,0,0.7) !important;
}

[data-theme="dark"] .cell-formula {
    background: #2a2520 !important;
}

[data-theme="dark"] .select-dropdown {
    background: var(--surface);
    border-color: var(--gray-300);
}

[data-theme="dark"] .select-option:hover {
    background: var(--gray-100);
}

[data-theme="dark"] .column-manager {
    background: var(--surface);
    border-color: var(--gray-300);
}

[data-theme="dark"] .filter-panel {
    background: var(--surface);
    border-color: var(--border);
}

[data-theme="dark"] .cell-edit-input {
    background: #252836 !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .floating-edit-container {
    background: #252836 !important;
    box-shadow: 0 0 0 2px var(--brand-blue) !important;
}

[data-theme="dark"] .toast {
    background: var(--surface);
    color: var(--text-primary);
    border-color: var(--gray-300);
}

[data-theme="dark"] .pagination button {
    background: var(--surface);
    color: var(--text-primary);
    border-color: var(--gray-300);
}

[data-theme="dark"] .btn-add {
    background: var(--brand-blue);
}

[data-theme="dark"] .detail-field-row {
    border-bottom-color: var(--border);
}

[data-theme="dark"] .detail-field-row.readonly {
    background: var(--gray-50);
}

[data-theme="dark"] .opt-row:hover {
    background: var(--gray-100);
}

[data-theme="dark"] .broker-card {
    background: var(--gray-50);
    border-color: var(--gray-300);
}

[data-theme="dark"] .history-popup,
[data-theme="dark"] .trash-modal {
    background: var(--surface);
    color: var(--text-primary);
}

/* Sticky columns dark */
[data-theme="dark"] .cell-checkbox,
[data-theme="dark"] .cell-expand {
    background: var(--surface) !important;
}
[data-theme="dark"] thead .cell-checkbox,
[data-theme="dark"] thead .cell-expand {
    background: var(--gray-50) !important;
}

/* Theme toggle button */
.theme-toggle {
    background: none;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 4px 8px;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
    color: var(--text-secondary);
}
.theme-toggle:hover {
    background: var(--gray-100);
}
"""

# ============================================================
# 1. Add dark mode CSS to database_list.css
# ============================================================
with open(CSS_DB, 'r') as f:
    css = f.read()

if 'Dark Mode' not in css:
    css += DARK_VARS
    with open(CSS_DB, 'w') as f:
        f.write(css)
    print("1a. Added dark mode CSS to database_list.css")

# Add to workspaces.css too
with open(CSS_WS, 'r') as f:
    css_ws = f.read()

DARK_WS = """
/* ===== Dark Mode ===== */
[data-theme="dark"] body {
    background: #0f1117;
    color: #e2e8f0;
}
[data-theme="dark"] .header-wrapper {
    background: #1a1d27;
}
[data-theme="dark"] .workspace-card {
    background: #1a1d27;
    border-color: #2a2d3a;
}
[data-theme="dark"] .workspace-card:hover {
    border-color: #3a3d4a;
}
[data-theme="dark"] .database-card {
    background: #252836;
}
[data-theme="dark"] .database-card:hover {
    background: #2a2d3a;
}
[data-theme="dark"] .modal-overlay {
    background: rgba(0,0,0,0.7);
}
[data-theme="dark"] .modal-content {
    background: #1a1d27;
    color: #e2e8f0;
}
[data-theme="dark"] input,
[data-theme="dark"] select,
[data-theme="dark"] textarea {
    background: #252836;
    color: #e2e8f0;
    border-color: #3a3d4a;
}
[data-theme="dark"] .broker-card {
    background: #1e2130;
    border-color: #2a2d3a;
}
[data-theme="dark"] .db-toolbar .tb-btn {
    background: #252836;
    color: #e2e8f0;
    border-color: #3a3d4a;
}
[data-theme="dark"] .user-menu {
    color: #e2e8f0;
}
.theme-toggle {
    background: none;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 4px 8px;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
    color: #94a3b8;
}
[data-theme="dark"] .theme-toggle {
    border-color: #3a3d4a;
}
.theme-toggle:hover {
    opacity: 0.8;
}
"""

if 'Dark Mode' not in css_ws:
    css_ws += DARK_WS
    with open(CSS_WS, 'w') as f:
        f.write(css_ws)
    print("1b. Added dark mode CSS to workspaces.css")

# ============================================================
# 2. Add theme toggle to HTML templates
# ============================================================

# database_list.html — add toggle button near logout
with open(HTML_DB, 'r') as f:
    html_db = f.read()

if 'theme-toggle' not in html_db:
    # Add toggle before logout button
    old_logout = '<a href="/propsheet/auth/logout" class="btn-logout" title="로그아웃">'
    new_logout = '''<button class="theme-toggle" @click="toggleTheme()" :title="darkMode ? '라이트 모드' : '다크 모드'" x-text="darkMode ? '☀️' : '🌙'"></button>
                        <a href="/propsheet/auth/logout" class="btn-logout" title="로그아웃">'''
    if old_logout in html_db:
        html_db = html_db.replace(old_logout, new_logout, 1)
        print("2a. Added theme toggle to database_list.html")

# Add theme init script
if 'initTheme' not in html_db:
    theme_script = '''
    <script>
        // Apply saved theme before Alpine loads (prevent flash)
        (function() {
            const saved = localStorage.getItem('propsheet-theme');
            if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
        })();
    </script>
'''
    html_db = html_db.replace('<head>', '<head>' + theme_script, 1)
    print("2b. Added theme init script to database_list.html")

# Bump version
html_db = html_db.replace("database_list.js') }}?v=1774004600", "database_list.js') }}?v=1774005000")
html_db = html_db.replace("database_list.css') }}?v=", "database_list.css') }}?v=1774005000____").replace("?v=1774005000____", "?v=1774005000")

with open(HTML_DB, 'w') as f:
    f.write(html_db)

# workspaces.html — add toggle
with open(HTML_WS, 'r') as f:
    html_ws = f.read()

if 'theme-toggle' not in html_ws:
    old_ws_logout = '<a href="/propsheet/auth/logout" class="btn-logout" title="로그아웃">'
    new_ws_logout = '''<button class="theme-toggle" onclick="const d=document.documentElement;const isDark=d.getAttribute('data-theme')==='dark';d.setAttribute('data-theme',isDark?'':'dark');localStorage.setItem('propsheet-theme',isDark?'light':'dark');this.textContent=isDark?'🌙':'☀️';">🌙</button>
                        <a href="/propsheet/auth/logout" class="btn-logout" title="로그아웃">'''
    if old_ws_logout in html_ws:
        html_ws = html_ws.replace(old_ws_logout, new_ws_logout, 1)
        print("2c. Added theme toggle to workspaces.html")

if 'initTheme' not in html_ws and 'propsheet-theme' not in html_ws:
    theme_script_ws = '''
    <script>
        (function() {
            const saved = localStorage.getItem('propsheet-theme');
            if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
        })();
    </script>
'''
    html_ws = html_ws.replace('<head>', '<head>' + theme_script_ws, 1)
    print("2d. Added theme init script to workspaces.html")

with open(HTML_WS, 'w') as f:
    f.write(html_ws)

# ============================================================
# 3. Add toggleTheme to JS (Alpine component)
# ============================================================
with open(JS_DB, 'r') as f:
    js = f.read()

if 'toggleTheme' not in js:
    # Add darkMode state
    js = js.replace(
        "                visibleColumns: [],",
        "                darkMode: localStorage.getItem('propsheet-theme') === 'dark',\n                visibleColumns: [],",
        1
    )

    # Add toggleTheme method
    toggle_method = """
                toggleTheme() {
                    this.darkMode = !this.darkMode;
                    if (this.darkMode) {
                        document.documentElement.setAttribute('data-theme', 'dark');
                        localStorage.setItem('propsheet-theme', 'dark');
                    } else {
                        document.documentElement.removeAttribute('data-theme');
                        localStorage.setItem('propsheet-theme', 'light');
                    }
                },

"""
    js = js.replace(
        '                async loadViews()',
        toggle_method + '                async loadViews()',
        1
    )
    print("3. Added toggleTheme to JS")

with open(JS_DB, 'w') as f:
    f.write(js)

# ============================================================
# 4. Fix hardcoded colors in HTML inline styles
# ============================================================
with open(HTML_DB, 'r') as f:
    html_db = f.read()

# Replace common hardcoded colors with CSS variables
replacements = [
    ('background:#fff', 'background:var(--surface)'),
    ('background: #fff', 'background:var(--surface)'),
    ('background:white', 'background:var(--surface)'),
    ('background: white', 'background:var(--surface)'),
    ('background:#f8f9fa', 'background:var(--gray-50)'),
    ('background: #f8f9fa', 'background:var(--gray-50)'),
]

for old_c, new_c in replacements:
    count = html_db.count(old_c)
    if count > 0:
        html_db = html_db.replace(old_c, new_c)
        print(f"4. Replaced {count}x: {old_c} -> {new_c}")

with open(HTML_DB, 'w') as f:
    f.write(html_db)

# Verify JS
import subprocess
result = subprocess.run(['node', '-c', JS_DB], capture_output=True, text=True)
print('\nJS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')

print("\nDone!")

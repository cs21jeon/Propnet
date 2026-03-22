#!/usr/bin/env python3
"""Add loading overlay that covers entire screen until rendering is complete"""

JS_PATH = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
HTML_PATH = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
CSS_PATH = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'

# ============================================================
# 1. JS: Add showOverlay state + $nextTick dismiss
# ============================================================
with open(JS_PATH, 'r') as f:
    js = f.read()

# Add showOverlay state
if 'showOverlay' not in js:
    js = js.replace(
        "                darkMode: localStorage.getItem('propsheet-theme') === 'dark',",
        "                darkMode: localStorage.getItem('propsheet-theme') === 'dark',\n                showOverlay: true,",
        1
    )
    print("1a. Added showOverlay state")

# In loadData success, use $nextTick to dismiss overlay
old_load = """                        if (data.success) {
                            this.items = data.items;
                            this.total = data.total;
                            this.pages = data.pages;"""

new_load = """                        if (data.success) {
                            this.items = data.items;
                            this.total = data.total;
                            this.pages = data.pages;
                            // Dismiss overlay after DOM rendering completes
                            this.$nextTick(() => { this.showOverlay = false; });"""

if old_load in js:
    js = js.replace(old_load, new_load, 1)
    print("1b. Added $nextTick overlay dismiss in loadData")
else:
    print("1b. WARN: loadData pattern not found")

# Show overlay when loading starts
old_loading_start = """                async loadData() {
                    this.loading = true;"""

new_loading_start = """                async loadData() {
                    this.loading = true;
                    this.showOverlay = true;"""

if old_loading_start in js:
    js = js.replace(old_loading_start, new_loading_start, 1)
    print("1c. Added showOverlay=true at loadData start")

# Also handle loadData error/empty
old_loading_end = """                    this.loading = false;
                },

                toggleSort"""

new_loading_end = """                    this.loading = false;
                    if (this.showOverlay) this.$nextTick(() => { this.showOverlay = false; });
                },

                toggleSort"""

if old_loading_end in js:
    js = js.replace(old_loading_end, new_loading_end, 1)
    print("1d. Added overlay dismiss at loadData end")

# Bump version
import re
with open(HTML_PATH, 'r') as f:
    html = f.read()
html = re.sub(r"database_list\.js'\) \}\}\?v=\d+", "database_list.js') }}?v=1774005300", html)
html = re.sub(r"database_list\.css'\) \}\}\?v=\d+", "database_list.css') }}?v=1774005300", html)

with open(JS_PATH, 'w') as f:
    f.write(js)

# ============================================================
# 2. HTML: Add overlay div
# ============================================================
overlay_html = """
    <!-- Loading Overlay -->
    <div x-show="showOverlay" x-cloak class="loading-overlay">
        <div class="loading-overlay-content">
            <div class="loading-overlay-spinner"></div>
            <span>로딩 중...</span>
        </div>
    </div>
"""

if 'loading-overlay' not in html:
    # Insert right after x-data div opening
    html = html.replace(
        '    <div class="header">',
        overlay_html + '    <div class="header">',
        1
    )
    print("2. Added loading overlay HTML")

with open(HTML_PATH, 'w') as f:
    f.write(html)

# ============================================================
# 3. CSS: Overlay styles
# ============================================================
with open(CSS_PATH, 'r') as f:
    css = f.read()

overlay_css = """
/* Loading Overlay */
.loading-overlay {
    position: fixed;
    inset: 0;
    background: rgba(255, 255, 255, 0.85);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(2px);
}
[data-theme="dark"] .loading-overlay {
    background: rgba(15, 17, 23, 0.85);
}
.loading-overlay-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    color: var(--text-secondary);
    font-size: 14px;
}
.loading-overlay-spinner {
    width: 36px;
    height: 36px;
    border: 3px solid var(--border);
    border-top-color: var(--brand-blue, #667eea);
    border-radius: 50%;
    animation: overlay-spin 0.8s linear infinite;
}
@keyframes overlay-spin {
    to { transform: rotate(360deg); }
}
"""

if 'loading-overlay' not in css:
    css += overlay_css
    with open(CSS_PATH, 'w') as f:
        f.write(css)
    print("3. Added overlay CSS")

# Verify JS
import subprocess
result = subprocess.run(['node', '-c', JS_PATH], capture_output=True, text=True)
print('\nJS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')

print("\nDone!")

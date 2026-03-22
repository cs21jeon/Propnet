#!/usr/bin/env python3
"""Add theme toggle to database_list.html header"""
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()

old = """            </button>
        </div>
    </div>

    <div class="toolbar">"""

# Find the right one (after 공유 button)
idx = html.find('공유\n            </button>\n        </div>\n    </div>\n\n    <div class="toolbar">')
if idx < 0:
    # Try alternate
    idx = html.find('공유\n            </button>')

if idx > 0:
    # Insert after the 공유 button
    insert_point = html.find('</button>\n        </div>\n    </div>', idx) + len('</button>')
    toggle_btn = '\n            <button class="theme-toggle" @click="toggleTheme()" :title="darkMode ? \'라이트 모드\' : \'다크 모드\'" x-text="darkMode ? \'☀️\' : \'🌙\'"></button>'
    html = html[:insert_point] + toggle_btn + html[insert_point:]
    print("Added theme toggle button to database_list.html header")
else:
    print("WARN: Could not find insertion point")

with open(path, 'w') as f:
    f.write(html)

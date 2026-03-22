#!/usr/bin/env python3
import re

path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(path, 'r') as f:
    js = f.read()

# Set workspaceIcons to exactly 101
ws_icons = """workspaceIcons: [
                    '📁','📂','📋','📊','📈','📉','🗂','🗃','📦','📚','📖','📝','📄','📑','🗄','💼',
                    '🏢','🏠','🏡','🏗','🏭','🏬','🏪','🏛','🏰','🏯','🗼','🛖','🏘','🏚',
                    '🎯','⭐','🌟','✨','💎','🔑','🔒','⚙','🛠','🔧','🔩','🧲',
                    '🚀','💡','🎨','🎭','🎪','🎬','📷','🎵','🎧','🎤','🎸','🎹',
                    '🌈','🌸','🌺','🌻','🌷','🌹','🍀','🌿','🌲','🌳','🌴','🌵',
                    '💰','💵','💴','💶','💷','💳','💸','🏦','💲','🪙',
                    '🔴','🟠','🟡','🟢','🔵','🟣','⚫','⚪','🟤',
                    '❤','🧡','💛','💚','💙','💜','🖤','🤍','🤎',
                    '🐕','🐈','🐎','🐘','🦁','🐻','🦊','🐼','🐨','🦄','🐝'
                ],"""

js = re.sub(r'workspaceIcons: \[[\s\S]*?\],', ws_icons, js, count=1)

with open(path, 'w') as f:
    f.write(js)

count = ws_icons.count("'") // 2
print(f"workspaceIcons: {count}")

# Bump version
path2 = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(path2, 'rb') as f:
    raw = f.read()
raw = raw.replace(b'v=20260317g', b'v=20260317h')
with open(path2, 'wb') as f:
    f.write(raw)
print("bumped to 20260317h")

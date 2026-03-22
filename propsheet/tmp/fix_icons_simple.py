#!/usr/bin/env python3
"""Reduce icon count and test - maybe 250 icons in x-for causes Alpine issue"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(path, 'r') as f:
    js = f.read()

import re

# Replace with smaller sets - 80 each, no ZWJ, no variation selectors
ws_icons = """workspaceIcons: [
                    '📁','📂','📋','📊','📈','📉','🗂','🗃','📦','📚','📖','📝','📄','📑','🗄','💼',
                    '🏢','🏠','🏡','🏗','🏭','🏬','🏪','🏛','🏰','🏯','🗼','🛖','🏘','🏚',
                    '🎯','⭐','🌟','✨','💎','🔑','🔒','⚙','🛠','🔧','🔩','🧲',
                    '🚀','💡','🎨','🎭','🎪','🎬','📷','🎵','🎧','🎤','🎸','🎹',
                    '🌈','🌸','🌺','🌻','🌷','🌹','🍀','🌿','🌲','🌳','🌴','🌵',
                    '💰','💵','💴','💶','💷','💳','💸','🏦','💲','🪙',
                    '🔴','🟠','🟡','🟢','🔵','🟣','⚫','⚪','🟤',
                    '❤','🧡','💛','💚','💙','💜','🖤','🤍','🤎'
                ],"""

db_icons = """databaseIcons: [
                    '📊','📈','📉','💹','💾','💿','📀','🗄','📋','📑','📝','📄','🗃','🗂','📦','📚',
                    '🏢','🏠','🏡','🏗','🏭','🏬','🏪','🏛','🏰','🏯','🗼','🛖','🏘','🏚',
                    '💰','💵','💴','💶','💷','💳','💸','🏦','🪙','💲',
                    '🔑','🔐','🔒','🔓','🗝','⚙','🛠','🔧','🔩','🧲',
                    '🎯','⭐','🌟','✨','💎','❤','🧡','💛','💚','💙','💜','🖤',
                    '🔴','🟠','🟡','🟢','🔵','🟣','⚫','⚪','🟤',
                    '📁','📂','📚','📖','📝','📄','💼','🎒',
                    '🚀','💡','🎨','🎭','📷','🎵','🎧','🎤',
                    '🌈','🌸','🌺','🌻','🌷','🌹','🍀','🌿',
                    '🐕','🐈','🐎','🐘','🦁','🐻','🦊','🐼',
                    '📱','💻','🖥','⌨','📡','🔋','🎮','🕹',
                    '🔬','🔭','🧪','🧬','🔮','🧿',
                    '📐','📏','✏','📌','📍','🔖','🏷','📎',
                    '🎀','🎁','🎈','🎊','🎉','🏮',
                    '🏆','🥇','🥈','🥉','📣','📢','🔔'
                ],"""

js = re.sub(r'workspaceIcons: \[[\s\S]*?\],', ws_icons, js, count=1)
js = re.sub(r'databaseIcons: \[[\s\S]*?\],', db_icons, js, count=1)

# Verify no ZWJ
if '\u200D' in js:
    print("WARNING: ZWJ still present!")
else:
    print("No ZWJ - clean")

# Verify no variation selector issues
import unicodedata
for char in js:
    if unicodedata.category(char) == 'Mn':  # Non-spacing marks
        print(f"Warning: combining char U+{ord(char):04X}")
        break

with open(path, 'w') as f:
    f.write(js)

ws_count = ws_icons.count("'") // 2
db_count = db_icons.count("'") // 2
print(f"Workspace icons: {ws_count}")
print(f"Database icons: {db_count}")

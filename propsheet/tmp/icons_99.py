#!/usr/bin/env python3
import re

path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(path, 'r') as f:
    js = f.read()

db_icons = """databaseIcons: [
                    '📊','📈','📉','💹','💾','💿','📀','🗄','📋','📑','📝','📄','🗃','🗂','📦','📚',
                    '🏢','🏠','🏡','🏗','🏭','🏬','🏪','🏛','🏰','🏯','🗼','🛖','🏘','🏚',
                    '💰','💵','💴','💶','💷','💳','💸','🏦','🪙','💲',
                    '🔑','🔐','🔒','🔓','🗝','⚙','🛠','🔧','🔩','🧲',
                    '🎯','⭐','🌟','✨','💎','❤','🧡','💛','💚','💙','💜','🖤',
                    '🔴','🟠','🟡','🟢','🔵','🟣','⚫','⚪','🟤',
                    '📁','📂','💼','🎒','🚀','💡','🎨','🎭','📷','🎵',
                    '🌈','🌸','🌺','🌻','🍀','🌿','🐕','🐈','🦁','🐻',
                    '📱','💻','🎮','🔬','🔮','🧿','📐','✏','📌',
                    '🎀','🎁','🎈','🎉','🏮','🏆','🥇','📣','🔔'
                ],"""

js = re.sub(r'databaseIcons: \[[\s\S]*?\],', db_icons, js, count=1)
with open(path, 'w') as f:
    f.write(js)

count = db_icons.count("'") // 2
print(f"databaseIcons: {count}")

path2 = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(path2, 'rb') as f:
    raw = f.read()
raw = raw.replace(b'v=20260317i', b'v=20260317j')
with open(path2, 'wb') as f:
    f.write(raw)
print("bumped to 20260317j")

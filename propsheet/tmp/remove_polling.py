#!/usr/bin/env python3
"""Remove polling from frontend (keep sync_events table and API for future use)"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Remove polling init block
old_init = """
                    // Real-time sync: poll for changes every 3 seconds
                    this.syncTimestamp = new Date().toISOString();
                    this.syncInterval = setInterval(() => this.pollChanges(), 3000);
                    window.addEventListener('beforeunload', () => {
                        if (this.syncInterval) clearInterval(this.syncInterval);
                    });

"""

if old_init in js:
    js = js.replace(old_init, '\n', 1)
    print("1. Removed polling init")
else:
    print("1. WARN: init pattern not found")

# Remove pollChanges method (keep it commented or remove entirely)
import re
poll_match = re.search(
    r'\n                // ===== Real-time Sync Polling =====\n                async pollChanges\(\).*?// Silent retry on next poll\n                    \}\n                \},\n',
    js, re.DOTALL
)
if poll_match:
    js = js.replace(poll_match.group(0), '\n', 1)
    print("2. Removed pollChanges method")
else:
    print("2. WARN: pollChanges pattern not found")

with open(path, 'w') as f:
    f.write(js)

import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR:\n{result.stderr}')

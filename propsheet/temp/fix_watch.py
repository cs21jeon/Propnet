#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html"
with open(path, "r") as f:
    content = f.read()

# Add x-effect to share modal to auto-load links when shown
old = 'x-show="showShareModal" x-cloak'
new = 'x-show="showShareModal" x-cloak x-effect="if(showShareModal) loadShareLinks()"'

if 'x-effect' not in content:
    content = content.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(content)
    print("OK - Added x-effect for auto-loading share links")
else:
    print("Already has x-effect")

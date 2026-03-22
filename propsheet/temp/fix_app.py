#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/app.py"
with open(path, "r") as f:
    content = f.read()

changes = 0

# 1. Add share to imports
old_import = "workspace_members, oauth"
new_import = "workspace_members, oauth, share"
if old_import in content and "share" not in content.split("from routes import")[1].split("\n")[0]:
    content = content.replace(old_import, new_import, 1)
    changes += 1
    print("1. Added share to imports")

# 2. Register share blueprint
old_reg = "app.register_blueprint(oauth.bp)"
new_reg = "app.register_blueprint(oauth.bp)\napp.register_blueprint(share.bp)"
if "share.bp" not in content:
    content = content.replace(old_reg, new_reg, 1)
    changes += 1
    print("2. Registered share blueprint")

with open(path, "w") as f:
    f.write(content)

print(f"\nTotal changes: {changes}")

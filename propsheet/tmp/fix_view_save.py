#!/usr/bin/env python3
"""Fix: Auto-save current view before switching to another view"""
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Add auto-save before switching views
old = """                async switchView(viewId) {
                    this.currentViewId = viewId;
                    const view = this.views.find(v => v.id === viewId);"""

new = """                async switchView(viewId) {
                    // Auto-save current view before switching
                    if (this.currentViewId && this.currentViewId !== viewId) {
                        await this.saveCurrentView();
                    }
                    this.currentViewId = viewId;
                    const view = this.views.find(v => v.id === viewId);"""

if old in js:
    js = js.replace(old, new, 1)
    print("Added auto-save before switchView")
else:
    print("WARN: pattern not found")

with open(path, 'w') as f:
    f.write(js)

# Verify
import subprocess
result = subprocess.run(['node', '-c', path], capture_output=True, text=True)
print('JS syntax: OK' if result.returncode == 0 else f'ERROR: {result.stderr}')

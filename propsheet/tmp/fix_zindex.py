#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/database_list.css'
with open(path, 'r') as f:
    css = f.read()

# Detail panel overlay: 2000, panel: 2001
# Field settings modal overlay needs to be above: 3000
# The field settings uses .modal-overlay which is z-index: 2000
# But we need it higher than detail panel (2001)

# Find the modal-overlay z-index and bump it
# Actually, we should only bump the field settings modal, not all modals
# The field settings modal is identified by x-show="showFieldSettings"
# But CSS doesn't know that. Safest: bump all .modal-overlay to 3000

css = css.replace(
    """    align-items: center;
    justify-content: center;
    z-index: 2000;
    backdrop-filter: blur(2px);""",
    """    align-items: center;
    justify-content: center;
    z-index: 3000;
    backdrop-filter: blur(2px);"""
)

with open(path, 'w') as f:
    f.write(css)
print("OK - modal-overlay z-index: 2000 → 3000")

#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(path, "r") as f:
    lines = f.readlines()

# Insert the modal function right after line 1 (function spreadsheetApp() {)
# Line 2 is "function spreadsheetApp() {"
modal_code = """            // Global image modal opener
            window._openImageModal = function(url, filename) {
                const overlay = document.createElement('div');
                overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:9999;display:flex;align-items:center;justify-content:center;cursor:zoom-out;';
                overlay.onclick = () => overlay.remove();
                const img = document.createElement('img');
                img.src = url;
                img.alt = filename;
                img.style.cssText = 'max-width:90vw;max-height:90vh;border-radius:8px;box-shadow:0 4px 32px rgba(0,0,0,0.5);';
                overlay.appendChild(img);
                document.body.appendChild(overlay);
            };
"""

# Check if already defined as a function
has_function_def = any('window._openImageModal = function' in line for line in lines)

if not has_function_def:
    # Insert after line 2 (index 1): "function spreadsheetApp() {"
    for i, line in enumerate(lines):
        if 'function spreadsheetApp()' in line:
            lines.insert(i + 1, modal_code + '\n')
            break

    with open(path, "w") as f:
        f.writelines(lines)
    print("OK - Added image modal opener function")
else:
    print("Already exists")

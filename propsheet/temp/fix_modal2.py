#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(path, "r") as f:
    content = f.read()

old = "function spreadsheetApp() {\n            return {"
new = """function spreadsheetApp() {
            // Global image modal opener
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

            return {"""

if "_openImageModal" not in content:
    content = content.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(content)
    print("OK - Added image modal opener")
else:
    print("Already exists")

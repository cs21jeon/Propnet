#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(path, "r") as f:
    content = f.read()

changes = 0

# 1. Add image thumbnail rendering in the template-level cell display
# We'll add an 'attachment' type check in formatCell
# But since formatCell doesn't have access to the row (only value + col),
# we need a different approach for the grid cells.

# Better approach: add a function that checks if a field is an image attachment
# and render it differently in the template.

# Actually, simplest: modify the template HTML to handle 대표사진 specially
# Let's instead modify formatCell to detect image attachment pattern

old_format = """                formatCell(value, col) {
                    if (value === null || value === undefined) return '-';

                    switch (col.type) {"""

new_format = """                formatCell(value, col, row) {
                    if (value === null || value === undefined) return '-';

                    // Image attachment field (대표사진, 건축물대장 etc.)
                    if (value && row && row.airtable_id && typeof value === 'string') {
                        const imgMatch = value.match(/^(.+?\.(jpg|jpeg|png|gif|webp))\s*\(/i);
                        if (imgMatch) {
                            const filename = imgMatch[1].trim();
                            const url = `/uploads/airtable/${row.airtable_id}/${encodeURIComponent(filename)}`;
                            return `<img src="${url}" alt="${filename}" class="cell-thumbnail" loading="lazy" onclick="event.stopPropagation(); window._openImageModal && window._openImageModal('${url}', '${filename.replace(/'/g, '')}')" onerror="this.style.display='none'; this.nextSibling.style.display='inline'"><span style="display:none">${filename}</span>`;
                        }
                    }

                    switch (col.type) {"""

if "cell-thumbnail" not in content:
    content = content.replace(old_format, new_format, 1)
    changes += 1
    print("1. Added image detection in formatCell")

# 2. Update formatCellWithColor to also pass row (it calls formatCell internally)
old_fcc = "                    return this.formatCell(value, col);"
new_fcc = "                    return this.formatCell(value, col, null);"
if old_fcc in content:
    content = content.replace(old_fcc, new_fcc, 1)
    changes += 1
    print("2. Updated formatCellWithColor fallback")

# 3. Add image modal opener function
old_init_start = "            return {"
new_init_start = """            // Global image modal opener
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
    content = content.replace(old_init_start, new_init_start, 1)
    changes += 1
    print("3. Added image modal opener")

with open(path, "w") as f:
    f.write(content)

print(f"\nTotal changes: {changes}")

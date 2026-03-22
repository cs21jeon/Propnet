#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(path, "r") as f:
    content = f.read()

changes = 0

# 1. Add helper function to get image URL from 대표사진 field value
# The value format is: "filename.jpg (https://airtable-cdn-url...)"
# We need to extract filename and combine with airtable_id

old_autofit = "                autoFitColumn(colKey) {"
new_funcs = """                getImageUrl(row) {
                    const photoField = row['대표사진'];
                    const airtableId = row['airtable_id'];
                    if (!photoField || !airtableId) return null;
                    // Extract filename: "KakaoTalk_xxx.jpg (https://...)" -> "KakaoTalk_xxx.jpg"
                    const match = photoField.match(/^(.+?\.\w+)\s*\(/);
                    if (!match) return null;
                    const filename = match[1].trim();
                    return `/uploads/airtable/${airtableId}/${encodeURIComponent(filename)}`;
                },

                autoFitColumn(colKey) {"""

if "getImageUrl" not in content:
    content = content.replace(old_autofit, new_funcs, 1)
    changes += 1
    print("1. Added getImageUrl() helper")

with open(path, "w") as f:
    f.write(content)

print(f"\nTotal changes: {changes}")

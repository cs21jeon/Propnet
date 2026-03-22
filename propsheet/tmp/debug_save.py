#!/usr/bin/env python3
path = "/home/webapp/goldenrabbit/backend/property-manager/routes/database.py"
with open(path, "r") as f:
    content = f.read()

# Add debug logging right after data extraction
old = "select_colors = data.get('select_colors')  # color map {option: {bg, text}}"
new = """select_colors = data.get('select_colors')  # color map {option: {bg, text}}
        logger.info(f"FIELD-DEF SAVE: field={field_name}, type={field_type}, options={select_options}, colors={select_colors}")"""

if 'FIELD-DEF SAVE' not in content:
    content = content.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(content)
    print("OK - Added debug log")
else:
    print("Already has debug log")

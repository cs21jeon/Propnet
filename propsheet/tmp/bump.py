#!/usr/bin/env python3
import re
path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html"
with open(path, "r") as f:
    html = f.read()
html = re.sub(r'database_list\.js\?v=\w+', 'database_list.js?v=20260317g', html)
html = re.sub(r'database_list\.css\?v=\w+', 'database_list.css?v=20260317g', html)
with open(path, "w") as f:
    f.write(html)
print("OK - 20260317g")

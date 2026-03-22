#!/usr/bin/env python3
js_path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(js_path, "r") as f:
    js = f.read()

changes = 0

# Pass col object to getOptionColor in formatCellWithColor
old1 = "const c = this.getOptionColor(value, options);"
new1 = "const c = this.getOptionColor(value, options, col);"
count1 = js.count(old1)
if count1 > 0:
    js = js.replace(old1, new1)
    changes += count1

old2 = "const c = this.getOptionColor(v, options);"
new2 = "const c = this.getOptionColor(v, options, col);"
count2 = js.count(old2)
if count2 > 0:
    js = js.replace(old2, new2)
    changes += count2

# Also check template HTML for getOptionColor calls
html_path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html"
with open(html_path, "r") as f:
    html = f.read()

html_changes = 0

# In template, getOptionColor is called for select dropdown colors
old_t1 = "getOptionColor(opt, col.selectOptions || [])"
new_t1 = "getOptionColor(opt, col.selectOptions || [], col)"
if old_t1 in html:
    html = html.replace(old_t1, new_t1)
    html_changes += html.count(new_t1)

old_t2 = "getOptionColor(option, selectDropdown.options)"
new_t2 = "getOptionColor(option, selectDropdown.options, selectDropdown.col)"
if old_t2 in html:
    html = html.replace(old_t2, new_t2)
    html_changes += 1

with open(js_path, "w") as f:
    f.write(js)
with open(html_path, "w") as f:
    f.write(html)

print(f"JS: {changes} calls updated")
print(f"HTML: {html_changes} calls updated")

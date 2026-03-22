#!/usr/bin/env python3

# === 1. HTML: number type always right-align, formula handled by JS ===
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()

old = "'cell-number': col.type === 'number' || (col.type === 'formula' && col.numberFormat && col.numberFormat.thousands !== undefined),"
new = "'cell-number': col.type === 'number',"
if old in html:
    html = html.replace(old, new, 1)
    print("1. HTML: Reverted cell-number to number type only")
else:
    print("1. WARN: pattern not found, checking current state")
    if "'cell-number': col.type === 'number'," in html:
        print("   Already correct")

with open(path, 'w') as f:
    f.write(html)

# === 2. JS: Wrap formula numeric results with right-align span ===
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

# In the formula case, wrap numeric results in a right-aligned div
# Find the number formatting return statements in the formula case
# We need to wrap all numeric returns with style="text-align:right;display:block"

# The formula case returns formatted numbers. Let's wrap them.
# Current structure: the formula case formats numbers and returns strings.
# Easiest: after formatting, wrap in a span with text-align:right

old_formula_start = """                        case 'formula': {
                            // If value is numeric, apply number formatting
                            const numVal = Number(value);
                            if (value !== null && value !== '' && !isNaN(numVal)) {"""

new_formula_start = """                        case 'formula': {
                            // If value is numeric, apply number formatting
                            const numVal = Number(value);
                            if (value !== null && value !== '' && !isNaN(numVal)) {
                                const _wrapRight = (s) => `<span style="display:block;text-align:right">${s}</span>`;"""

if '_wrapRight' not in js:
    js = js.replace(old_formula_start, new_formula_start, 1)
    print("2. JS: Added _wrapRight helper in formula case")

    # Now wrap all return statements in the numeric block
    # There are 4 return paths in the numeric block:
    # 1. return parts.join('.');
    # 2. return v;  (after toFixed)
    # 3. return thousands ? numVal.toLocaleString() : String(numVal);

    # Find them within the formula case block and wrap
    # Let's be precise - these are inside "if (value !== null && value !== '' && !isNaN(numVal)) {"

    js = js.replace(
        "                                        return parts.join('.');",
        "                                        return _wrapRight(parts.join('.'));",
        1
    )
    # Find the right "return v;" - it's the one after toFixed in formula block
    # This is tricky. Let's find by context.
    js = js.replace(
        """                                    return v;
                                }
                                return thousands ? numVal.toLocaleString() : String(numVal);""",
        """                                    return _wrapRight(v);
                                }
                                return _wrapRight(thousands ? numVal.toLocaleString() : String(numVal));""",
        1
    )
    print("3. JS: Wrapped formula numeric returns with right-align")

with open(js_path, 'w') as f:
    f.write(js)

import re
html = open(path).read()
html = re.sub(r'database_list\.js\?v=\w+', 'database_list.js?v=20260317q', html)
with open(path, 'w') as f:
    f.write(html)

print("\nDone!")

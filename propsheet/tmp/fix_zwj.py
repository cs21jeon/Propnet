#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/workspaces.js'
with open(path, 'r') as f:
    js = f.read()

# Replace the ZWJ emoji line with safe emojis
old_line = "                    '\U0001F464','\U0001F465','\U0001F468\u200D\U0001F4BC','\U0001F469\u200D\U0001F4BC','\U0001F9D1\u200D\U0001F4BB','\U0001F468\u200D\U0001F527','\U0001F469\u200D\U0001F3EB','\U0001F468\u200D\u2695\uFE0F','\U0001F9D1\u200D\U0001F373','\U0001F477','\U0001F575\uFE0F','\U0001F9D1\u200D\U0001F680',"
new_line = "                    '\U0001F464','\U0001F465','\U0001F474','\U0001F475','\U0001F476','\U0001F468','\U0001F469','\U0001F9D1','\U0001F477','\U0001F482','\U0001F575\uFE0F','\U0001F9D9',"

if old_line in js:
    js = js.replace(old_line, new_line)
    print("Replaced ZWJ line")
else:
    # Fallback: remove any line containing ZWJ in the icon arrays
    lines = js.split('\n')
    new_lines = []
    for line in lines:
        if '\u200D' in line:
            # Replace with safe version
            safe = "                    '\U0001F464','\U0001F465','\U0001F474','\U0001F475','\U0001F476','\U0001F468','\U0001F469','\U0001F9D1','\U0001F477','\U0001F482','\U0001F575\uFE0F','\U0001F9D9',"
            new_lines.append(safe)
            print(f"Replaced ZWJ line (fallback)")
        else:
            new_lines.append(line)
    js = '\n'.join(new_lines)

with open(path, 'w') as f:
    f.write(js)

# Verify
with open(path) as f:
    content = f.read()
print(f"ZWJ remaining: {content.count(chr(0x200D))}")

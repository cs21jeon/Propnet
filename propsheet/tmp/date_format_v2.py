#!/usr/bin/env python3

js_path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(js_path, "r") as f:
    js = f.read()

# Update date format switch
old = """switch (style) {
                                    case 'long': return `${y}년 ${parseInt(m)}월 ${parseInt(dd)}일`;
                                    case 'dot': return `${y}.${m}.${dd}`;
                                    case 'dash': return `${y}-${m}-${dd}`;
                                    case 'slash': return `${y}/${m}/${dd}`;
                                    case 'year': return `${y}`;
                                    case 'yearMonth': return `${y}년 ${parseInt(m)}월`;
                                    case 'yearMonthDot': return `${y}.${m}`;
                                    default: return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
                                }"""

new = """switch (style) {
                                    case 'long': return `${y}년 ${parseInt(m)}월 ${parseInt(dd)}일`;
                                    case 'dot': return `${y}.${m}.${dd}`;
                                    case 'dash': return `${y}-${m}-${dd}`;
                                    case 'slash': return `${y}/${m}/${dd}`;
                                    case 'compact8': return `${y}${m}${dd}`;
                                    case 'compact6': return `${String(y).slice(2)}${m}${dd}`;
                                    case 'year': return `${y}`;
                                    default: return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
                                }"""

if old in js:
    js = js.replace(old, new, 1)
    with open(js_path, "w") as f:
        f.write(js)
    print("1. JS: Updated date formats")

# Update HTML options
html_path = "/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html"
with open(html_path, "r") as f:
    html = f.read()

old_opts = """<option value="long">1991년 10월 16일</option>
                                <option value="dot">1991.10.16</option>
                                <option value="dash">1991-10-16</option>
                                <option value="slash">1991/10/16</option>
                                <option value="yearMonth">1991년 10월</option>
                                <option value="yearMonthDot">1991.10</option>
                                <option value="year">1991 (년도만)</option>"""

new_opts = """<option value="long">1991년 10월 16일</option>
                                <option value="dot">1991.10.16</option>
                                <option value="dash">1991-10-16</option>
                                <option value="slash">1991/10/16</option>
                                <option value="compact8">19911016</option>
                                <option value="compact6">911016</option>
                                <option value="year">1991 (년도만)</option>"""

if old_opts in html:
    html = html.replace(old_opts, new_opts, 1)
    print("2. HTML: Updated options")

# Update preview hint
old_hint = """if(s==='year') return y+'';
                                    if(s==='yearMonth') return y+'년 '+parseInt(m)+'월';
                                    if(s==='yearMonthDot') return y+'.'+m;"""

new_hint = """if(s==='compact8') return y+m+dd;
                                    if(s==='compact6') return String(y).slice(2)+m+dd;
                                    if(s==='year') return y+'';"""

if old_hint in html:
    html = html.replace(old_hint, new_hint, 1)
    print("3. HTML: Updated preview")

import re
html = re.sub(r'database_list\.js\?v=\w+', 'database_list.js?v=20260317o', html)

with open(html_path, "w") as f:
    f.write(html)

print("Done!")

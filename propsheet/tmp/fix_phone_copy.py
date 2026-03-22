#!/usr/bin/env python3
"""Change phone number in broker card from tel: link to click-to-copy"""
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(path, 'r') as f:
    html = f.read()

# Replace tel: link with click-to-copy span
old = """<a href="tel:0234717377">02.3471.7377</a>"""
new = """<span style="color:var(--brand-blue,#667eea);cursor:pointer;" onclick="navigator.clipboard.writeText('02-3471-7377'); this.dataset.orig=this.textContent; this.textContent='복사됨!'; setTimeout(()=>this.textContent=this.dataset.orig, 1500);" title="클릭하여 복사">02.3471.7377</span>"""

count = html.count(old)
if count > 0:
    html = html.replace(old, new)
    print(f"1. Replaced {count} phone link(s) with click-to-copy")
else:
    print("1. WARN: tel link not found, checking alternatives...")
    # Try other patterns
    import re
    tel_match = re.search(r'<a[^>]*href="tel:[^"]*"[^>]*>([^<]*)</a>', html)
    if tel_match:
        print(f"   Found: {tel_match.group(0)}")
        phone_text = tel_match.group(1)
        old2 = tel_match.group(0)
        new2 = f"""<span style="color:var(--brand-blue,#667eea);cursor:pointer;" onclick="navigator.clipboard.writeText('02-3471-7377'); this.dataset.orig=this.textContent; this.textContent='복사됨!'; setTimeout(()=>this.textContent=this.dataset.orig, 1500);" title="클릭하여 복사">{phone_text}</span>"""
        html = html.replace(old2, new2, 1)
        print(f"   Replaced with click-to-copy")
    else:
        print("   No tel: link found at all")

with open(path, 'w') as f:
    f.write(html)

# Bump HTML version
import re, time
ts = str(int(time.time()))
html2 = re.sub(r'workspaces\.css\?v=\d+', f'workspaces.css?v={ts}', html)
if html2 != html:
    with open(path, 'w') as f:
        f.write(html2)
    print(f"2. Bumped CSS version to {ts}")

print("\nDone! Restart: sudo systemctl restart property-manager propsheet")

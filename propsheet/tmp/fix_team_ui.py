#!/usr/bin/env python3
"""
1. Hide team button for subagents (show only for agent/admin)
2. Widen broker card to prevent line wrapping
"""

HTML_PATH = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
CSS_PATH = '/home/webapp/goldenrabbit/backend/property-manager/static/css/propsheet/workspaces.css'

# 1. Change team button condition: agent_info AND user is agent (not subagent)
with open(HTML_PATH, 'r') as f:
    html = f.read()

# Currently: {% if agent_info %} shows for both agent and subagent
# Change to: only show if session role is admin or agent
old_btn = '{% if agent_info %}\n                    <button class="btn-team"'
new_btn = "{% if agent_info and session.get('user_role') != 'subagent' %}\n                    <button class=\"btn-team\""

if old_btn in html:
    html = html.replace(old_btn, new_btn, 1)
    print("1. Hidden team button for subagents")
else:
    print("1. WARN: button pattern not found")

with open(HTML_PATH, 'w') as f:
    f.write(html)

# 2. Widen broker card
with open(CSS_PATH, 'r') as f:
    css = f.read()

# Find broker-card style and increase min-width / prevent wrapping
if '.broker-card {' in css:
    old_card = '.broker-card {'
    new_card = '.broker-card {\n    min-width: 280px;\n    white-space: nowrap;'
    if 'min-width: 280px' not in css:
        css = css.replace(old_card, new_card, 1)
        print("2. Widened broker card (min-width:280px, nowrap)")
    else:
        print("2. Already widened")
else:
    # Add new rule
    css += """
.broker-card {
    min-width: 280px;
    white-space: nowrap;
}
"""
    print("2. Added broker card width rule")

with open(CSS_PATH, 'w') as f:
    f.write(css)

print("Done!")

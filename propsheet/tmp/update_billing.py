#!/usr/bin/env python3
"""Update proptalk billing: API filter by user_type + plans page UI"""

# === 1. models_billing.py: Add user_type filter to list_active ===
model_path = '/home/webapp/goldenrabbit/chat_stt/server/models_billing.py'
with open(model_path, 'r') as f:
    content = f.read()

old_list = """    def list_active():
        return query_all(
            "SELECT * FROM billing_plans WHERE is_active = true ORDER BY sort_order"
        )"""

new_list = """    def list_active(user_type=None):
        if user_type:
            return query_all(
                "SELECT * FROM billing_plans WHERE is_active = true AND user_type = %s ORDER BY sort_order",
                (user_type,)
            )
        return query_all(
            "SELECT * FROM billing_plans WHERE is_active = true ORDER BY sort_order"
        )"""

if 'user_type=None' not in content:
    content = content.replace(old_list, new_list, 1)
    with open(model_path, 'w') as f:
        f.write(content)
    print("1. Updated list_active with user_type filter")

# === 2. routes_billing.py: Pass user_type query param ===
routes_path = '/home/webapp/goldenrabbit/chat_stt/server/routes_billing.py'
with open(routes_path, 'r') as f:
    content = f.read()

old_api = """        plans = BillingPlan.list_active()"""
new_api = """        user_type = request.args.get('user_type', None)
        plans = BillingPlan.list_active(user_type=user_type)"""

if "request.args.get('user_type'" not in content:
    content = content.replace(old_api, new_api, 1)
    with open(routes_path, 'w') as f:
        f.write(content)
    print("2. Updated API with user_type query param")

# === 3. billing_web.py: Pass user_type to template ===
web_path = '/home/webapp/goldenrabbit/chat_stt/server/billing_web.py'
with open(web_path, 'r') as f:
    content = f.read()

# Find the plans page route
if "user_type" not in content.split('def plans')[1].split('def ')[0] if 'def plans' in content else '':
    # Find where plans are loaded and template is rendered
    old_plans = "plans = BillingPlan.list_active()"
    if old_plans in content:
        new_plans = """user_type = request.args.get('type', 'user')
        plans = BillingPlan.list_active(user_type=user_type)"""
        content = content.replace(old_plans, new_plans, 1)

        # Also pass user_type to template
        # Find render_template call for plans
        import re
        # Add user_type to template context
        old_render = "return render_template('billing/plans.html',"
        if old_render in content:
            new_render = "return render_template('billing/plans.html', user_type=user_type,"
            content = content.replace(old_render, new_render, 1)

        with open(web_path, 'w') as f:
            f.write(content)
        print("3. Updated billing_web with user_type")
    else:
        print("3. WARN: Could not find plans loading in billing_web.py")

# === 4. plans.html: Add user/agent tab switcher ===
plans_path = '/home/webapp/goldenrabbit/chat_stt/server/templates/billing/plans.html'
with open(plans_path, 'r') as f:
    html = f.read()

if 'user-type-tab' not in html:
    # Find the main heading or section to add tabs
    # Look for a heading element
    import re
    # Add a tab switcher before the plans grid
    tab_html = '''
    <div class="user-type-tabs" style="display:flex;justify-content:center;gap:8px;margin-bottom:24px;">
        <a href="?type=user" class="plan-tab" style="padding:8px 24px;border-radius:20px;text-decoration:none;font-size:14px;font-weight:600;{% if user_type != 'agent' %}background:#667eea;color:white;{% else %}background:#f0f0f0;color:#666;{% endif %}">일반 사용자</a>
        <a href="?type=agent" class="plan-tab" style="padding:8px 24px;border-radius:20px;text-decoration:none;font-size:14px;font-weight:600;{% if user_type == 'agent' %}background:#667eea;color:white;{% else %}background:#f0f0f0;color:#666;{% endif %}">중개사 (Agent)</a>
    </div>
'''
    # Find a good insertion point — look for the first <div or <section after the header
    # Try to find plans container
    markers = ['<div class="plans-container"', '<div class="plans-grid"', '<div class="pricing"', '<section', '<div class="content"']
    inserted = False
    for marker in markers:
        if marker in html:
            html = html.replace(marker, tab_html + marker, 1)
            inserted = True
            print(f"4. Added tabs before '{marker}'")
            break

    if not inserted:
        # Fallback: add after <body> or first main div
        if '<main' in html:
            html = html.replace('<main', tab_html + '<main', 1)
            print("4. Added tabs before <main>")
        else:
            print("4. WARN: Could not find insertion point for tabs")

    with open(plans_path, 'w') as f:
        f.write(html)

print("Done!")

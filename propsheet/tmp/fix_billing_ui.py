#!/usr/bin/env python3
"""Add user/agent tab to billing plans page"""

plans_path = '/home/webapp/goldenrabbit/chat_stt/server/templates/billing/plans.html'
with open(plans_path, 'r') as f:
    html = f.read()

# 1. Add tab UI before time-packs section
old_section = """<h2 style="font-size:16px; font-weight:700; margin:16px 0 8px; padding-left:4px;">시간 충전</h2>"""

tab_html = """<div style="display:flex;justify-content:center;gap:8px;margin-bottom:20px;">
    <button id="tab-user" onclick="switchTab('user')" style="padding:8px 24px;border-radius:20px;border:none;font-size:14px;font-weight:600;cursor:pointer;background:#1A73E8;color:white;">일반 사용자</button>
    <button id="tab-agent" onclick="switchTab('agent')" style="padding:8px 24px;border-radius:20px;border:none;font-size:14px;font-weight:600;cursor:pointer;background:#f0f0f0;color:#666;">중개사 (Agent)</button>
</div>

<div id="agent-info" style="display:none;margin-bottom:16px;padding:12px 16px;background:#FFF3E0;border-radius:8px;font-size:13px;color:#E65100;">
    ✅ Agent 요금제에는 <b>Propsheet</b>(부동산 데이터베이스)가 포함되어 있습니다.
</div>

<h2 style="font-size:16px; font-weight:700; margin:16px 0 8px; padding-left:4px;">시간 충전</h2>"""

if 'tab-user' not in html:
    html = html.replace(old_section, tab_html, 1)
    print("1. Added tab UI")

# 2. Modify loadPlans to accept user_type and add switchTab function
old_load = "async function loadPlans() {"
new_load = """let currentUserType = 'user';

function switchTab(type) {
    currentUserType = type;
    document.getElementById('tab-user').style.background = type === 'user' ? '#1A73E8' : '#f0f0f0';
    document.getElementById('tab-user').style.color = type === 'user' ? 'white' : '#666';
    document.getElementById('tab-agent').style.background = type === 'agent' ? '#1A73E8' : '#f0f0f0';
    document.getElementById('tab-agent').style.color = type === 'agent' ? 'white' : '#666';
    document.getElementById('agent-info').style.display = type === 'agent' ? 'block' : 'none';
    // Hide time packs for agent (agent only has subscriptions)
    const timePacksHeader = document.querySelectorAll('h2')[0];
    const timePacksDiv = document.getElementById('time-packs');
    if (type === 'agent') {
        if (timePacksHeader) timePacksHeader.style.display = 'none';
        if (timePacksDiv) timePacksDiv.style.display = 'none';
    } else {
        if (timePacksHeader) timePacksHeader.style.display = '';
        if (timePacksDiv) timePacksDiv.style.display = '';
    }
    loadPlans();
}

async function loadPlans() {"""

if 'switchTab' not in html:
    html = html.replace(old_load, new_load, 1)
    print("2. Added switchTab function")

# 3. Modify API call to include user_type
old_api_call = "apiCall('/api/billing/plans')"
new_api_call = "apiCall(`/api/billing/plans?user_type=${currentUserType}`)"

if 'user_type=${currentUserType}' not in html:
    html = html.replace(old_api_call, new_api_call, 1)
    print("3. Updated API call with user_type")

# 4. For agent plans, add propsheet badge to card
old_card = """<div style="font-size:13px; color:#666; margin-top:2px;">
                            ${hours} · ${plan.plan_type === 'subscription' ? '월 정기결제' : '일회성 · 만료 없음'}
                            ${perHour > 0 ? ` · 시간당 ${perHour.toLocaleString()}원` : ''}
                            ${plan.overage_rate > 0 ? ` · 초과 시 ${plan.overage_rate}원/분` : ''}
                        </div>"""

new_card = """<div style="font-size:13px; color:#666; margin-top:2px;">
                            ${hours} · ${plan.plan_type === 'subscription' ? '월 정기결제' : '일회성 · 만료 없음'}
                            ${perHour > 0 ? ` · 시간당 ${perHour.toLocaleString()}원` : ''}
                            ${plan.overage_rate > 0 ? ` · 초과 시 ${plan.overage_rate}원/분` : ''}
                            ${plan.includes_propsheet ? ' · <span style="color:#1A73E8;font-weight:600;">Propsheet 포함</span>' : ''}
                        </div>"""

if 'includes_propsheet' not in html:
    html = html.replace(old_card, new_card, 1)
    print("4. Added propsheet badge for agent plans")

with open(plans_path, 'w') as f:
    f.write(html)

print("Done!")

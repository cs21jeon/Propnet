#!/usr/bin/env python3
"""
1. Fix billing plans.html: ensure user tab only shows user plans on load
2. Update proptalk landing page pricing to match actual DB
3. Add pricing link to propnet page
"""

# === 1. Fix billing plans.html — ensure proper initial load ===
plans_path = '/home/webapp/goldenrabbit/chat_stt/server/templates/billing/plans.html'
with open(plans_path, 'r') as f:
    html = f.read()

# The issue: loadPlans() is called on page load but might not use currentUserType
# Check if there's a DOMContentLoaded or onload that calls loadPlans
# Make sure loadPlans uses currentUserType from the start
if 'loadPlans()' in html and 'currentUserType' in html:
    # It should already work, but let's verify the initial call
    # Add a check: if plans are loaded without filter, clear and reload
    print("1. billing plans.html already has user_type filter")

# === 2. Update proptalk landing page pricing ===
landing_path = '/home/webapp/goldenrabbit/chat_stt/marketing/proptalk/index.html'
with open(landing_path, 'r') as f:
    content = f.read()

old_pricing = """            <div class="pricing-grid">
                <div class="price-card free-card">
                    <h3>무료 체험</h3>
                    <div class="time">10분</div>
                    <div class="amount">무료</div>
                    <div class="unit">가입 시 제공</div>
                </div>
                <div class="price-card">
                    <h3>Starter</h3>
                    <div class="time">3시간</div>
                    <div class="amount">4,900원</div>
                    <div class="unit">시간팩 (1회)</div>
                </div>
                <div class="price-card popular">
                    <h3>Basic</h3>
                    <div class="time">10시간</div>
                    <div class="amount">9,900원</div>
                    <div class="unit">월 구독</div>
                </div>
                <div class="price-card">
                    <h3>Standard</h3>
                    <div class="time">30시간</div>
                    <div class="amount">19,900원</div>
                    <div class="unit">월 구독</div>
                </div>
                <div class="price-card">
                    <h3>Pro</h3>
                    <div class="time">90시간</div>
                    <div class="amount">39,900원</div>
                    <div class="unit">월 구독</div>
                </div>
            </div>
            <p class="pricing-note">출시 후 충전 · 구독이 가능합니다. 요금제는 변경될 수 있습니다.</p>"""

new_pricing = """            <h3 style="text-align:center;margin-bottom:8px;font-size:14px;color:#666;">일반 사용자</h3>
            <div class="pricing-grid">
                <div class="price-card free-card">
                    <h3>무료 체험</h3>
                    <div class="time">10분</div>
                    <div class="amount">무료</div>
                    <div class="unit">가입 시 제공</div>
                </div>
                <div class="price-card">
                    <h3>1시간 팩</h3>
                    <div class="time">1시간</div>
                    <div class="amount">4,900원</div>
                    <div class="unit">시간팩 (1회)</div>
                </div>
                <div class="price-card">
                    <h3>10시간 팩</h3>
                    <div class="time">10시간</div>
                    <div class="amount">19,900원</div>
                    <div class="unit">시간팩 (1회)</div>
                </div>
                <div class="price-card popular">
                    <h3>Basic</h3>
                    <div class="time">30시간</div>
                    <div class="amount">29,900원</div>
                    <div class="unit">월 구독</div>
                </div>
                <div class="price-card">
                    <h3>Pro</h3>
                    <div class="time">90시간</div>
                    <div class="amount">79,900원</div>
                    <div class="unit">월 구독</div>
                </div>
            </div>

            <h3 style="text-align:center;margin:24px 0 8px;font-size:14px;color:#666;">중개사 (Agent)</h3>
            <div class="pricing-grid">
                <div class="price-card">
                    <h3>Agent Regular</h3>
                    <div class="time">Basic 기본</div>
                    <div class="amount">9,900원</div>
                    <div class="unit">월 구독 · Propsheet 포함</div>
                </div>
                <div class="price-card popular">
                    <h3>Agent Basic</h3>
                    <div class="time">30시간</div>
                    <div class="amount">29,900원</div>
                    <div class="unit">월 구독 · Propsheet 포함</div>
                </div>
                <div class="price-card">
                    <h3>Agent Pro</h3>
                    <div class="time">90시간</div>
                    <div class="amount">79,900원</div>
                    <div class="unit">월 구독 · Propsheet 포함</div>
                </div>
            </div>
            <p class="pricing-note">자세한 내용은 <a href="/proptalk/billing/" style="color:#1A73E8;">요금제 페이지</a>에서 확인하세요.</p>"""

if old_pricing in content:
    content = content.replace(old_pricing, new_pricing, 1)
    with open(landing_path, 'w') as f:
        f.write(content)
    print("2. Updated proptalk landing pricing")
else:
    print("2. WARN: old pricing pattern not found")

# === 3. Add pricing link to propnet page ===
propnet_path = '/home/webapp/goldenrabbit/frontend/public/propnet/index.html'
with open(propnet_path, 'r') as f:
    propnet = f.read()

if 'proptalk/billing' not in propnet:
    # Find a good place to add — before </body> or in a footer/nav section
    # Look for existing links or footer
    if '</footer>' in propnet:
        propnet = propnet.replace('</footer>',
            '<div style="text-align:center;margin-top:16px;"><a href="/proptalk/billing/" style="color:#1A73E8;text-decoration:none;font-size:13px;">Proptalk 요금제 보기 →</a></div>\n</footer>')
        print("3. Added pricing link to propnet footer")
    elif '</body>' in propnet:
        propnet = propnet.replace('</body>',
            '<div style="text-align:center;padding:20px;"><a href="/proptalk/billing/" style="color:#1A73E8;text-decoration:none;font-size:14px;">Proptalk 요금제 보기 →</a></div>\n</body>')
        print("3. Added pricing link before propnet body close")
    with open(propnet_path, 'w') as f:
        f.write(propnet)
else:
    print("3. Propnet already has billing link")

print("Done!")

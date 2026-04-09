#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PropMap template update: Add consultation form + agent info popup"""

template_path = '/home/webapp/goldenrabbit/frontend/public/propmap/_template/index.html'

with open(template_path, 'r', encoding='utf-8') as f:
    html = f.read()

changes = 0

# 1. Header: Replace PropNet link with info button
old1 = '<a href="https://propnet.kr" target="_blank" class="text-xs text-slate-400 hover:text-primary transition-colors">PropNet</a>'
new1 = '<button onclick="toggleAgentInfo()" class="p-2 hover:bg-slate-100 rounded-full transition-colors" aria-label="\ubd80\ub3d9\uc0b0 \uc815\ubcf4"><span class="material-symbols-outlined text-slate-500 text-[22px]">info</span></button>'
if old1 in html:
    html = html.replace(old1, new1)
    changes += 1
    print("1. Header info button: OK")
else:
    print("1. Header info button: NOT FOUND")

# 2. Add consultation button after search menu section
old2 = '        </section>\n\n        <!-- \ub9e4\ubb3c\uc9c0\ub3c4 \uc139\uc158 -->'
new2 = '''            <!-- \ud558\ub2e8: \uc0c1\ub2f4\uc2e0\uccad -->
            <div class="mt-3">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">\ubb38\uc758</p>
                <button class="category-chip w-full flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all bg-white text-slate-600 border border-slate-200 hover:border-primary hover:text-primary" onclick="openConsultModal()">
                    <span class="material-symbols-outlined text-[16px]">chat</span>
                    \uc0c1\ub2f4\uc2e0\uccad
                </button>
            </div>

        </section>

        <!-- \ub9e4\ubb3c\uc9c0\ub3c4 \uc139\uc158 -->'''
if old2 in html:
    html = html.replace(old2, new2)
    changes += 1
    print("2. Consultation button: OK")
else:
    print("2. Consultation button: NOT FOUND")

# 3. Add agent info popup after header
old3 = '    </header>\n\n    <!-- \uba54\uc778 \ucf58\ud150\uce20 -->'
new3 = '''    </header>

    <!-- \ubd80\ub3d9\uc0b0 \uc815\ubcf4 \ud31d\uc5c5 -->
    <div id="agentInfoPopup" class="hidden fixed top-16 right-4 z-[55] w-72 bg-white rounded-2xl shadow-2xl border border-slate-200/60 overflow-hidden">
        <div class="p-5">
            <div class="flex items-center justify-between mb-3">
                <h3 class="text-base font-bold text-slate-900">\ubd80\ub3d9\uc0b0 \uc815\ubcf4</h3>
                <button onclick="toggleAgentInfo()" class="p-1 hover:bg-slate-100 rounded-full transition-colors">
                    <span class="material-symbols-outlined text-slate-400 text-[18px]">close</span>
                </button>
            </div>
            <div id="agentInfoContent" class="space-y-2.5">
                <div class="text-sm text-slate-500 text-center py-4">\uc815\ubcf4\ub97c \ubd88\ub7ec\uc624\ub294 \uc911...</div>
            </div>
        </div>
    </div>

    <!-- \uba54\uc778 \ucf58\ud150\uce20 -->'''
if old3 in html:
    html = html.replace(old3, new3)
    changes += 1
    print("3. Agent info popup: OK")
else:
    print("3. Agent info popup: NOT FOUND")

# 4. Add consultModal before background decoration
old4 = '    <!-- \ubc30\uacbd \uc7a5\uc2dd -->\n    <div class="fixed top-0 left-0 -z-10 w-full h-full pointer-events-none opacity-40">'
new4 = '''    <!-- \uc0c1\ub2f4 \ubaa8\ub2ec -->
    <div id="consultModal" class="fixed inset-0 z-[70] bg-black/50 hidden items-start justify-center overflow-y-auto px-4">
        <div class="relative w-full max-w-lg mx-auto my-6 bg-white rounded-2xl overflow-hidden shadow-2xl">
            <button onclick="closeConsultModal()" class="absolute top-4 right-4 z-10 w-9 h-9 flex items-center justify-center bg-slate-100 rounded-full hover:bg-slate-200 transition-colors">
                <span class="material-symbols-outlined text-slate-700 text-[20px]">close</span>
            </button>
            <div class="p-6 pt-14">
                <h2 class="text-xl font-bold mb-6">\uc0c1\ub2f4 \ubb38\uc758</h2>
                <form id="consultForm" onsubmit="return false;">
                    <div class="space-y-4">
                        <div>
                            <label for="propertyType" class="block text-sm font-semibold text-slate-700 mb-1.5">\ub9e4\ubb3c\uc885\ub958</label>
                            <select id="propertyType" name="propertyType" required class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none">
                                <option value="">-- \uc120\ud0dd\ud558\uc138\uc694 --</option>
                                <option value="house">\ub2e8\ub3c5/\ub2e4\uac00\uad6c</option>
                                <option value="mixed">\uc0c1\uac00\uc8fc\ud0dd</option>
                                <option value="commercial">\uc0c1\uc5c5\uc6a9\uac74\ubb3c</option>
                                <option value="land">\uc7ac\uac74\ucd95/\ud1a0\uc9c0</option>
                                <option value="sell">\ub9e4\ubb3c\uc811\uc218</option>
                            </select>
                        </div>
                        <div>
                            <label for="phone" class="block text-sm font-semibold text-slate-700 mb-1.5">\uc5f0\ub77d\ucc98</label>
                            <input type="tel" id="phone" name="phone" placeholder="010-0000-0000" required autocomplete="tel" class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none">
                        </div>
                        <div>
                            <label for="email" class="block text-sm font-semibold text-slate-700 mb-1.5">\uc774\uba54\uc77c <span class="text-slate-400 font-normal">(\uc120\ud0dd\uc0ac\ud56d)</span></label>
                            <input type="email" id="email" name="email" placeholder="abc@abc.com" autocomplete="email" class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none">
                        </div>
                        <div>
                            <label for="message" class="block text-sm font-semibold text-slate-700 mb-1.5">\ubb38\uc758\uc0ac\ud56d</label>
                            <textarea id="message" name="message" placeholder="\uad00\uc2ec\uc9c0\uc5ed, \ud3c9\ud615, \ud76c\ub9dd\uc218\uc775\ub960 \ub4f1\uc744 \uc791\uc131\ud574 \uc8fc\uc138\uc694!" required class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none h-28 resize-none"></textarea>
                        </div>
                        <button type="button" id="submitConsult" class="w-full py-3.5 bg-primary text-white rounded-xl font-bold text-[15px] hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20">\uc0c1\ub2f4 \uc2e0\uccad\ud558\uae30</button>
                        <div id="formStatus" style="margin-top: 10px; text-align: center; display: none; padding: 10px; border-radius: 8px;"></div>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- \ubc30\uacbd \uc7a5\uc2dd -->
    <div class="fixed top-0 left-0 -z-10 w-full h-full pointer-events-none opacity-40">'''
if old4 in html:
    html = html.replace(old4, new4)
    changes += 1
    print("4. Consult modal: OK")
else:
    print("4. Consult modal: NOT FOUND")

# 5. Add toggleAgentInfo and fix openConsultModal
old5 = '''    // ===== \uc0c1\ub2f4 \ubaa8\ub2ec =====
    function openConsultFromDetail(address) {'''
new5 = '''    // ===== \ubd80\ub3d9\uc0b0 \uc815\ubcf4 \ud31d\uc5c5 =====
    var _agentInfoLoaded = false;
    var _agentInfoData = null;

    function toggleAgentInfo() {
        var popup = document.getElementById('agentInfoPopup');
        if (popup.classList.contains('hidden')) {
            popup.classList.remove('hidden');
            if (!_agentInfoLoaded) {
                loadAgentInfo();
            }
        } else {
            popup.classList.add('hidden');
        }
    }

    function loadAgentInfo() {
        if (_agentInfoData) {
            renderAgentInfo(_agentInfoData);
            return;
        }
        fetch('/propsheet/api/propsheet/map-data?agent_slug={{AGENT_SLUG}}')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.agent) {
                    _agentInfoData = data.agent;
                    _agentInfoLoaded = true;
                    renderAgentInfo(data.agent);
                } else {
                    document.getElementById('agentInfoContent').innerHTML =
                        '<div class="text-sm text-slate-400 text-center py-4">\uc815\ubcf4\ub97c \ubd88\ub7ec\uc62c \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.</div>';
                }
            })
            .catch(function() {
                document.getElementById('agentInfoContent').innerHTML =
                    '<div class="text-sm text-slate-400 text-center py-4">\uc815\ubcf4\ub97c \ubd88\ub7ec\uc62c \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.</div>';
            });
    }

    function renderAgentInfo(agent) {
        var rows = '';
        if (agent.agency_name) rows += agentInfoRow('\uc0ac\ubb34\uc18c\uba85', agent.agency_name);
        if (agent.address) rows += agentInfoRow('\uc8fc\uc18c', agent.address);
        if (agent.phone) rows += agentInfoRow('\uc5f0\ub77d\ucc98', '<a href="tel:' + agent.phone + '" class="text-primary hover:underline">' + agent.phone + '</a>');
        if (agent.name) rows += agentInfoRow('\ub300\ud45c\uc790\uba85', agent.name);
        if (agent.license_no) rows += agentInfoRow('\ub4f1\ub85d\ubc88\ud638', agent.license_no);
        document.getElementById('agentInfoContent').innerHTML = rows ||
            '<div class="text-sm text-slate-400 text-center py-4">\ub4f1\ub85d\ub41c \uc815\ubcf4\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.</div>';
    }

    function agentInfoRow(label, value) {
        return '<div class="flex items-start gap-3">' +
                   '<span class="text-xs text-slate-400 font-medium w-14 shrink-0 pt-0.5">' + label + '</span>' +
                   '<span class="text-sm text-slate-700 font-medium flex-1">' + value + '</span>' +
               '</div>';
    }

    // ===== \uc0c1\ub2f4 \ubaa8\ub2ec =====
    function openConsultFromDetail(address) {'''
if old5 in html:
    html = html.replace(old5, new5)
    changes += 1
    print("5. Agent info functions: OK")
else:
    print("5. Agent info functions: NOT FOUND")

# 6. Fix the disabled openConsultModal function
old6 = '    function openConsultModal_disabled(address) {\n        const modal = document.getElementById(\'consultModal\');\n        modal.classList.remove(\'hidden\');\n        modal.classList.add(\'flex\');\n        document.body.style.overflow = \'hidden\';\n\n        if (address) {\n            const messageField = document.getElementById(\'message\');\n            if (messageField) {\n                messageField.value = address + \' \ub9e4\ubb3c\uc5d0 \uad00\uc2ec\uc788\uc2b5\ub2c8\ub2e4.\';\n            }\n        }\n    }'
new6 = '''    function openConsultModal(address) {
        var popup = document.getElementById('agentInfoPopup');
        if (popup && !popup.classList.contains('hidden')) {
            popup.classList.add('hidden');
        }
        const modal = document.getElementById('consultModal');
        if (!modal) return;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.body.style.overflow = 'hidden';

        if (address) {
            const messageField = document.getElementById('message');
            if (messageField) {
                messageField.value = address + ' \ub9e4\ubb3c\uc5d0 \uad00\uc2ec\uc788\uc2b5\ub2c8\ub2e4.';
            }
        }
    }'''
if old6 in html:
    html = html.replace(old6, new6)
    changes += 1
    print("6. openConsultModal fix: OK")
else:
    print("6. openConsultModal fix: NOT FOUND")

# 7. Add agentInfo popup close on click outside + ESC
old7 = '    document.addEventListener(\'keydown\', function(e) {\n        if (e.key === \'Escape\') {\n            var detailModal = document.getElementById(\'propertyDetailModal\');'
new7 = '''    // \ubd80\ub3d9\uc0b0 \uc815\ubcf4 \ud31d\uc5c5 \uc678\ubd80 \ud074\ub9ad \uc2dc \ub2eb\uae30
    document.addEventListener('click', function(e) {
        var popup = document.getElementById('agentInfoPopup');
        if (!popup || popup.classList.contains('hidden')) return;
        if (!popup.contains(e.target) && !e.target.closest('button[aria-label="\ubd80\ub3d9\uc0b0 \uc815\ubcf4"]')) {
            popup.classList.add('hidden');
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            var agentPopup = document.getElementById('agentInfoPopup');
            if (agentPopup && !agentPopup.classList.contains('hidden')) {
                agentPopup.classList.add('hidden');
                return;
            }
            var detailModal = document.getElementById('propertyDetailModal');'''
if old7 in html:
    html = html.replace(old7, new7)
    changes += 1
    print("7. Click outside + ESC: OK")
else:
    print("7. Click outside + ESC: NOT FOUND")

# 8. Add inquiry-form.js and agent_slug override
old8 = '    <!-- \uc0c1\ub2f4 \ud3fc \uc81c\ucd9c \ucc98\ub9ac -->\n    \n\n    <!-- PropNet \ub3c4\uba54\uc778\ubcc4 \ub9c1\ud06c \ubd84\uae30 -->'
new8 = '''    <!-- \uc0c1\ub2f4 \ud3fc \uc81c\ucd9c \ucc98\ub9ac -->
    <script src="/js/inquiry-form.js"></script>
    <script>
    // PropMap\uc6a9: inquiry-form.js\uc758 submit-inquiry API \ud638\ucd9c\uc5d0 agent_slug \ucd94\uac00
    (function() {
        var _origFetch = window.fetch;
        window.fetch = function(url, options) {
            if (url === '/api/submit-inquiry' && options && options.body) {
                try {
                    var body = JSON.parse(options.body);
                    body.agent_slug = '{{AGENT_SLUG}}';
                    options.body = JSON.stringify(body);
                } catch(e) {}
            }
            return _origFetch.apply(this, arguments);
        };
    })();
    </script>

    <!-- PropNet \ub3c4\uba54\uc778\ubcc4 \ub9c1\ud06c \ubd84\uae30 -->'''
if old8 in html:
    html = html.replace(old8, new8)
    changes += 1
    print("8. inquiry-form.js + agent_slug: OK")
else:
    print("8. inquiry-form.js + agent_slug: NOT FOUND")

with open(template_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nTotal changes applied: {changes}/8")
print(f"File size: {len(html)} bytes")

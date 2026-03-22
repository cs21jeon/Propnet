#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(path, 'r') as f:
    html = f.read()

old = """                            <label>숫자 형식</label>
                            <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;">
                                <label style="display:flex;align-items:center;gap:4px;font-size:13px;cursor:pointer;">
                                    <input type="checkbox" x-model="editingField.numberFormat.thousands"> 1,000 단위 쉼표
                                </label>
                                <label style="display:flex;align-items:center;gap:4px;font-size:13px;cursor:pointer;">
                                    <input type="checkbox" x-model="editingField.numberFormat.allowNegative"> 음수 허용
                                </label>
                            </div>
                            <div style="display:flex;align-items:center;gap:8px;">
                                <label style="font-size:13px;white-space:nowrap;">소수점 자릿수</label>
                                <select x-model.number="editingField.numberFormat.decimals" style="padding:4px 8px;border:1px solid var(--gray-300);border-radius:4px;font-size:13px;">
                                    <option :value="-1">자동</option>
                                    <option :value="0">0 (정수)</option>
                                    <option :value="1">1</option>
                                    <option :value="2">2</option>
                                    <option :value="3">3</option>
                                    <option :value="4">4</option>
                                </select>
                                <span style="color:var(--gray-500);font-size:12px;" x-text="editingField.numberFormat.decimals >= 0 ? '예: ' + (1234.5678).toFixed(editingField.numberFormat.decimals) : '예: 1234.5678'"></span>
                            </div>"""

new = """                            <label>숫자 형식</label>
                            <div style="display:flex;gap:16px;align-items:center;white-space:nowrap;">
                                <label style="display:flex;align-items:center;gap:4px;font-size:13px;cursor:pointer;">
                                    <input type="checkbox" x-model="editingField.numberFormat.thousands"> 1,000 단위 쉼표
                                </label>
                                <label style="display:flex;align-items:center;gap:4px;font-size:13px;cursor:pointer;">
                                    <input type="checkbox" x-model="editingField.numberFormat.allowNegative"> 음수 허용
                                </label>
                            </div>
                            <div style="display:flex;align-items:center;gap:8px;white-space:nowrap;">
                                <label style="font-size:13px;">소수점 자릿수</label>
                                <select x-model.number="editingField.numberFormat.decimals" style="width:80px;padding:4px 8px;border:1px solid var(--gray-300);border-radius:4px;font-size:13px;">
                                    <option :value="-1">자동</option>
                                    <option :value="0">0 (정수)</option>
                                    <option :value="1">1</option>
                                    <option :value="2">2</option>
                                    <option :value="3">3</option>
                                    <option :value="4">4</option>
                                </select>
                                <span style="color:var(--gray-500);font-size:12px;" x-text="editingField.numberFormat.decimals >= 0 ? '예: ' + (1234.5678).toFixed(editingField.numberFormat.decimals) : '예: 1234.5678'"></span>
                            </div>"""

if old in html:
    html = html.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(html)
    print("OK")
else:
    print("WARN: pattern not found")

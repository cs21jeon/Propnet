#!/usr/bin/env python3
js_path = "/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js"
with open(js_path, "r") as f:
    js = f.read()

# saveFieldSettings: preserve column order after loadColumns
old = """                            this.showToast('필드 설정이 저장되었습니다', 'success');
                            this.closeFieldSettings();
                            await this.loadColumns();
                            await this.loadData();"""

new = """                            this.showToast('필드 설정이 저장되었습니다', 'success');
                            this.closeFieldSettings();
                            const savedVisible = [...this.visibleColumns];
                            await this.loadColumns();
                            this.applyColumnOrder();
                            this.visibleColumns = savedVisible.filter(k => this.allColumns.some(c => c.key === k));
                            await this.loadData();"""

if old in js:
    js = js.replace(old, new, 1)
    with open(js_path, "w") as f:
        f.write(js)
    print("OK - Preserved column order after field settings save")
else:
    print("WARN: pattern not found")

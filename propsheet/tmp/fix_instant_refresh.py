#!/usr/bin/env python3
"""Fix: refresh detail panel item after upload"""
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

# Fix triggerFileUpload: refresh detail panel item after loadData
old_trigger = """                triggerFileUpload(recordId, fieldName) {
                    const input = document.createElement('input');
                    input.type = 'file';
                    input.accept = 'image/*,.pdf,.doc,.docx,.xls,.xlsx,.hwp,.txt,.csv';
                    input.onchange = async (e) => {
                        const file = e.target.files[0];
                        if (!file) return;
                        const result = await this.uploadFile(recordId, fieldName, file);
                        if (result) {
                            await this.loadData();
                        }
                    };
                    input.click();
                },"""

new_trigger = """                triggerFileUpload(recordId, fieldName) {
                    const input = document.createElement('input');
                    input.type = 'file';
                    input.accept = 'image/*,.pdf,.doc,.docx,.xls,.xlsx,.hwp,.txt,.csv';
                    input.onchange = async (e) => {
                        const file = e.target.files[0];
                        if (!file) return;
                        const result = await this.uploadFile(recordId, fieldName, file);
                        if (result) {
                            await this.loadData();
                            // Refresh detail panel if open
                            if (this.detailPanel.show && this.detailPanel.item) {
                                const updated = this.items.find(i => i.id === recordId);
                                if (updated) this.detailPanel.item = {...updated};
                            }
                        }
                    };
                    input.click();
                },"""

if old_trigger in js:
    js = js.replace(old_trigger, new_trigger, 1)
    print("1. Fixed triggerFileUpload refresh")

# Fix handleFileDrop similarly
old_drop = """                async handleFileDrop(event, recordId, fieldName) {
                    event.preventDefault();
                    const files = event.dataTransfer.files;
                    if (files.length === 0) return;
                    for (let i = 0; i < files.length; i++) {
                        await this.uploadFile(recordId, fieldName, files[i]);
                    }
                    await this.loadData();
                },"""

new_drop = """                async handleFileDrop(event, recordId, fieldName) {
                    event.preventDefault();
                    const files = event.dataTransfer.files;
                    if (files.length === 0) return;
                    for (let i = 0; i < files.length; i++) {
                        await this.uploadFile(recordId, fieldName, files[i]);
                    }
                    await this.loadData();
                    if (this.detailPanel.show && this.detailPanel.item) {
                        const updated = this.items.find(i => i.id === this.detailPanel.item.id);
                        if (updated) this.detailPanel.item = {...updated};
                    }
                },"""

if old_drop in js:
    js = js.replace(old_drop, new_drop, 1)
    print("2. Fixed handleFileDrop refresh")

with open(js_path, 'w') as f:
    f.write(js)

# Bump version
html_path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/database_list.html'
with open(html_path, 'rb') as f:
    html = f.read()
html = html.replace(b'v=20260318c', b'v=20260318d')
with open(html_path, 'wb') as f:
    f.write(html)

print("Done!")

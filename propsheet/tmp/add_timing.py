#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(path, 'r') as f:
    js = f.read()

# Add timing logs to loadData
old = """                        const res = await fetch(`${basePath}/api/database/properties?${params}`);
                        if (!_checkAuth(res)) return;
                        const data = await res.json();

                        if (data.success) {
                            this.items = data.items;"""

new = """                        console.time('API fetch');
                        const res = await fetch(`${basePath}/api/database/properties?${params}`);
                        if (!_checkAuth(res)) return;
                        const data = await res.json();
                        console.timeEnd('API fetch');
                        console.log(`Received ${data.items ? data.items.length : 0} items, ${JSON.stringify(data).length/1024|0}KB`);

                        if (data.success) {
                            console.time('DOM render');
                            this.items = data.items;"""

old2 = """                    } catch (err) {
                        this.showToast('데이터 로딩 실패: ' + err.message, 'error');
                    }
                    this.loading = false;"""

new2 = """                        // Measure render time after Alpine processes the items
                        requestAnimationFrame(() => {
                            requestAnimationFrame(() => {
                                console.timeEnd('DOM render');
                            });
                        });
                    } catch (err) {
                        this.showToast('데이터 로딩 실패: ' + err.message, 'error');
                    }
                    this.loading = false;"""

if 'console.time' not in js:
    js = js.replace(old, new, 1)
    js = js.replace(old2, new2, 1)
    with open(path, 'w') as f:
        f.write(js)
    print("OK - Added timing logs")
else:
    print("Already has timing")

#!/usr/bin/env python3
js_path = '/home/webapp/goldenrabbit/backend/property-manager/static/js/propsheet/database_list.js'
with open(js_path, 'r') as f:
    js = f.read()

old = """                        case 'formula':
                            // Formula fields might contain URLs too
                            if (typeof value === 'string') {
                                const urlPattern = /^(https?:\\/\\/)/i;
                                if (urlPattern.test(value)) {
                                    const displayUrl = value.length > 50 ? value.substring(0, 47) + '...' : value;
                                    return `<a href="${value}" target="_blank" rel="noopener noreferrer" style="color: #667eea; text-decoration: underline;" onclick="event.stopPropagation();">${displayUrl}</a>`;
                                }
                            }
                            return value || '-';"""

new = """                        case 'formula': {
                            // If value is numeric, apply number formatting
                            const numVal = Number(value);
                            if (value !== null && value !== '' && !isNaN(numVal)) {
                                const fmt = col.numberFormat || {};
                                const decimals = (fmt.decimals !== undefined && fmt.decimals !== null) ? fmt.decimals : -1;
                                const thousands = fmt.thousands !== false;
                                const allowNeg = fmt.allowNegative !== false;
                                let v = (!allowNeg && numVal < 0) ? 0 : numVal;
                                if (decimals >= 0) {
                                    v = v.toFixed(decimals);
                                    if (thousands) {
                                        const parts = v.split('.');
                                        parts[0] = parts[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',');
                                        return parts.join('.');
                                    }
                                    return v;
                                }
                                return thousands ? numVal.toLocaleString() : String(numVal);
                            }
                            // URL detection for text results
                            if (typeof value === 'string') {
                                const urlPattern = /^(https?:\\/\\/)/i;
                                if (urlPattern.test(value)) {
                                    const displayUrl = value.length > 50 ? value.substring(0, 47) + '...' : value;
                                    return `<a href="${value}" target="_blank" rel="noopener noreferrer" style="color: #667eea; text-decoration: underline;" onclick="event.stopPropagation();">${displayUrl}</a>`;
                                }
                            }
                            return value || '-';
                        }"""

if old in js:
    js = js.replace(old, new, 1)
    with open(js_path, 'w') as f:
        f.write(js)
    print("OK - Formula now applies number formatting for numeric results")
else:
    print("WARN: pattern not found")

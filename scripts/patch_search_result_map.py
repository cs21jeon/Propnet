#!/usr/bin/env python3
"""Patch _generate_search_map_html: Add marker colors + dbId to detail postMessage
   Also add db_id to search-map API markers"""

FILE = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# ===== PATCH 1: Add db_id to search-map markers for all 3 types =====

# danil markers
old_danil = """                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'price': price_num,
                            'price_display': price_display,
                            'popup': popup,
                            'record_id': record_id,
                            'address': address,
                        })
                    elif property_type == 'jibhap':"""
new_danil = """                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'price': price_num,
                            'price_display': price_display,
                            'popup': popup,
                            'record_id': record_id,
                            'address': address,
                            'property_type': 'danil',
                            'transaction_type': '매매',
                            'db_id': 39,
                        })
                    elif property_type == 'jibhap':"""
if old_danil in content:
    content = content.replace(old_danil, new_danil)
    print("PATCH 1a: danil markers - added property_type/db_id")
else:
    print("WARN: danil search markers not found")

# jibhap markers
old_jibhap = """                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'price': price_num or deposit,
                            'price_display': pd,
                            'popup': popup,
                            'record_id': record_id,
                            'address': address,
                        })
                    else:  # bubun"""
new_jibhap = """                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'price': price_num or deposit,
                            'price_display': pd,
                            'popup': popup,
                            'record_id': record_id,
                            'address': address,
                            'property_type': 'jibhap',
                            'transaction_type': txn,
                            'db_id': 38,
                        })
                    else:  # bubun"""
if old_jibhap in content:
    content = content.replace(old_jibhap, new_jibhap)
    print("PATCH 1b: jibhap markers - added property_type/db_id")
else:
    print("WARN: jibhap search markers not found")

# bubun markers
old_bubun = """                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'price': deposit,
                            'price_display': pd,
                            'popup': popup,
                            'record_id': record_id,
                            'address': address,
                        })

    except Exception as e:
        import traceback
        logger.error(f"search-map DB 조회 실패"""
new_bubun = """                        markers.append({
                            'lat': to_float(row['coordinates_lat']),
                            'lon': to_float(row['coordinates_lon']),
                            'price': deposit,
                            'price_display': pd,
                            'popup': popup,
                            'record_id': record_id,
                            'address': address,
                            'property_type': 'bubun',
                            'transaction_type': txn,
                            'db_id': 43,
                        })

    except Exception as e:
        import traceback
        logger.error(f"search-map DB 조회 실패"""
if old_bubun in content:
    content = content.replace(old_bubun, new_bubun)
    print("PATCH 1c: bubun markers - added property_type/db_id")
else:
    print("WARN: bubun search markers not found")


# ===== PATCH 2: Update _generate_search_map_html - marker colors =====
old_marker_css = """        .price-marker {{
            background-color: #fff; border: 2px solid #e38000; border-radius: 6px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2); padding: 3px 8px; font-size: 12px;
            font-weight: bold; color: #e38000; white-space: nowrap; text-align: center;
            position: relative; cursor: pointer; transition: all 0.2s;
            font-family: -apple-system, sans-serif;
        }}
        .price-marker:hover {{ background-color: #e38000; color: white; transform: scale(1.1); }}
        .price-marker::after {{
            content: ''; position: absolute; bottom: -8px; left: 50%; margin-left: -6px;
            width: 0; height: 0; border-left: 6px solid transparent;
            border-right: 6px solid transparent; border-top: 8px solid #e38000;
        }}"""

new_marker_css = """        .price-marker {{
            border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            padding: 3px 8px; font-size: 11px; font-weight: bold; color: white;
            white-space: nowrap; text-align: center; position: relative;
            cursor: pointer; transition: all 0.15s; font-family: -apple-system, sans-serif;
        }}
        .price-marker:hover {{ transform: scale(1.1); z-index: 5; }}
        .price-marker::after {{
            content: ''; position: absolute; bottom: -7px; left: 50%; margin-left: -5px;
            width: 0; height: 0; border-left: 5px solid transparent;
            border-right: 5px solid transparent;
        }}
        .price-marker.danil-매매 {{ background: #1D4ED8; }}
        .price-marker.danil-매매::after {{ border-top: 7px solid #1D4ED8; }}
        .price-marker.jibhap-매매 {{ background: #15803D; }}
        .price-marker.jibhap-매매::after {{ border-top: 7px solid #15803D; }}
        .price-marker.jibhap-전세 {{ background: #22C55E; }}
        .price-marker.jibhap-전세::after {{ border-top: 7px solid #22C55E; }}
        .price-marker.jibhap-월세 {{ background: #86EFAC; color: #14532d; }}
        .price-marker.jibhap-월세::after {{ border-top: 7px solid #86EFAC; }}
        .price-marker.bubun-매매 {{ background: #C2410C; }}
        .price-marker.bubun-매매::after {{ border-top: 7px solid #C2410C; }}
        .price-marker.bubun-전세 {{ background: #EA580C; }}
        .price-marker.bubun-전세::after {{ border-top: 7px solid #EA580C; }}
        .price-marker.bubun-월세 {{ background: #FB923C; color: #431407; }}
        .price-marker.bubun-월세::after {{ border-top: 7px solid #FB923C; }}"""

if old_marker_css in content:
    content = content.replace(old_marker_css, new_marker_css)
    print("PATCH 2: marker CSS updated with type-based colors")
else:
    print("WARN: marker CSS not found")


# ===== PATCH 3: Update marker element creation - apply color class =====
old_marker_js = "                el.className = 'price-marker'; el.textContent = m.price_display;"
new_marker_js = "                el.className = 'price-marker ' + (m.property_type || 'danil') + '-' + (m.transaction_type || '매매'); el.textContent = m.price_display;"

if old_marker_js in content:
    content = content.replace(old_marker_js, new_marker_js)
    print("PATCH 3: marker JS updated with type-based class")
else:
    print("WARN: marker JS not found")


# ===== PATCH 4: Update postMessage to include dbId =====
old_post = "parent.postMessage({{action: 'openPropertyDetail', recordId: m.record_id}}, '*');"
new_post = "parent.postMessage({{action: 'openPropertyDetail', recordId: m.record_id, dbId: m.db_id}}, '*');"

if old_post in content:
    content = content.replace(old_post, new_post)
    print("PATCH 4: postMessage updated with dbId")
else:
    print("WARN: postMessage not found")


with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

# Verify syntax
import py_compile
try:
    py_compile.compile(FILE, doraise=True)
    print("SYNTAX CHECK: OK")
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
    import sys
    sys.exit(1)

print("SUCCESS: Search result map fully updated")

#!/usr/bin/env python3
"""Fix: handle Decimal type when serializing record to trash"""
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/database.py'
with open(path, 'r') as f:
    content = f.read()

# Fix the record_data serialization in delete_property_route
old = """                # Convert to serializable dict
                record_data = {}
                for k, v in record.items():
                    if hasattr(v, 'isoformat'):
                        record_data[k] = v.isoformat()
                    else:
                        record_data[k] = v"""

new = """                # Convert to serializable dict
                from decimal import Decimal
                record_data = {}
                for k, v in record.items():
                    if hasattr(v, 'isoformat'):
                        record_data[k] = v.isoformat()
                    elif isinstance(v, Decimal):
                        record_data[k] = float(v)
                    else:
                        record_data[k] = v"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(content)
    print("OK - Fixed Decimal serialization")
else:
    print("WARN: pattern not found")

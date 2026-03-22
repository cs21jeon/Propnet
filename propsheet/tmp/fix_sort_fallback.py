#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/services/database_service.py'
with open(path, 'r') as f:
    c = f.read()

# Add sort column validation - if sort_by doesn't exist in table, fall back to created_at or id
old = """            # Validate sort order (only ASC or DESC allowed)
            sort_order = 'DESC' if sort_order.lower() == 'desc' else 'ASC'

            # Escape column name for sorting (prevents SQL injection)
            # All columns are allowed since escape_column_name handles special characters
            sort_col = escape_column_name(sort_by)

            # Check if the column is text type for proper sorting
            cursor.execute(f\"\"\"
                SELECT data_type FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            \"\"\", (table_name, sort_by))
            col_type_result = cursor.fetchone()
            col_type = col_type_result['data_type'] if col_type_result else None"""

new = """            # Validate sort order (only ASC or DESC allowed)
            sort_order = 'DESC' if sort_order.lower() == 'desc' else 'ASC'

            # Check if the sort column exists in the table, fall back to created_at or id
            cursor.execute(f\"\"\"
                SELECT data_type FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            \"\"\", (table_name, sort_by))
            col_type_result = cursor.fetchone()
            if not col_type_result:
                # Sort column doesn't exist, try fallbacks
                for fallback in ['created_at', 'id']:
                    cursor.execute("SELECT data_type FROM information_schema.columns WHERE table_name = %s AND column_name = %s", (table_name, fallback))
                    col_type_result = cursor.fetchone()
                    if col_type_result:
                        sort_by = fallback
                        break

            sort_col = escape_column_name(sort_by)
            col_type = col_type_result['data_type'] if col_type_result else None"""

if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(c)
    print("OK - Added sort column fallback")
else:
    print("WARN: pattern not found")

#!/usr/bin/env python3
import sys

path = "/home/webapp/goldenrabbit/backend/property-manager/routes/database.py"
with open(path, "r") as f:
    content = f.read()

lines = content.split('\n')

# Find the start of export_csv function body
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if 'def export_csv():' in line:
        start_idx = i
    if start_idx and i > start_idx + 5 and line.strip().startswith('# Create CSV in memory'):
        end_idx = i
        break

if start_idx is None or end_idx is None:
    print(f"Could not find boundaries: start={start_idx}, end={end_idx}")
    sys.exit(1)

print(f"Replacing lines {start_idx+1} to {end_idx+1}")

new_body = """def export_csv():
    \"\"\"
    Export database to CSV file, optionally filtered by view settings.

    Query parameters:
    - db: Database ID (required)
    - view_id: View ID (optional - applies view's filter/sort/columns)
    \"\"\"
    try:
        database_id = request.args.get('db', type=int)
        if not database_id:
            return jsonify({'success': False, 'error': '\\ub370\\uc774\\ud130\\ubca0\\uc774\\uc2a4 ID\\uac00 \\ud544\\uc694\\ud569\\ub2c8\\ub2e4'}), 400

        view_id = request.args.get('view_id', type=int)

        from services.workspace_service import get_database
        db_info = get_database(database_id)
        if not db_info:
            return jsonify({'success': False, 'error': '\\ub370\\uc774\\ud130\\ubca0\\uc774\\uc2a4\\ub97c \\ucc3e\\uc744 \\uc218 \\uc5c6\\uc2b5\\ub2c8\\ub2e4'}), 404

        table_name = db_info['table_name']
        db_name = db_info['name']

        # Get all columns
        all_columns = get_table_columns(table_name)
        if not all_columns:
            return jsonify({'success': False, 'error': '\\ucee8\\ub7fc \\uc815\\ubcf4\\ub97c \\uac00\\uc838\\uc62c \\uc218 \\uc5c6\\uc2b5\\ub2c8\\ub2e4'}), 500

        # Load view settings if view_id provided
        view_columns = None
        view_filters = []
        view_sort_by = '\\ub808\\ucf54\\ub4dc\\uc0dd\\uc131\\uc77c\\uc790'
        view_sort_order = 'desc'
        view_filter_logic = 'and'
        view_name = None

        if view_id:
            from services.view_service import get_view
            view = get_view(view_id)
            if view and view.get('database_id') == database_id:
                view_name = view.get('name')
                # Parse column_config (supports both array and {columns, widths} format)
                cc = view.get('column_config')
                if cc:
                    if isinstance(cc, list):
                        view_columns = cc
                    elif isinstance(cc, dict) and 'columns' in cc:
                        view_columns = cc['columns']

                # Parse filter_config
                fc = view.get('filter_config')
                if fc and isinstance(fc, list):
                    view_filters = [f for f in fc if f.get('field')]

                # Parse sort_config
                sc = view.get('sort_config')
                if sc and isinstance(sc, dict):
                    view_sort_by = sc.get('sort_by', '\\ub808\\ucf54\\ub4dc\\uc0dd\\uc131\\uc77c\\uc790')
                    view_sort_order = sc.get('sort_order', 'desc')

        # Determine which columns to export
        if view_columns:
            columns = [c for c in all_columns if c['key'] in view_columns]
            # Maintain view column order
            col_order = {k: i for i, k in enumerate(view_columns)}
            columns.sort(key=lambda c: col_order.get(c['key'], 999))
        else:
            columns = all_columns

        column_names = [col['key'] for col in columns]

        # Build query with filters and sorting
        with get_db_connection() as conn:
            with get_db_cursor(conn, cursor_factory=RealDictCursor) as cursor:
                escaped_columns = [f'"' + col + '"' for col in column_names]
                select_clause = ', '.join(escaped_columns)

                # Build WHERE clause from view filters
                where_parts = []
                params = []

                for fr in view_filters:
                    field = fr.get('field')
                    operator = fr.get('operator')
                    value = fr.get('value')
                    if not field or not operator:
                        continue

                    ef = '"' + field + '"'

                    if operator == 'equals':
                        where_parts.append(f'{ef} = %s')
                        params.append(value)
                    elif operator == 'not_equals':
                        where_parts.append(f'({ef} IS NULL OR {ef} != %s)')
                        params.append(value)
                    elif operator == 'contains':
                        where_parts.append(f'{ef}::text ILIKE %s')
                        params.append(f'%{value}%')
                    elif operator == 'not_contains':
                        where_parts.append(f'({ef} IS NULL OR {ef}::text NOT ILIKE %s)')
                        params.append(f'%{value}%')
                    elif operator == 'gt':
                        where_parts.append(f'{ef} > %s')
                        params.append(value)
                    elif operator == 'lt':
                        where_parts.append(f'{ef} < %s')
                        params.append(value)
                    elif operator == 'gte':
                        where_parts.append(f'{ef} >= %s')
                        params.append(value)
                    elif operator == 'lte':
                        where_parts.append(f'{ef} <= %s')
                        params.append(value)
                    elif operator == 'is_empty':
                        where_parts.append(f'({ef} IS NULL OR {ef}::text = %s)')
                        params.append('')
                    elif operator == 'is_not_empty':
                        where_parts.append(f'({ef} IS NOT NULL AND {ef}::text != %s)')
                        params.append('')
                    elif operator == 'is_any_of':
                        options = [v.strip() for v in str(value).split(',') if v.strip()]
                        if options:
                            placeholders = ','.join(['%s'] * len(options))
                            where_parts.append(f'{ef}::text IN ({placeholders})')
                            params.extend(options)
                    elif operator == 'is_none_of':
                        options = [v.strip() for v in str(value).split(',') if v.strip()]
                        if options:
                            placeholders = ','.join(['%s'] * len(options))
                            where_parts.append(f'({ef} IS NULL OR {ef}::text NOT IN ({placeholders}))')
                            params.extend(options)

                where_sql = ''
                if where_parts:
                    joiner = ' OR ' if view_filter_logic == 'or' else ' AND '
                    where_sql = 'WHERE ' + joiner.join(where_parts)

                # Sort
                sort_order_sql = 'DESC' if view_sort_order.lower() == 'desc' else 'ASC'
                sort_col = '"' + view_sort_by + '"'

                query = f'SELECT {select_clause} FROM "{table_name}" {where_sql} ORDER BY {sort_col} {sort_order_sql} NULLS LAST'
                cursor.execute(query, params)
                rows = cursor.fetchall()"""

lines_new = lines[:start_idx] + new_body.split('\n') + lines[end_idx:]
content = '\n'.join(lines_new)

# Also update the filename to include view name
content = content.replace(
    'filename = f"{db_name}_{timestamp}.csv"',
    'suffix = f"_{view_name}" if view_name else ""\n        filename = f"{db_name}{suffix}_{timestamp}.csv"'
)

with open(path, 'w') as f:
    f.write(content)

print("OK - export_csv updated with view support")

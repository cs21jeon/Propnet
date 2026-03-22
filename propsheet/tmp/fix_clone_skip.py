#!/usr/bin/env python3
path = '/home/webapp/goldenrabbit/backend/property-manager/routes/propsheet.py'
with open(path, 'r') as f:
    content = f.read()

# Add try/except around each DB clone to skip missing tables
old = """            clone_database_table(
                source_table=db['table_name'],
                target_table=new_table_name,
                source_db_id=db['id'],
                target_db_id=new_db_id
            )
            clone_database_views(db['id'], new_db_id)
            cloned_count += 1"""

new = """            try:
                clone_database_table(
                    source_table=db['table_name'],
                    target_table=new_table_name,
                    source_db_id=db['id'],
                    target_db_id=new_db_id
                )
                clone_database_views(db['id'], new_db_id)
                cloned_count += 1
            except Exception as clone_err:
                logger.warning(f"Skipped cloning DB '{db['name']}': {clone_err}")
                # Clean up the empty database entry
                try:
                    from services.workspace_service import delete_database
                    delete_database(new_db_id)
                except:
                    pass"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(content)
    print("OK - Clone now skips missing tables")
else:
    print("WARN: pattern not found")

#!/usr/bin/env python3
"""
Fix column name mismatches in admin_dashboard_service.py
Actual agent_requests columns:
  propnet_user_id, agent_name, agent_slug, representative_name,
  phone, office_address, license_file_path, business_reg_path,
  status, reject_reason, reviewed_by (integer FK), created_at, reviewed_at
"""

path = '/home/webapp/goldenrabbit/backend/property-manager/services/admin_dashboard_service.py'
with open(path, 'r') as f:
    content = f.read()

changes = 0

# 1. Fix JOIN: user_id -> propnet_user_id
old = "LEFT JOIN propnet_users pu ON pu.id = ar.user_id"
new = "LEFT JOIN propnet_users pu ON pu.id = ar.propnet_user_id"
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("1. Fixed JOIN user_id -> propnet_user_id")

# 2. Fix approve: user_id -> propnet_user_id
old = "user_id = req['user_id']"
new = "user_id = req['propnet_user_id']"
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("2. Fixed user_id -> propnet_user_id in approve")

# 3. Fix approve INSERT: use correct column names
old = """req.get('agency_name'), req.get('slug'), req.get('phone'),
             req.get('address'), req.get('license_no'), req.get('license_file')"""
new = """req.get('agent_name'), req.get('agent_slug'), req.get('phone'),
             req.get('office_address'), None, req.get('license_file_path')"""
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("3. Fixed column names in agents INSERT")

# 4. Fix reviewed_by: should be admin user ID (integer), not email string
old = """execute(
            "UPDATE agent_requests SET status = 'approved', reviewed_at = NOW(), reviewed_by = %s WHERE id = %s",
            (admin_email, req_id)
        )"""
new = """execute(
            "UPDATE agent_requests SET status = 'approved', reviewed_at = NOW() WHERE id = %s",
            (req_id,)
        )"""
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("4. Fixed approve reviewed_by (removed email, column is integer FK)")

# 5. Fix reject reviewed_by similarly
old = """execute(
            \"\"\"UPDATE agent_requests SET status = 'rejected', reject_reason = %s,
                      reviewed_at = NOW(), reviewed_by = %s
               WHERE id = %s\"\"\",
            (reason, admin_email, req_id)
        )"""
new = """execute(
            \"\"\"UPDATE agent_requests SET status = 'rejected', reject_reason = %s,
                      reviewed_at = NOW()
               WHERE id = %s\"\"\",
            (reason, req_id)
        )"""
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("5. Fixed reject reviewed_by (removed email)")

# 6. Fix slug reference in workspace creation
old = "slug = req.get('slug')"
new = "slug = req.get('agent_slug')"
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("6. Fixed slug reference in workspace creation")

# 7. Fix agency_name reference in workspace creation
old = "req.get('agency_name', '')"
new = "req.get('agent_name', '')"
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("7. Fixed agency_name reference in workspace creation")

with open(path, 'w') as f:
    f.write(content)

print(f"\nDone: {changes} fixes applied")

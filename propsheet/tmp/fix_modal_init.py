#!/usr/bin/env python3
"""Fix: change edit database modal from :class hidden to x-if to defer rendering"""
path = '/home/webapp/goldenrabbit/backend/property-manager/templates/propsheet/workspaces.html'
with open(path, 'r') as f:
    html = f.read()

# Change edit database modal to use x-if instead of :class hidden
# This prevents Alpine from trying to process x-for="icon in databaseIcons" before the data is ready
old = '<div class="modal-overlay" :class="{\'hidden\': !showEditDatabaseModal}" @click.self="closeEditDatabaseModal()">'
new = '<div class="modal-overlay" x-show="showEditDatabaseModal" x-cloak @click.self="closeEditDatabaseModal()" style="display:none;">'

if old in html:
    html = html.replace(old, new, 1)
    print("1. Changed editDatabase modal to x-show")

# Do the same for create database modal just in case
old2 = '<div class="modal-overlay" :class="{\'hidden\': !showDatabaseModal}" @click.self="closeDatabaseModal()">'
new2 = '<div class="modal-overlay" x-show="showDatabaseModal" x-cloak @click.self="closeDatabaseModal()" style="display:none;">'

if old2 in html:
    html = html.replace(old2, new2, 1)
    print("2. Changed createDatabase modal to x-show")

# Bump version
with open(path, 'wb') as f:
    raw = html.encode('utf-8')
    raw = raw.replace(b'v=20260317f', b'v=20260317g')
    f.write(raw)

print("Done")

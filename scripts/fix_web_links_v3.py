#!/usr/bin/env python3
"""
PropNet 웹 링크 v3 패치
========================
1. Proppedia 사이드메뉴 금토끼 링크 HTML 구조 수정 (태그 순서 뒤바뀜)
2. Proppedia 정적 리소스(favicon, icon, manifest) 경로 복원 → /app/ 절대경로
   (propnet.kr Nginx가 /proppedia/ 정적파일을 서빙하지 않으므로 /app/ 사용)

사용법: ssh root@175.119.224.71 'python3 -' < fix_web_links_v3.py
"""

import os
import re
import shutil
from datetime import datetime

PUBLIC = "/home/webapp/goldenrabbit/frontend/public"
APP_DIR = os.path.join(PUBLIC, "app")

MODIFIED_COUNT = 0
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
BACKUP_DIR = os.path.join(PUBLIC, f'_backup_links_v3_{ts}')


def backup_file(filepath):
    rel = os.path.relpath(filepath, PUBLIC)
    dst = os.path.join(BACKUP_DIR, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(filepath, dst)


def fix_sidemenu_html(filepath):
    """사이드메뉴 <a> 태그 순서 수정: 금토끼 링크 내용이 비어있는 문제"""
    global MODIFIED_COUNT
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # 현재 깨진 구조 (금토끼 <a> 열림 → 사용가이드 <a> 열림 → 닫힘 → 금토끼 콘텐츠 → 닫힘)
    broken_pattern = (
        '<a href="/propmap/goldenrabbit/" class="block w-full text-left px-4 py-3 '
        'hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors '
        'text-slate-900 dark:text-slate-100 no-underline">\n'
        '                <a href="/proppedia/guide/" class="block w-full text-left px-4 py-3 '
        'hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors '
        'text-slate-900 dark:text-slate-100 no-underline">\n'
        '                    <span class="material-symbols-outlined inline-block mr-3">menu_book</span>\n'
        '                    사용가이드\n'
        '                </a>\n'
        '                    <span class="material-symbols-outlined inline-block mr-3">real_estate_agent</span>\n'
        '                    금토끼부동산 매물정보\n'
        '                </a>'
    )

    # 수정된 구조 (각 <a> 태그가 자기 콘텐츠를 가짐)
    fixed_html = (
        '<a href="/propmap/goldenrabbit/" class="block w-full text-left px-4 py-3 '
        'hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors '
        'text-slate-900 dark:text-slate-100 no-underline">\n'
        '                    <span class="material-symbols-outlined inline-block mr-3">real_estate_agent</span>\n'
        '                    금토끼부동산 매물정보\n'
        '                </a>\n'
        '                <a href="/proppedia/guide/" class="block w-full text-left px-4 py-3 '
        'hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors '
        'text-slate-900 dark:text-slate-100 no-underline">\n'
        '                    <span class="material-symbols-outlined inline-block mr-3">menu_book</span>\n'
        '                    사용가이드\n'
        '                </a>'
    )

    content = content.replace(broken_pattern, fixed_html)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        MODIFIED_COUNT += 1
        return True
    return False


def fix_static_resources(filepath):
    """정적 리소스 경로를 /app/ 절대경로로 복원 (Nginx 호환)"""
    global MODIFIED_COUNT
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # favicon, icon, manifest, apple-touch-icon → /app/ 절대경로로 복원
    # 이 리소스들은 <head>의 <link> 태그에서 사용되며, Nginx가 /app/ 경로로만 서빙
    static_files = [
        'manifest.json', 'favicon.png', 'icon-192x192.png',
        'icon-512x512.png', 'apple-touch-icon.png',
    ]

    for fname in static_files:
        # href="filename" → href="/app/filename" (rel 태그에서만)
        content = re.sub(
            rf'((?:href|src)=")({re.escape(fname)}")',
            rf'\g<1>/app/{fname}"',
            content
        )

    # sw.js (service worker) 도 /app/ 경로 필요
    content = content.replace("'/sw.js'", "'/app/sw.js'")
    content = content.replace('"sw.js"', '"/app/sw.js"')
    # navigator.serviceWorker.register('sw.js') → '/app/sw.js'
    content = re.sub(
        r"register\('sw\.js'\)",
        "register('/app/sw.js')",
        content
    )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        MODIFIED_COUNT += 1
        return True
    return False


def main():
    print("=" * 60)
    print("PropNet 웹 링크 v3 패치")
    print("=" * 60)
    print(f"백업: {BACKUP_DIR}")
    print()

    # 모든 app/*.html 파일 처리
    print("[1/2] Proppedia 사이드메뉴 HTML 수정")
    for fname in sorted(os.listdir(APP_DIR)):
        if not fname.endswith('.html'):
            continue
        fpath = os.path.join(APP_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        backup_file(fpath)
        changed = fix_sidemenu_html(fpath)
        if changed:
            print(f"  [수정됨] {fname} - 사이드메뉴 구조")

    print()
    print("[2/2] 정적 리소스 경로 복원 (/app/ 절대경로)")
    for fname in sorted(os.listdir(APP_DIR)):
        if not fname.endswith('.html'):
            continue
        fpath = os.path.join(APP_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        # 이미 백업됨
        changed = fix_static_resources(fpath)
        if changed:
            print(f"  [수정됨] {fname} - 정적 리소스 경로")

    print()
    print("=" * 60)
    print(f"완료! {MODIFIED_COUNT}개 수정")
    print()

    # 검증
    print("--- 검증 ---")
    idx_path = os.path.join(APP_DIR, "index.html")
    with open(idx_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 사이드메뉴 금토끼 링크
    if 'real_estate_agent</span>\n                    금토끼부동산 매물정보\n                </a>' in content:
        print("  [OK] 금토끼부동산 매물정보 링크 내용 있음")
    else:
        print("  [FAIL] 금토끼부동산 매물정보 링크 확인 필요")

    # 아이콘 경로
    if 'href="/app/icon-192x192.png"' in content:
        print("  [OK] icon-192x192.png → /app/ 절대경로")
    else:
        print("  [FAIL] icon-192x192.png 경로 확인 필요")

    if 'href="/app/manifest.json"' in content:
        print("  [OK] manifest.json → /app/ 절대경로")
    else:
        print("  [FAIL] manifest.json 경로 확인 필요")


if __name__ == '__main__':
    main()

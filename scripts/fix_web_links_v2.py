#!/usr/bin/env python3
"""
PropNet 웹 링크 통합 v2 패치
==============================
v1에서 누락된 패턴 추가 수정:
  1. Proppedia: fetch('/app/api/...') → fetch('api/...')
  2. Proppedia: 템플릿 리터럴 `/app/xxx` → `xxx`
  3. Proppedia: window.open('/app/...') → window.open('...')
  4. 금토끼 서브페이지: href="/" → 상대경로

사용법: ssh root@175.119.224.71 'python3 -' < fix_web_links_v2.py
"""

import os
import re
import shutil
from datetime import datetime

PUBLIC = "/home/webapp/goldenrabbit/frontend/public"
APP_DIR = os.path.join(PUBLIC, "app")

MODIFIED_COUNT = 0
BACKUP_DIR = ""


def backup_file(filepath):
    rel = os.path.relpath(filepath, PUBLIC)
    dst = os.path.join(BACKUP_DIR, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(filepath, dst)


def fix_proppedia_v2(filepath):
    """Proppedia 페이지 v2 패치: API fetch, 템플릿 리터럴, window.open"""
    global MODIFIED_COUNT
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # 1. fetch('/app/api/...') → fetch('api/...')
    content = re.sub(r"fetch\('/app/api/", "fetch('api/", content)
    content = re.sub(r'fetch\("/app/api/', 'fetch("api/', content)

    # 2. fetch('/app/...' + ...) 패턴 (변수 연결)
    content = re.sub(r"fetch\('/app/([^']*)'", r"fetch('\1'", content)
    content = re.sub(r'fetch\("/app/([^"]*)"', r'fetch("\1"', content)

    # 3. 템플릿 리터럴: `/app/something...`  →  `something...`
    content = re.sub(r'`/app/([^`]+)`', r'`\1`', content)

    # 4. window.open('/app/...') → window.open('...')
    content = re.sub(r"window\.open\('/app/([^']*)'", r"window.open('\1'", content)
    content = re.sub(r'window\.open\("/app/([^"]*)"', r'window.open("\1"', content)

    # 5. 남은 '/app/' 또는 "/app/" 패턴 (JS 내 문자열)
    #    canonical URL 등 HTML attribute의 full URL은 건드리지 않음
    #    return 문: return '/app/' → return './'
    content = re.sub(r"return\s+params\.get\('redirect'\)\s*\|\|\s*'/app/'",
                     "return params.get('redirect') || './'", content)

    # 6. 나머지 JS 내 '/app/' (비 fetch, 비 href)
    #    안전하게: 줄 단위로 처리, HTML attribute는 건드리지 않음
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        # canonical, og:url 등 full URL은 스킵
        if 'canonical' in line or 'og:url' in line or 'goldenrabbit.biz/app' in line:
            new_lines.append(line)
            continue
        # JS 라인에서 남은 /app/ 패턴 처리
        if '/app/' in line and ('fetch' in line or 'href' in line or 'location' in line or 'open' in line or 'url' in line.lower()):
            # 이미 처리된 패턴이 남았을 수 있으므로 한번 더 치환
            line = re.sub(r"'/app/([^']*)'", r"'\1'", line)
            line = re.sub(r'"/app/([^"]*)"', r'"\1"', line)
            line = re.sub(r'`/app/([^`]*)`', r'`\1`', line)
            # 빈 문자열 보정
            line = line.replace("''", "'./'").replace('""', '"./"') if "location" in line else line
        new_lines.append(line)
    content = '\n'.join(new_lines)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        MODIFIED_COUNT += 1
        return True
    return False


def fix_goldenrabbit_subpage_v2(filepath):
    """금토끼 서브페이지(about.html, inquiry.html) 홈 링크 수정"""
    global MODIFIED_COUNT
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # href="/" → href="./" (금토끼 홈으로 돌아가기)
    # 단, canonical URL, og:url 등 full URL은 건드리지 않음
    # 패턴: href="/" 만 정확히 매치 (href="/something"은 이미 v1에서 처리됨)
    content = re.sub(r'href="/"', 'href="./"', content)
    content = re.sub(r"href='/'", "href='./'", content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        MODIFIED_COUNT += 1
        return True
    return False


def main():
    global BACKUP_DIR, MODIFIED_COUNT

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    BACKUP_DIR = os.path.join(PUBLIC, f'_backup_links_v2_{ts}')

    print("=" * 60)
    print("PropNet 웹 링크 통합 v2 패치")
    print("=" * 60)
    print(f"백업: {BACKUP_DIR}")
    print()

    # 1. Proppedia HTML + JS
    print("[1/2] Proppedia (app/*.html, app/*.js, app/js/*.js)")
    for dirpath in [APP_DIR, os.path.join(APP_DIR, "js")]:
        if not os.path.isdir(dirpath):
            continue
        for fname in sorted(os.listdir(dirpath)):
            if not (fname.endswith('.html') or fname.endswith('.js')):
                continue
            fpath = os.path.join(dirpath, fname)
            if not os.path.isfile(fpath):
                continue
            backup_file(fpath)
            changed = fix_proppedia_v2(fpath)
            label = os.path.relpath(fpath, PUBLIC)
            print(f"  [{'수정됨' if changed else '변경없음'}] {label}")
    print()

    # 2. 금토끼 서브페이지 홈 링크
    print("[2/2] 금토끼 서브페이지 (about.html, inquiry.html)")
    for fname in ['about.html', 'inquiry.html']:
        fpath = os.path.join(PUBLIC, fname)
        if not os.path.isfile(fpath):
            print(f"  [SKIP] {fname}")
            continue
        backup_file(fpath)
        changed = fix_goldenrabbit_subpage_v2(fpath)
        print(f"  [{'수정됨' if changed else '변경없음'}] {fname}")
    print()

    print("=" * 60)
    print(f"완료! {MODIFIED_COUNT}개 파일 수정")
    print(f"롤백: cp -r {BACKUP_DIR}/* {PUBLIC}/")
    print()

    # 잔존 /app/ 확인
    print("--- 잔존 /app/ 확인 (canonical/og 제외) ---")
    for dirpath in [APP_DIR, os.path.join(APP_DIR, "js")]:
        if not os.path.isdir(dirpath):
            continue
        for fname in sorted(os.listdir(dirpath)):
            fpath = os.path.join(dirpath, fname)
            if not os.path.isfile(fpath):
                continue
            with open(fpath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if '/app/' in line and 'canonical' not in line and 'og:url' not in line and 'goldenrabbit.biz/app' not in line:
                    label = os.path.relpath(fpath, PUBLIC)
                    print(f"  {label}:{i}: {line.strip()[:100]}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
PropNet 웹페이지 링크 통합 스크립트
===================================
goldenrabbit.biz와 propnet.kr 양쪽에서 모든 내비게이션 링크가 정상 동작하도록 수정합니다.

사용법:
  서버에서 직접 실행:
    python3 fix_web_links.py

  또는 로컬에서 SSH로 실행:
    ssh root@175.119.224.71 'python3 -' < fix_web_links.py

변경 요약:
  1. Proppedia 웹(app/*.html): /app/ 절대경로 → 상대경로
     - 사용자가 propnet.kr/proppedia/ 에서 접속해도 URL이 /proppedia/ 내에서 유지됨
  2. 금토끼부동산 홈(index.html 등): /about.html 등 → 상대경로
     - propnet.kr/propmap/goldenrabbit/ 에서 접속해도 내부 링크 정상 동작
  3. 크로스사이트 링크: 도메인 감지 JS로 자동 분기
     - 금토끼→Proppedia: goldenrabbit.biz=/app/, propnet.kr=/proppedia/
  4. /images/, /uploads/, /propsheet/api/ 등 서버 전역 경로는 변경하지 않음
  5. canonical URL, OG 메타태그는 변경하지 않음 (SEO 별도 관리)

주의: Flutter 앱 코드는 수정하지 않음 (앱 영향 없음)
"""

import os
import re
import shutil
from datetime import datetime

PUBLIC = "/home/webapp/goldenrabbit/frontend/public"
APP_DIR = os.path.join(PUBLIC, "app")
PROPMAP_GOLDENRABBIT_DIR = os.path.join(PUBLIC, "propmap", "goldenrabbit")

# 도메인 감지 + 크로스사이트 링크 분기 JS (금토끼 페이지용)
CROSS_SITE_JS_GOLDENRABBIT = """
    <!-- PropNet 도메인별 링크 분기 -->
    <script>
    (function() {
        var host = window.location.hostname;
        // propnet.kr에서는 /app/ 링크를 /proppedia/로 변환
        if (host === 'propnet.kr') {
            document.querySelectorAll('a[href^="/app"]').forEach(function(a) {
                a.href = a.getAttribute('href').replace(/^\\/app(\\/|$)/, '/proppedia/');
            });
        }
        // goldenrabbit.biz에서 /propmap/goldenrabbit/ 경로로 접속한 경우 내부 링크 보정
        if (host === 'goldenrabbit.biz' && window.location.pathname.indexOf('/propmap/goldenrabbit') === 0) {
            document.querySelectorAll('a[href^="/app"]').forEach(function(a) {
                a.href = a.getAttribute('href');  // /app/ 유지 (goldenrabbit.biz에서 동작)
            });
        }
    })();
    </script>"""

# 도메인 감지 JS (Proppedia 페이지용)
CROSS_SITE_JS_PROPPEDIA = """
    <!-- PropNet 도메인별 링크 분기 -->
    <script>
    (function() {
        var host = window.location.hostname;
        var path = window.location.pathname;
        // goldenrabbit.biz/app/ 에서 접속한 경우, /propmap/goldenrabbit/ 이 있으니 그대로 OK
        // propnet.kr/proppedia/ 에서 접속한 경우도 /propmap/goldenrabbit/ 동작
        // 추가 분기가 필요한 경우 여기에 작성
    })();
    </script>"""

MODIFIED_COUNT = 0
BACKUP_DIR = ""


def backup_file(filepath):
    """파일 백업"""
    rel = os.path.relpath(filepath, PUBLIC)
    dst = os.path.join(BACKUP_DIR, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(filepath, dst)


def fix_proppedia_page(filepath):
    """
    Proppedia 웹페이지(app/*.html) 링크 수정
    /app/xxx → xxx (상대경로)
    """
    global MODIFIED_COUNT
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # === HTML href 속성 ===
    # href="/app/" → href="./"  (홈 링크)
    content = content.replace('href="/app/"', 'href="./"')
    content = content.replace("href='/app/'", "href='./'")

    # href="/app/something.html" → href="something.html"
    content = re.sub(r'href="/app/([^"]+)"', r'href="\1"', content)
    content = re.sub(r"href='/app/([^']+)'", r"href='\1'", content)

    # === JavaScript window.location.href ===
    # window.location.href = '/app/' → './'
    content = re.sub(
        r"(window\.location\.href\s*=\s*)'/app/'",
        r"\1'./'",
        content
    )
    content = re.sub(
        r'(window\.location\.href\s*=\s*)"/app/"',
        r'\1"./"',
        content
    )

    # window.location.href = '/app/something.html' → 'something.html'
    content = re.sub(
        r"(window\.location\.href\s*=\s*)'/app/([^']+)'",
        r"\1'\2'",
        content
    )
    content = re.sub(
        r'(window\.location\.href\s*=\s*)"/app/([^"]+)"',
        r'\1"\2"',
        content
    )

    # === script src, link href (CSS/manifest/icon) ===
    # src="/app/something" → src="something"
    content = re.sub(r'src="/app/([^"]+)"', r'src="\1"', content)

    # <link href="/app/manifest.json"> → <link href="manifest.json">
    # 주의: canonical URL은 full URL이므로 이 패턴에 걸리지 않음
    content = re.sub(r'href="/app/([^"]*\.(json|png|css|ico|js))"', r'href="\1"', content)

    # === onclick 등 인라인 핸들러 ===
    content = re.sub(
        r"window\.location\.href\s*=\s*'/app/([^']*)'",
        r"window.location.href='\1'",
        content
    )

    # 변경 후 빈 상대경로 보정 (혹시 남은 것)
    content = content.replace("href=''", "href='./'")
    content = content.replace('href=""', 'href="./"')

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        MODIFIED_COUNT += 1
        return True
    return False


def fix_goldenrabbit_page(filepath):
    """
    금토끼부동산 홈페이지(*.html) 링크 수정
    /about.html 등 → about.html (상대경로)
    /app/ → 도메인별 분기 JS
    """
    global MODIFIED_COUNT
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # === 같은 사이트 내부 링크 → 상대경로 ===
    root_pages = [
        'about.html', 'inquiry.html', 'privacy-policy.html',
        'terms-of-service.html', 'data-deletion.html', 'account-delete.html',
        'map.html', 'index.html',
    ]
    for page in root_pages:
        # href="/page.html" → href="page.html"
        content = content.replace(f'href="/{page}"', f'href="{page}"')
        content = content.replace(f"href='/{page}'", f"href='{page}'")

    # src="/map.html" → src="map.html" (iframe)
    content = content.replace('src="/map.html"', 'src="map.html"')

    # === 크로스사이트 링크 분기 JS 추가 ===
    marker = '<!-- PropNet 도메인별 링크 분기 -->'
    if marker not in content:
        content = content.replace('</body>', CROSS_SITE_JS_GOLDENRABBIT + '\n</body>')

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        MODIFIED_COUNT += 1
        return True
    return False


def fix_js_file(filepath):
    """
    app/ 디렉토리의 JS 파일에서 /app/ 경로 수정
    """
    global MODIFIED_COUNT
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # fetch('/app/api/...') → fetch('api/...')   (Proppedia 자체 API)
    content = re.sub(r"fetch\('/app/(api/[^']+)'\)", r"fetch('\1')", content)
    content = re.sub(r'fetch\("/app/(api/[^"]+)"\)', r'fetch("\1")', content)

    # '/app/something.html' → 'something.html'
    content = re.sub(r"'/app/([^']+\.html)'", r"'\1'", content)
    content = re.sub(r'"/app/([^"]+\.html)"', r'"\1"', content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        MODIFIED_COUNT += 1
        return True
    return False


def process_directory(dirpath, fix_func, extensions=('.html',), label=""):
    """디렉토리 내 파일 일괄 처리"""
    if not os.path.isdir(dirpath):
        print(f"  [SKIP] 디렉토리 없음: {dirpath}")
        return

    files = sorted(f for f in os.listdir(dirpath)
                   if any(f.endswith(ext) for ext in extensions))

    if not files:
        print(f"  [SKIP] {label}: 대상 파일 없음")
        return

    for fname in files:
        fpath = os.path.join(dirpath, fname)
        if not os.path.isfile(fpath):
            continue
        backup_file(fpath)
        changed = fix_func(fpath)
        status = "수정됨" if changed else "변경없음"
        print(f"  [{status}] {fname}")


def main():
    global BACKUP_DIR, MODIFIED_COUNT

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    BACKUP_DIR = os.path.join(PUBLIC, f'_backup_links_{ts}')

    print("=" * 60)
    print("PropNet 웹 링크 통합 스크립트")
    print("=" * 60)
    print(f"대상 경로: {PUBLIC}")
    print(f"백업 경로: {BACKUP_DIR}")
    print()

    # 1. Proppedia 웹 (app/*.html)
    print("[1/4] Proppedia 웹 HTML (app/*.html)")
    print("      /app/xxx → xxx (상대경로)")
    process_directory(APP_DIR, fix_proppedia_page, ('.html',), "app HTML")
    print()

    # 2. Proppedia JS 파일 (app/*.js, app/js/*.js)
    print("[2/4] Proppedia JS 파일 (app/*.js)")
    process_directory(APP_DIR, fix_js_file, ('.js',), "app JS")
    app_js_dir = os.path.join(APP_DIR, "js")
    if os.path.isdir(app_js_dir):
        process_directory(app_js_dir, fix_js_file, ('.js',), "app/js JS")
    print()

    # 3. 금토끼부동산 홈 (root *.html)
    print("[3/4] 금토끼부동산 홈 (root HTML)")
    print("      /about.html → about.html + 크로스사이트 JS")
    target_files = ['index.html', 'about.html', 'inquiry.html', 'map.html',
                    'privacy-policy.html', 'terms-of-service.html']
    for fname in target_files:
        fpath = os.path.join(PUBLIC, fname)
        if os.path.isfile(fpath):
            backup_file(fpath)
            changed = fix_goldenrabbit_page(fpath)
            status = "수정됨" if changed else "변경없음"
            print(f"  [{status}] {fname}")
        else:
            print(f"  [SKIP] {fname} (파일 없음)")
    print()

    # 4. PropMap/goldenrabbit 복사본 (있을 경우)
    print("[4/4] PropMap/goldenrabbit (propmap/goldenrabbit/*.html)")
    process_directory(PROPMAP_GOLDENRABBIT_DIR, fix_goldenrabbit_page,
                      ('.html',), "propmap/goldenrabbit")
    print()

    # 결과 요약
    print("=" * 60)
    print(f"완료! 총 {MODIFIED_COUNT}개 파일 수정됨")
    print(f"롤백: cp -r {BACKUP_DIR}/* {PUBLIC}/")
    print()
    print("변경 후 확인사항:")
    print("  1. https://goldenrabbit.biz/ → 사이드메뉴 링크 클릭 테스트")
    print("  2. https://goldenrabbit.biz/app/ → 내부 링크 이동 테스트")
    print("  3. https://propnet.kr/proppedia/ → 내부 링크 이동 테스트")
    print("  4. https://propnet.kr/propmap/goldenrabbit/ → 사이드메뉴 링크 테스트")
    print("  5. 양쪽 도메인에서 크로스사이트 링크 (금토끼↔Proppedia) 테스트")


if __name__ == '__main__':
    main()

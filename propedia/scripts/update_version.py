#!/usr/bin/env python3
"""
버전 업데이트 스크립트

사용법:
  python scripts/update_version.py 1.0.3+11

변경 대상:
  1. pubspec.yaml (Flutter 앱 - package_info_plus가 자동으로 읽음)
  2. 서버: /app/about.html (웹페이지 앱 정보)

Flutter 앱 내 버전 표시 (profile_screen, app_drawer)는
package_info_plus가 pubspec.yaml에서 자동으로 읽으므로 수정 불필요.
"""

import sys
import re
import subprocess


def update_pubspec(version: str) -> bool:
    """pubspec.yaml 버전 업데이트"""
    filepath = 'pubspec.yaml'
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = re.sub(
            r'^version:\s*\S+',
            f'version: {version}',
            content,
            count=1,
            flags=re.MULTILINE,
        )

        if new_content == content:
            print(f'  [SKIP] {filepath}: 이미 {version}')
            return True

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'  [OK] {filepath}: -> {version}')
        return True
    except Exception as e:
        print(f'  [FAIL] {filepath}: {e}')
        return False


def update_web_about(version: str) -> bool:
    """서버의 /app/about.html 버전 업데이트"""
    remote_path = '/home/webapp/goldenrabbit/frontend/public/app/about.html'
    cmd = f"ssh root@175.119.224.71 \"sed -i 's/버전 [0-9][0-9.+]*/버전 {version}/' {remote_path}\""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f'  [OK] {remote_path}: -> 버전 {version}')
            return True
        else:
            print(f'  [FAIL] {remote_path}: {result.stderr}')
            return False
    except Exception as e:
        print(f'  [FAIL] {remote_path}: {e}')
        return False


def main():
    if len(sys.argv) < 2:
        print('사용법: python scripts/update_version.py <version>')
        print('예시:   python scripts/update_version.py 1.0.3+11')
        sys.exit(1)

    version = sys.argv[1]

    # 버전 형식 검증
    if not re.match(r'^\d+\.\d+\.\d+\+\d+$', version):
        print(f'오류: 버전 형식이 올바르지 않습니다: {version}')
        print('형식: X.Y.Z+N (예: 1.0.3+11)')
        sys.exit(1)

    print(f'버전 업데이트: {version}')
    print()

    results = []
    results.append(('pubspec.yaml', update_pubspec(version)))
    results.append(('web about.html', update_web_about(version)))

    print()
    all_ok = all(r[1] for r in results)
    if all_ok:
        print('모든 버전 업데이트 완료!')
        print()
        print('다음 단계:')
        print('  flutter build apk --release')
        print('  flutter build appbundle --release')
    else:
        print('일부 업데이트 실패!')
        sys.exit(1)


if __name__ == '__main__':
    main()

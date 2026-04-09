#!/usr/bin/env python3
"""PropMap 템플릿을 헤더/바디/푸터 레이아웃으로 재구성"""

path = '/home/webapp/goldenrabbit/frontend/public/propmap/_template/index.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. CSS: html,body 100% + flexbox 레이아웃으로 변경
old_css = """        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            font-family: 'Noto Sans KR', sans-serif;
        }
        #map {
            width: 100%;
            height: 100%;
        }"""

new_css = """        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            font-family: 'Noto Sans KR', sans-serif;
        }
        .page-wrapper {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        .page-header {
            background: #fff;
            border-bottom: 1px solid #e0e0e0;
            padding: 10px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 1001;
            flex-shrink: 0;
        }
        .page-header .logo {
            font-size: 17px;
            font-weight: 700;
            color: #222;
            text-decoration: none;
        }
        .page-header .logo span {
            color: #2962FF;
        }
        .page-header .header-sub {
            font-size: 11px;
            color: #888;
        }
        .map-container {
            flex: 1;
            position: relative;
            overflow: hidden;
        }
        #map {
            width: 100%;
            height: 100%;
        }
        .page-footer {
            background: #f8f8f8;
            border-top: 1px solid #eee;
            padding: 12px 16px;
            text-align: center;
            font-size: 11px;
            color: #999;
            flex-shrink: 0;
        }
        .page-footer a {
            color: #2962FF;
            text-decoration: none;
        }"""

if old_css in c:
    c = c.replace(old_css, new_css)
    print('[1] CSS 교체 완료')
else:
    print('[1] CSS 패턴 불일치')

# 2. body 구조: 헤더 + map-container 래퍼 + 푸터
old_body_start = """<body>
    <div id="map"></div>"""

new_body_start = """<body>
    <div class="page-wrapper">
    <header class="page-header">
        <a href="/propmap/{{AGENT_SLUG}}/" class="logo">{{AGENT_NAME}} <span>매물지도</span></a>
        <span class="header-sub">{{AGENT_SLUG}}.propnet.kr</span>
    </header>
    <div class="map-container">
    <div id="map"></div>"""

if old_body_start in c:
    c = c.replace(old_body_start, new_body_start)
    print('[2] body 시작 교체 완료')
else:
    print('[2] body 시작 패턴 불일치')

# 3. 푸터 + 닫는 태그
old_footer = """    <div style="text-align:center;padding:12px 0;font-size:11px;color:#999;background:#f8f8f8;border-top:1px solid #eee;">
      <div>&copy; {{COPYRIGHT_YEAR}} {{AGENT_NAME}}. All rights reserved.</div>
      <div style="margin-top:2px;">Designed &amp; Built by <a href="https://propnet.kr" target="_blank" style="color:#2962FF;text-decoration:none;">PropNet</a></div>
    </div>
</body>"""

new_footer = """    </div><!-- /map-container -->
    <footer class="page-footer">
      <div>&copy; {{COPYRIGHT_YEAR}} {{AGENT_NAME}}. All rights reserved.</div>
      <div style="margin-top:2px;">Designed &amp; Built by <a href="https://propnet.kr" target="_blank">PropNet</a></div>
    </footer>
    </div><!-- /page-wrapper -->
</body>"""

if old_footer in c:
    c = c.replace(old_footer, new_footer)
    print('[3] 푸터 교체 완료')
else:
    print('[3] 푸터 패턴 불일치')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

# 4. goldenrabbit 인스턴스에도 적용 (재생성)
print('\n[4] goldenrabbit 인스턴스 재생성...')
import sys
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.propmap_setup_service import create_propmap_page
result = create_propmap_page('goldenrabbit', '금토끼부동산', '11590-2024-00048', '서울특별시 동작구 사당로16나길 55')
print(f'    결과: {result}')
print('완료')

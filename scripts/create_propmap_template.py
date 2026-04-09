#!/usr/bin/env python3
"""index.html 기반으로 PropMap 템플릿 생성 - 제거/수정 방식"""
import re

src = '/home/webapp/goldenrabbit/frontend/public/index.html'
dst = '/home/webapp/goldenrabbit/frontend/public/propmap/_template/index.html'

with open(src, 'r', encoding='utf-8') as f:
    c = f.read()

# === 1. <head> 수정 ===

# title
c = c.replace('<title>금토끼부동산중개</title>', '<title>{{AGENT_NAME}} 매물지도</title>')

# meta description
c = c.replace('content="수익형 부동산 전문 금토끼부동산중개 - 서울 동작구 사당동"',
              'content="{{AGENT_NAME}} 매물지도"')

# canonical URL 제거 (agent별로 다르니)
c = re.sub(r'<link rel="canonical"[^>]*>\n?', '', c)

# OG tags - 템플릿화
c = c.replace('content="https://goldenrabbit.biz/"', 'content="https://propnet.kr/propmap/{{AGENT_SLUG}}/"')
c = c.replace('content="금토끼부동산중개 - 수익형 부동산 전문"', 'content="{{AGENT_NAME}} 매물지도"')
c = c.replace('content="수익형 부동산 전문 금토끼부동산중개 - 서울 동작구 사당동"', 'content="{{AGENT_NAME}} 매물지도"')
c = c.replace('content="금토끼부동산중개"', 'content="{{AGENT_NAME}}"')

# naver verification 제거
c = re.sub(r'<meta name="naver-site-verification"[^>]*>\s*\n?', '', c)

# Schema.org 전체 제거 (agent별로 다르니)
c = re.sub(r'<script type="application/ld\+json">.*?</script>\s*\n?', '', c, flags=re.DOTALL)

# manifest 제거
c = re.sub(r'<link rel="manifest"[^>]*>\s*\n?', '', c)

# fb:app_id 제거
c = re.sub(r'<meta property="fb:app_id"[^>]*>\s*\n?', '', c)

# twitter card 제거
c = re.sub(r'<!-- Twitter Card -->.*?<meta name="twitter:image"[^>]*>\s*\n?', '', c, flags=re.DOTALL)

# favicon - 공통 PropNet 로고로
c = c.replace('href="/images/favicon.png"', 'href="/images/propnet-favicon.png"')

# === 2. 헤더 수정 - 메뉴버튼/회원가입 제거, 사무소명 템플릿화 ===
old_header = '''    <!-- 헤더 -->
    <header class="sticky top-0 z-50 bg-white/90 backdrop-blur-xl border-b border-slate-200/60">
        <div class="flex items-center justify-between px-5 h-16 max-w-lg md:max-w-3xl mx-auto w-full">
            <button id="menuButton" class="p-2 -ml-2 hover:bg-slate-100 rounded-full transition-colors">
                <span class="material-symbols-outlined text-slate-700">menu</span>
            </button>
            <div class="flex items-center gap-2">
                <img src="/images/logo_goldenrabbit.jpg" alt="금토끼부동산 로고" class="w-8 h-8 rounded-lg object-cover">
                <h1 class="text-xl font-bold tracking-tight text-slate-900">금토끼부동산</h1>
            </div>
            <a href="/register/" class="text-sm font-semibold text-primary hover:text-primary/80 transition-colors whitespace-nowrap">회원가입</a>
        </div>
    </header>'''

new_header = '''    <!-- 헤더 -->
    <header class="sticky top-0 z-50 bg-white/90 backdrop-blur-xl border-b border-slate-200/60">
        <div class="flex items-center justify-between px-5 h-16 max-w-lg md:max-w-3xl mx-auto w-full">
            <div class="flex items-center gap-2">
                <h1 class="text-xl font-bold tracking-tight text-slate-900">{{AGENT_NAME}}</h1>
                <span class="text-xs text-slate-400 font-medium">매물지도</span>
            </div>
            <a href="https://propnet.kr" target="_blank" class="text-xs text-slate-400 hover:text-primary transition-colors">PropNet</a>
        </div>
    </header>'''
c = c.replace(old_header, new_header)

# === 3. 히어로 섹션 제거 ===
c = re.sub(r'        <!-- 히어로 섹션 -->.*?</section>\s*\n', '', c, flags=re.DOTALL, count=1)

# === 4. 추천매물 제거 (매물검색/매물지도 버튼은 유지) ===
# "추천 매물" div 부터 닫는 </div>까지 제거
old_recommend = '''            <!-- 하단: 추천 매물 -->
            <div>
                <p class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">추천 매물</p>
                <div class="flex gap-2">
                    <button class="category-chip flex-1 flex items-center justify-center px-3 py-2.5 rounded-xl text-[13px] font-semibold transition-all bg-white text-slate-600 border border-slate-200 hover:border-primary hover:text-primary" data-filter="70" data-category="재건축용 토지">
                        재건축용 토지
                    </button>
                    <button class="category-chip flex-1 flex items-center justify-center px-3 py-2.5 rounded-xl text-[13px] font-semibold transition-all bg-white text-slate-600 border border-slate-200 hover:border-primary hover:text-primary" data-filter="71" data-category="고수익률 건물">
                        고수익률 건물
                    </button>
                    <button class="category-chip flex-1 flex items-center justify-center px-3 py-2.5 rounded-xl text-[13px] font-semibold transition-all bg-white text-slate-600 border border-slate-200 hover:border-primary hover:text-primary" data-filter="72" data-category="저가단독주택">
                        저가단독주택
                    </button>
                </div>
            </div>'''
c = c.replace(old_recommend, '')

# === 5. 매물지도 iframe src 수정 ===
# map.html -> 기존 PropMap 지도 (map-data API에 agent_slug 포함)
c = c.replace('src="map.html"', 'src="/propmap/{{AGENT_SLUG}}/map.html"')

# === 6. 푸터 수정 ===
old_footer = '''        <!-- 푸터 -->
        <footer class="px-5 py-8 border-t border-slate-200/60">
            <div class="max-w-lg md:max-w-3xl mx-auto text-center">
                <p class="text-xs text-slate-400 leading-relaxed">
                    &copy; 2024 금토끼부동산중개. All rights reserved.<br>
                    대표: 전창성 | 사업자등록번호: 520-41-01170<br>
                    중개사무소등록번호: 11590-2024-00048
                </p>
            </div>
        </footer>'''

new_footer = '''        <!-- 푸터 -->
        <footer class="px-5 py-8 border-t border-slate-200/60">
            <div class="max-w-lg md:max-w-3xl mx-auto text-center">
                <p class="text-xs text-slate-400 leading-relaxed">
                    &copy; {{COPYRIGHT_YEAR}} {{AGENT_NAME}}. All rights reserved.
                </p>
                <p class="text-[10px] text-slate-300 mt-2">
                    Designed &amp; Built by <a href="https://propnet.kr" target="_blank" class="hover:text-primary transition-colors">PropNet</a>
                </p>
            </div>
        </footer>'''
c = c.replace(old_footer, new_footer)

# === 7. 사이드 메뉴 전체 제거 ===
# overlay + sideMenu
c = re.sub(r'    <!-- 사이드 메뉴 오버레이 -->.*?</div>\s*\n\s*<!-- 사이드 메뉴 -->\s*\n.*?</div>\s*\n\s*</div>\s*\n', '', c, flags=re.DOTALL)

# === 8. 상담 모달 전체 제거 ===
c = re.sub(r'    <!-- 상담 모달 -->.*?</div>\s*\n\s*</div>\s*\n', '', c, flags=re.DOTALL)

# === 9. 개인정보 동의 모달 제거 (있다면) ===
# 보통 JS에서 처리되므로 남겨둬도 무방

# === 10. API 엔드포인트에 agent_slug 추가 ===
# category-properties
c = c.replace("'/propsheet/api/propsheet/category-properties",
              "'/propsheet/api/propsheet/category-properties?agent_slug={{AGENT_SLUG}}&")
# property-detail
c = c.replace("'/propsheet/api/propsheet/property-detail/",
              "'/propsheet/api/propsheet/property-detail/")
# search-map
c = c.replace("'/propsheet/api/propsheet/search-map'",
              "'/propsheet/api/propsheet/search-map?agent_slug={{AGENT_SLUG}}'")

# === 11. 금토끼 하드코딩 텍스트 치환 ===
c = c.replace('금토끼부동산중개', '{{AGENT_NAME}}')
c = c.replace('금토끼부동산', '{{AGENT_NAME}}')
# 광고 텍스트의 금토끼부동산은 제거
c = c.replace("'⚛ 금토끼부동산은'", "'⚛ '")

# === 12. 맨위로 버튼 유지, 배경 장식 유지 ===

# === 13. JS에서 메뉴 관련 코드 제거 (에러 방지) ===
# menuButton, closeMenu 이벤트 리스너가 없는 요소 참조 시 에러 발생
# 안전하게 null check 추가
c = c.replace("document.getElementById('menuButton')",
              "(document.getElementById('menuButton') || {addEventListener:function(){}})")
c = c.replace("document.getElementById('closeMenu')",
              "(document.getElementById('closeMenu') || {addEventListener:function(){}})")
c = c.replace("document.getElementById('overlay')",
              "(document.getElementById('overlay') || {classList:{add:function(){},remove:function(){}}})")
c = c.replace("document.getElementById('sideMenu')",
              "(document.getElementById('sideMenu') || {classList:{add:function(){},remove:function(){}}})")

# 상담 모달 관련 함수 - 빈 함수로
c = c.replace('function openConsultModal(', 'function openConsultModal_disabled(')

# 로고 이미지 제거 (없으므로 무시)
c = c.replace('src="/images/logo_goldenrabbit.jpg"', 'src="/images/propnet-logo.png"')

with open(dst, 'w', encoding='utf-8') as f:
    f.write(c)
print(f'템플릿 생성 완료: {dst}')
print(f'크기: {len(c)} bytes, {c.count(chr(10))} lines')

# goldenrabbit 인스턴스 재생성
print('\ngoldenrabbit 재생성...')
import sys, os
sys.path.insert(0, '/home/webapp/goldenrabbit/backend/property-manager')
os.environ.setdefault('DB_HOST', '127.0.0.1')
from dotenv import load_dotenv
load_dotenv('/home/webapp/goldenrabbit/backend/.env')
from services.propmap_setup_service import create_propmap_page
result = create_propmap_page('goldenrabbit', '금토끼부동산', '11590-2024-00048', '서울특별시 동작구 사당로16나길 55')
print(f'결과: {result}')

# map.html도 propmap/goldenrabbit/ 에 복사 (iframe 참조용)
import shutil
map_src = '/home/webapp/goldenrabbit/frontend/public/propmap/_template/map.html'
map_dst = '/home/webapp/goldenrabbit/frontend/public/propmap/goldenrabbit/map.html'
if os.path.exists(map_src):
    shutil.copy2(map_src, map_dst)
    print(f'map.html 복사: {map_dst}')
else:
    # 기존 map.html 템플릿이 없으면 원본에서 복사
    orig_map = '/home/webapp/goldenrabbit/frontend/public/map.html'
    if os.path.exists(orig_map):
        shutil.copy2(orig_map, map_dst)
        print(f'원본 map.html 복사: {map_dst}')

print('\n완료!')

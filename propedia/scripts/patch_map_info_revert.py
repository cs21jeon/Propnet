path = '/home/webapp/goldenrabbit/frontend/public/app/search-map.html'
with open(path, 'r') as f:
    content = f.read()

# Revert compact info card back to original
old = """                <div class="px-4 py-3 space-y-2">
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-primary text-xl flex-shrink-0">location_on</span>
                        <div class="flex-1 min-w-0">
                            <p id="infoAddress" class="text-sm font-semibold text-slate-900 dark:text-white leading-snug truncate">주소를 불러오는 중...</p>
                            <p id="infoRoadAddress" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 hidden truncate"></p>
                            <p id="infoMainPurpose" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 hidden"></p>
                        </div>
                    </div>
                    <div class="flex gap-2">
                        <button onclick="closeSearchInfo()" class="flex-1 h-9 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg font-semibold text-sm hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                            취소
                        </button>
                        <button onclick="searchSelected()" class="flex-[2] h-9 bg-primary text-white rounded-lg font-bold text-sm shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all active:scale-[0.98]">
                            조회하기
                        </button>
                    </div>
                </div>"""

new = """                <div class="p-5 space-y-3">
                    <div class="flex items-start gap-3">
                        <span class="material-symbols-outlined text-primary text-2xl flex-shrink-0 mt-0.5">location_on</span>
                        <div class="flex-1 min-w-0">
                            <p id="infoAddress" class="text-sm font-semibold text-slate-900 dark:text-white leading-snug">주소를 불러오는 중...</p>
                            <p id="infoRoadAddress" class="text-xs text-slate-500 dark:text-slate-400 mt-1 hidden"></p>
                            <p id="infoMainPurpose" class="text-xs text-slate-500 dark:text-slate-400 mt-1 hidden"></p>
                        </div>
                    </div>
                    <div class="flex gap-2 pt-2">
                        <button onclick="closeSearchInfo()" class="flex-1 h-11 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl font-semibold text-sm hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                            취소
                        </button>
                        <button onclick="searchSelected()" class="flex-[2] h-11 bg-primary text-white rounded-xl font-bold text-sm shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all active:scale-[0.98]">
                            조회하기
                        </button>
                    </div>
                </div>"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print('SUCCESS: info card reverted')
else:
    print('Already original or pattern not found')

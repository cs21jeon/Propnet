#!/usr/bin/env python3
"""Patch index.html: Add property type tabs and dynamic search fields"""

FILE = '/home/webapp/goldenrabbit/frontend/public/index.html'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open(FILE + '.bak', 'w', encoding='utf-8') as f:
    f.write(content)

# 1. Replace the search form section
old_form = '''<h3 class="text-base font-bold mb-4">조건 검색</h3>
                <form id="conditionSearchForm" class="space-y-3">
                    <!-- 매가 -->
                    <div class="flex items-center gap-2">
                        <label class="text-sm font-medium text-slate-600 w-16 shrink-0">매가</label>
                        <input type="number" id="searchPrice" placeholder="만원" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                        <select id="searchPriceCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                            <option value="below">이하</option>
                            <option value="above">이상</option>
                        </select>
                    </div>
                    <!-- 실투자금 -->
                    <div class="flex items-center gap-2">
                        <label class="text-sm font-medium text-slate-600 w-16 shrink-0">실투자금</label>
                        <input type="number" id="searchInvestment" placeholder="만원" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                        <select id="searchInvestmentCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                            <option value="below">이하</option>
                            <option value="above">이상</option>
                        </select>
                    </div>
                    <!-- 수익률 -->
                    <div class="flex items-center gap-2">
                        <label class="text-sm font-medium text-slate-600 w-16 shrink-0">수익률</label>
                        <input type="number" id="searchYield" placeholder="%" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                        <select id="searchYieldCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                            <option value="above">이상</option>
                            <option value="below">이하</option>
                        </select>
                    </div>
                    <!-- 토지면적 -->
                    <div class="flex items-center gap-2">
                        <label class="text-sm font-medium text-slate-600 w-16 shrink-0">토지면적</label>
                        <input type="number" id="searchArea" placeholder="㎡" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                        <select id="searchAreaCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                            <option value="above">이상</option>
                            <option value="below">이하</option>
                        </select>
                    </div>
                    <!-- 버튼 -->
                    <div class="flex gap-2 pt-1">
                        <button type="submit" class="flex-1 py-2.5 bg-primary text-white rounded-xl font-bold text-sm hover:bg-primary/90 transition-colors shadow-sm">
                            <span class="material-symbols-outlined text-[16px] align-middle mr-1">search</span>검색
                        </button>
                        <button type="button" id="searchReset" class="px-4 py-2.5 bg-slate-100 text-slate-600 rounded-xl font-semibold text-sm hover:bg-slate-200 transition-colors">초기화</button>
                    </div>
                </form>'''

new_form = '''<h3 class="text-base font-bold mb-4">조건 검색</h3>
                <!-- 부동산유형 선택 탭 -->
                <div class="flex gap-1 mb-4" id="searchTypeTabs">
                    <button type="button" class="search-type-tab active flex-1 py-2 rounded-lg text-sm font-semibold transition-all" data-type="danil" style="background:#1D4ED8;color:white;">단일</button>
                    <button type="button" class="search-type-tab flex-1 py-2 rounded-lg text-sm font-semibold transition-all bg-slate-100 text-slate-500" data-type="jibhap">집합</button>
                    <button type="button" class="search-type-tab flex-1 py-2 rounded-lg text-sm font-semibold transition-all bg-slate-100 text-slate-500" data-type="bubun">부분</button>
                </div>
                <form id="conditionSearchForm" class="space-y-3">
                    <input type="hidden" id="searchPropertyType" value="danil">
                    <!-- 단일부동산 필드 -->
                    <div id="searchFields-danil">
                        <div class="flex items-center gap-2 mb-3">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">매가</label>
                            <input type="number" id="searchPrice" placeholder="만원" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchPriceCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="below">이하</option>
                                <option value="above">이상</option>
                            </select>
                        </div>
                        <div class="flex items-center gap-2 mb-3">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">실투자금</label>
                            <input type="number" id="searchInvestment" placeholder="만원" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchInvestmentCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="below">이하</option>
                                <option value="above">이상</option>
                            </select>
                        </div>
                        <div class="flex items-center gap-2 mb-3">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">수익률</label>
                            <input type="number" id="searchYield" placeholder="%" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchYieldCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="above">이상</option>
                                <option value="below">이하</option>
                            </select>
                        </div>
                        <div class="flex items-center gap-2">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">토지면적</label>
                            <input type="number" id="searchArea" placeholder="㎡" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchAreaCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="above">이상</option>
                                <option value="below">이하</option>
                            </select>
                        </div>
                    </div>
                    <!-- 집합부동산 필드 -->
                    <div id="searchFields-jibhap" class="hidden">
                        <div class="flex items-center gap-2 mb-3">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">매가</label>
                            <input type="number" id="searchJPrice" placeholder="만원" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchJPriceCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="below">이하</option>
                                <option value="above">이상</option>
                            </select>
                        </div>
                        <div class="flex items-center gap-2 mb-3">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">보증금</label>
                            <input type="number" id="searchJDeposit" placeholder="만원" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchJDepositCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="below">이하</option>
                                <option value="above">이상</option>
                            </select>
                        </div>
                        <div class="flex items-center gap-2 mb-3">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">월세</label>
                            <input type="number" id="searchJRent" placeholder="만원" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchJRentCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="below">이하</option>
                                <option value="above">이상</option>
                            </select>
                        </div>
                        <div class="flex items-center gap-2 mb-3">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">전용면적</label>
                            <input type="number" id="searchJArea" placeholder="㎡" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchJAreaCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="above">이상</option>
                                <option value="below">이하</option>
                            </select>
                        </div>
                        <div class="flex items-center gap-2">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">방</label>
                            <input type="number" id="searchJRooms" placeholder="개" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchJRoomsCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="above">이상</option>
                                <option value="below">이하</option>
                            </select>
                        </div>
                    </div>
                    <!-- 부분부동산 필드 -->
                    <div id="searchFields-bubun" class="hidden">
                        <div class="flex items-center gap-2 mb-3">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">보증금</label>
                            <input type="number" id="searchBDeposit" placeholder="만원" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchBDepositCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="below">이하</option>
                                <option value="above">이상</option>
                            </select>
                        </div>
                        <div class="flex items-center gap-2 mb-3">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">월세</label>
                            <input type="number" id="searchBRent" placeholder="만원" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchBRentCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="below">이하</option>
                                <option value="above">이상</option>
                            </select>
                        </div>
                        <div class="flex items-center gap-2 mb-3">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">전용면적</label>
                            <input type="number" id="searchBArea" placeholder="㎡" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchBAreaCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="above">이상</option>
                                <option value="below">이하</option>
                            </select>
                        </div>
                        <div class="flex items-center gap-2 mb-3">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">물건종류</label>
                            <select id="searchBSubtype" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary outline-none">
                                <option value="">전체</option>
                                <option value="다가구주택">다가구주택</option>
                                <option value="단독주택">단독주택</option>
                                <option value="상가">상가</option>
                                <option value="사무실">사무실</option>
                                <option value="원룸">원룸</option>
                            </select>
                        </div>
                        <div class="flex items-center gap-2">
                            <label class="text-sm font-medium text-slate-600 w-16 shrink-0">방</label>
                            <input type="number" id="searchBRooms" placeholder="개" class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none">
                            <select id="searchBRoomsCond" class="w-16 rounded-lg border border-slate-200 px-2 py-2 text-sm focus:border-primary outline-none">
                                <option value="above">이상</option>
                                <option value="below">이하</option>
                            </select>
                        </div>
                    </div>
                    <!-- 버튼 -->
                    <div class="flex gap-2 pt-1">
                        <button type="submit" class="flex-1 py-2.5 bg-primary text-white rounded-xl font-bold text-sm hover:bg-primary/90 transition-colors shadow-sm">
                            <span class="material-symbols-outlined text-[16px] align-middle mr-1">search</span>검색
                        </button>
                        <button type="button" id="searchReset" class="px-4 py-2.5 bg-slate-100 text-slate-600 rounded-xl font-semibold text-sm hover:bg-slate-200 transition-colors">초기화</button>
                    </div>
                </form>'''

if old_form in content:
    content = content.replace(old_form, new_form)
    print("STEP 1: Search form replaced")
else:
    print("ERROR: Could not find search form")
    import sys
    sys.exit(1)

# 2. Replace the search submit handler
old_handler = """    document.getElementById('conditionSearchForm').addEventListener('submit', function(e) {
        e.preventDefault();

        var searchData = {
            price_value: document.getElementById('searchPrice').value,
            price_condition: document.getElementById('searchPrice').value ? document.getElementById('searchPriceCond').value : 'all',
            investment_value: document.getElementById('searchInvestment').value,
            investment_condition: document.getElementById('searchInvestment').value ? document.getElementById('searchInvestmentCond').value : 'all',
            yield_value: document.getElementById('searchYield').value,
            yield_condition: document.getElementById('searchYield').value ? document.getElementById('searchYieldCond').value : 'all',
            area_value: document.getElementById('searchArea').value,
            area_condition: document.getElementById('searchArea').value ? document.getElementById('searchAreaCond').value : 'all',
            approval_date: '',
            approval_condition: 'all'
        };"""

new_handler = """    // 부동산유형 탭 전환
    var typeColors = {danil: '#1D4ED8', jibhap: '#15803D', bubun: '#EA580C'};
    document.querySelectorAll('.search-type-tab').forEach(function(tab) {
        tab.addEventListener('click', function() {
            var type = this.getAttribute('data-type');
            document.getElementById('searchPropertyType').value = type;
            document.querySelectorAll('.search-type-tab').forEach(function(t) {
                t.classList.remove('active');
                t.style.background = '#f1f5f9';
                t.style.color = '#64748b';
            });
            this.classList.add('active');
            this.style.background = typeColors[type];
            this.style.color = 'white';
            document.getElementById('searchFields-danil').classList.add('hidden');
            document.getElementById('searchFields-jibhap').classList.add('hidden');
            document.getElementById('searchFields-bubun').classList.add('hidden');
            document.getElementById('searchFields-' + type).classList.remove('hidden');
        });
    });

    document.getElementById('conditionSearchForm').addEventListener('submit', function(e) {
        e.preventDefault();

        var propertyType = document.getElementById('searchPropertyType').value;
        var searchData = { property_type: propertyType };

        if (propertyType === 'danil') {
            searchData.price_value = document.getElementById('searchPrice').value;
            searchData.price_condition = document.getElementById('searchPrice').value ? document.getElementById('searchPriceCond').value : 'all';
            searchData.investment_value = document.getElementById('searchInvestment').value;
            searchData.investment_condition = document.getElementById('searchInvestment').value ? document.getElementById('searchInvestmentCond').value : 'all';
            searchData.yield_value = document.getElementById('searchYield').value;
            searchData.yield_condition = document.getElementById('searchYield').value ? document.getElementById('searchYieldCond').value : 'all';
            searchData.area_value = document.getElementById('searchArea').value;
            searchData.area_condition = document.getElementById('searchArea').value ? document.getElementById('searchAreaCond').value : 'all';
        } else if (propertyType === 'jibhap') {
            searchData.price_value = document.getElementById('searchJPrice').value;
            searchData.price_condition = document.getElementById('searchJPrice').value ? document.getElementById('searchJPriceCond').value : 'all';
            searchData.deposit_value = document.getElementById('searchJDeposit').value;
            searchData.deposit_condition = document.getElementById('searchJDeposit').value ? document.getElementById('searchJDepositCond').value : 'all';
            searchData.rent_value = document.getElementById('searchJRent').value;
            searchData.rent_condition = document.getElementById('searchJRent').value ? document.getElementById('searchJRentCond').value : 'all';
            searchData.exclusive_area_value = document.getElementById('searchJArea').value;
            searchData.exclusive_area_condition = document.getElementById('searchJArea').value ? document.getElementById('searchJAreaCond').value : 'all';
            searchData.rooms_value = document.getElementById('searchJRooms').value;
            searchData.rooms_condition = document.getElementById('searchJRooms').value ? document.getElementById('searchJRoomsCond').value : 'all';
        } else {
            searchData.deposit_value = document.getElementById('searchBDeposit').value;
            searchData.deposit_condition = document.getElementById('searchBDeposit').value ? document.getElementById('searchBDepositCond').value : 'all';
            searchData.rent_value = document.getElementById('searchBRent').value;
            searchData.rent_condition = document.getElementById('searchBRent').value ? document.getElementById('searchBRentCond').value : 'all';
            searchData.exclusive_area_value = document.getElementById('searchBArea').value;
            searchData.exclusive_area_condition = document.getElementById('searchBArea').value ? document.getElementById('searchBAreaCond').value : 'all';
            searchData.subtype_value = document.getElementById('searchBSubtype').value;
            searchData.rooms_value = document.getElementById('searchBRooms').value;
            searchData.rooms_condition = document.getElementById('searchBRooms').value ? document.getElementById('searchBRoomsCond').value : 'all';
        }"""

if old_handler in content:
    content = content.replace(old_handler, new_handler)
    print("STEP 2: Search handler replaced")
else:
    print("ERROR: Could not find search handler")
    import sys
    sys.exit(1)

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: index.html patched")

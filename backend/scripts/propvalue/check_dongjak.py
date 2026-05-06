#!/usr/bin/env python3
"""동작구 도시개발계획포털 데이터 확인"""
import urllib.request, ssl, re
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "http://ud.dongjak.go.kr/www/bizSrch/develop/list.do?mid=935"
req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
resp = urllib.request.urlopen(req, timeout=15, context=ctx)
html = resp.read().decode("utf-8", errors="replace")
soup = BeautifulSoup(html, "html.parser")

print(f"Page length: {len(html)}")
tables = soup.find_all("table")
print(f"Tables: {len(tables)}")

# 사당 관련
for el in soup.find_all(["td","li","a","span","div","p"]):
    t = el.get_text(strip=True)
    if ("사당" in t or "연번" in t) and len(t) < 100:
        print(f"  {t[:80]}")

# 테이블 구조
for ti, t in enumerate(tables[:3]):
    ths = [th.get_text(strip=True) for th in t.find_all("th")]
    print(f"\nTable {ti} headers: {ths[:10]}")
    for tr in t.find_all("tr")[:5]:
        tds = [td.get_text(strip=True)[:25] for td in tr.find_all("td")]
        if tds:
            print(f"  {tds}")

# JS에서 API URL 찾기
urls = re.findall(r'["\']([^"\']*(?:bizSrch|list|map|polygon|json|api)[^"\']*)["\']', html)
for u in set(urls):
    if len(u) > 5:
        print(f"  JS URL: {u}")

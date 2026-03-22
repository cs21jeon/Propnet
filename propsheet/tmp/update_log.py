#!/usr/bin/env python3
"""Update development log with 2026-03-19 progress"""
path = '/home/webapp/goldenrabbit/docs/property-manager-development-log.md'
with open(path, 'r') as f:
    content = f.read()

# Remove any corrupted append from failed heredoc
marker = '### 2026-03-19'
if marker in content:
    # Find the marker and remove everything from there that's corrupted
    idx = content.index(marker)
    # Go back to find the newline before it
    content = content[:idx].rstrip() + '\n'

update = """
### 2026-03-19

- **광고(자동완성) 트리거 시스템 구축**
  - 단일부동산: format_ad_text() - 홍보문구(최상단) + 매매금액, 임대내역, 건물현황, 면적(평 환산), 층수(지하/지상 파싱), 주차, 승강기, 방향, 주용도, 용도지역, 위반건축물, 사용승인일
  - 부분부동산: format_ad_text_partial() - 임대 전용. 홍보문구, 물건종류, 임대종류, 보증금/월세(전세/월세 자동분기), 관리비, 전용면적, 방/화장실, 방향, 위반건축물, 입주가능일
  - 집합부동산: format_ad_text_multi() - 매매/전세/월세 3종 분기, 관리비(매매 제외), 전용/공급/대지면적(평 환산), 총세대수, 총주차, 승강기, 사용승인일, 용도지역, 공동주택공시가격, 방/화장실, 방향, 입주가능일
  - 각 DB별 field_definitions에 formula 타입 및 수식 등록
  - psycopg2 % 이스케이프 수정 (formula SQL 내 LIKE 패턴의 % -> %% 변환)
- **부분부동산 테이블 구조 변경**
  - 삭제: 실투자금, 실투자금(융자포함), 융자제외수익률(%), 융자포함수익률, 층(복사본)
  - 추가: 호수, 물건종류, 호실, 전용면적, 관리비, 방, 화, 입주가능일
- **상세보기 줄바꿈 표시**: white-space: pre-line 적용으로 텍스트 내 줄바꿈이 실제 줄바꿈으로 표시
- **파일/이미지 업로드 수정**: attachment 필드 클릭 시 텍스트 편집 모드 진입 방지 (click handler에 attachment 타입 체크 추가)
- **브로커 카드 전화번호**: tel: 링크를 클릭시 클립보드 복사로 변경. 점선 밑줄 표시. 피드백 메시지 "클립보드에 복사됨"
- **체크박스/상세보기 컬럼 순서**: 체크박스를 상세보기 왼쪽으로 이동, sticky 위치 및 CSS 조정

---

**마지막 업데이트**: 2026-03-19
**작성자**: Claude (AI Assistant)
**프로젝트**: GoldenRabbit PropSheet
"""

# Update the last update date at the bottom
if '**마지막 업데이트**: 2026-02-03' in content:
    content = content.replace('**마지막 업데이트**: 2026-02-03', '')
    content = content.replace('**작성자**: Claude (AI Assistant)\n**프로젝트**: GoldenRabbit Property Manager', '')

# Also update the 향후 개선 사항 section - mark completed items
content = content.replace('- [ ] 다중 선택 (Multi-select) 필드 타입', '- [x] 다중 선택 (Multi-select) 필드 타입')
content = content.replace('- [ ] 첨부파일 (Attachment) 필드 타입', '- [x] 첨부파일 (Attachment) 필드 타입')
content = content.replace('- [ ] 뷰 (View) 저장 기능', '- [x] 뷰 (View) 저장 기능')
content = content.replace('- [ ] 공유 및 권한 관리', '- [x] 공유 및 권한 관리 (admin/agent/subagent/user)')
content = content.replace('- [ ] 일괄 수정 (Bulk edit)', '- [x] 일괄 수정 (Bulk edit) - 행/열 선택 후 삭제/복제')

content = content.rstrip() + '\n' + update

with open(path, 'w') as f:
    f.write(content)

print('Updated development log')

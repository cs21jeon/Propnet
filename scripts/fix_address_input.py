#!/usr/bin/env python3
"""주소 입력을 다음 우편번호 서비스로 교체"""

path = '/home/webapp/goldenrabbit/backend/property-manager/templates/register/step4_agent.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 기존 주소 입력 필드 교체
old_address = '''        <div class="form-group">
            <label for="address">사무소 주소 <span class="required">*</span></label>
            <small style="color:#666;font-size:12px;">매물지도의 기준 위치로 사용됩니다. 정확한 도로명주소를 입력해주세요.</small>
            <input type="text" id="address" name="address"
                   placeholder="서울시 강남구 테헤란로 123" required
                   x-model="address">
        </div>'''

new_address = '''        <div class="form-group">
            <label for="address">사무소 주소 <span class="required">*</span></label>
            <small style="color:#666;font-size:12px;">매물지도의 기준 위치로 사용됩니다.</small>
            <div style="display:flex;gap:8px;margin-top:4px;">
                <input type="text" id="address" name="address"
                       placeholder="주소 검색 버튼을 클릭하세요" required readonly
                       x-model="address"
                       style="flex:1;background:#f5f5f5;cursor:pointer;"
                       @click="openPostcode()">
                <button type="button" @click="openPostcode()"
                        style="padding:8px 16px;background:#2962FF;color:white;border:none;border-radius:6px;font-size:13px;cursor:pointer;white-space:nowrap;">
                    주소 검색
                </button>
            </div>
            <input type="text" id="addressDetail" name="address_detail"
                   placeholder="상세주소 (동/호수 등)"
                   x-model="addressDetail"
                   style="margin-top:6px;">
        </div>'''

if old_address in content:
    content = content.replace(old_address, new_address)
    print('[1] 주소 입력 필드 교체 완료')
else:
    print('[1] 패턴 불일치')

# 2. Alpine.js data에 addressDetail 추가 + openPostcode 함수 추가
# 기존 script 블록 끝에 추가
old_script_end = '''    };
}
</script>
{% endblock %}'''

new_script_end = '''    };
}
</script>
<script src="//t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js"></script>
<script>
function openPostcode() {
    new daum.Postcode({
        oncomplete: function(data) {
            var addr = data.roadAddress || data.jibunAddress;
            // Alpine.js 데이터 업데이트
            var el = document.querySelector('[x-data]');
            if (el && el.__x) {
                el.__x.$data.address = addr;
            } else {
                // Alpine v3
                document.getElementById('address').value = addr;
                document.getElementById('address').dispatchEvent(new Event('input'));
            }
            // 상세주소로 포커스
            var detail = document.getElementById('addressDetail');
            if (detail) detail.focus();
        }
    }).open();
}
</script>
{% endblock %}'''

if old_script_end in content:
    content = content.replace(old_script_end, new_script_end)
    print('[2] Postcode 스크립트 추가 완료')
else:
    print('[2] 스크립트 패턴 불일치')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('완료')

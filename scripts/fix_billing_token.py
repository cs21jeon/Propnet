"""billing 토큰 저장을 sessionStorage['billing_token'] → localStorage['proptalk_token']으로 통일"""

# 1. login.html
path1 = '/home/webapp/goldenrabbit/chat_stt/server/templates/billing/login.html'
with open(path1, 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace("sessionStorage.setItem('billing_token', data.token)", "localStorage.setItem('proptalk_token', data.token)")
with open(path1, 'w', encoding='utf-8') as f:
    f.write(c)
print('login.html updated')

# 2. base.html
path2 = '/home/webapp/goldenrabbit/chat_stt/server/templates/billing/base.html'
with open(path2, 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace("sessionStorage.getItem('billing_token')", "localStorage.getItem('proptalk_token')")
c = c.replace("sessionStorage.setItem('billing_token', token)", "localStorage.setItem('proptalk_token', token)")
c = c.replace("sessionStorage.removeItem('billing_token')", "localStorage.removeItem('proptalk_token')")
with open(path2, 'w', encoding='utf-8') as f:
    f.write(c)
print('base.html updated')

#!/bin/bash
# 통합 관리자 대시보드 전체 배포 스크립트
# 서버에서 실행: bash deploy_admin_all.sh
#
# 실행 전: scp로 스크립트 파일들을 서버에 업로드
# scp propedia/scripts/deploy_admin_dashboard.py root@175.119.224.71:/tmp/
# scp propedia/scripts/patch_proppedia_app_admin.py root@175.119.224.71:/tmp/
# scp propedia/scripts/patch_nginx_admin.py root@175.119.224.71:/tmp/
# scp propedia/scripts/setup_admin_db.sql root@175.119.224.71:/tmp/
# scp propedia/scripts/deploy_admin_all.sh root@175.119.224.71:/tmp/
# ssh root@175.119.224.71 'cd /tmp && bash deploy_admin_all.sh'

set -e

echo "=== Phase 11: 통합 관리자 대시보드 배포 ==="
echo ""

# 1. DB 스키마
echo "[1/5] DB 스키마 업데이트..."
cd /home/webapp/goldenrabbit
sudo -u postgres psql goldenrabbit_db < /tmp/setup_admin_db.sql
echo "  Done"

# 2. 대시보드 파일 생성
echo "[2/5] 대시보드 파일 생성..."
cd /home/webapp/goldenrabbit/backend
source venv/bin/activate
python3 /tmp/deploy_admin_dashboard.py
echo "  Done"

# 3. proppedia app.py 패치
echo "[3/5] proppedia app.py 패치..."
python3 /tmp/patch_proppedia_app_admin.py
echo "  Done"

# 4. Nginx 설정
echo "[4/5] Nginx 설정 업데이트..."
python3 /tmp/patch_nginx_admin.py
sudo nginx -t && sudo systemctl reload nginx
echo "  Done"

# 5. 서비스 재시작
echo "[5/5] proppedia 서비스 재시작..."
sudo systemctl restart proppedia
sleep 2
sudo systemctl status proppedia --no-pager | head -5
echo "  Done"

echo ""
echo "=== 배포 완료 ==="
echo "대시보드: https://goldenrabbit.biz/admin/"
echo "로그 확인: journalctl -u proppedia -f"

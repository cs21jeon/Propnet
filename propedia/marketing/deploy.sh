#!/bin/bash
# 부동산백과 마케팅 파일 배포 스크립트 (Bash)
# 사용법: bash deploy.sh

SERVER="root@175.119.224.71"
REMOTE_PATH="/home/webapp/goldenrabbit/frontend/public"
PROJECT_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"

echo "=== 부동산백과 마케팅 파일 배포 ==="

# 1. 서버 디렉토리 생성
echo ""
echo "[1/5] 서버 디렉토리 생성..."
ssh $SERVER "mkdir -p $REMOTE_PATH/proppedia/screenshots && mkdir -p $REMOTE_PATH/proppedia-app"

# 2. 랜딩 페이지 파일 업로드
echo ""
echo "[2/5] 랜딩 페이지 업로드..."
scp "$PROJECT_ROOT/marketing/proppedia/index.html" "$SERVER:$REMOTE_PATH/proppedia/"
scp "$PROJECT_ROOT/marketing/robots.txt" "$SERVER:$REMOTE_PATH/"
scp "$PROJECT_ROOT/marketing/sitemap.xml" "$SERVER:$REMOTE_PATH/"

# 3. 스크린샷 업로드
echo ""
echo "[3/5] 스크린샷 업로드..."
scp "$PROJECT_ROOT/screenshots/"*.png "$SERVER:$REMOTE_PATH/proppedia/screenshots/"

# 4. 로고 및 OG 이미지 업로드
echo ""
echo "[4/5] 로고 및 이미지 업로드..."
scp "$PROJECT_ROOT/assets/images/proppedia_logo.png" "$SERVER:$REMOTE_PATH/proppedia/logo.png"
scp "$PROJECT_ROOT/screenshots/Feature Graphic_proppedia.png" "$SERVER:$REMOTE_PATH/proppedia/og-image.png"
scp "$PROJECT_ROOT/screenshots/icon_512x512.png" "$SERVER:$REMOTE_PATH/proppedia/apple-touch-icon.png"

# 5. Flutter Web 앱 업로드 (빌드 폴더가 있는 경우)
if [ -d "$PROJECT_ROOT/build/web" ]; then
    echo ""
    echo "[5/5] Flutter Web 앱 업로드..."
    scp -r "$PROJECT_ROOT/build/web/"* "$SERVER:$REMOTE_PATH/proppedia-app/"
else
    echo ""
    echo "[5/5] Flutter Web 빌드 폴더가 없습니다."
    echo "flutter build web --base-href '/proppedia-app/' 먼저 실행하세요."
fi

# 6. 권한 설정
echo ""
echo "권한 설정 중..."
ssh $SERVER "chown -R www-data:www-data $REMOTE_PATH/proppedia $REMOTE_PATH/proppedia-app && chmod -R 755 $REMOTE_PATH/proppedia $REMOTE_PATH/proppedia-app"

echo ""
echo "=== 배포 완료 ==="
echo "확인할 URL:"
echo "  - https://goldenrabbit.biz/proppedia/"
echo "  - https://goldenrabbit.biz/proppedia-app/"
echo "  - https://goldenrabbit.biz/robots.txt"
echo "  - https://goldenrabbit.biz/sitemap.xml"

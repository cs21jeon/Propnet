# 부동산백과 마케팅 파일 배포 스크립트 (PowerShell)
# 사용법: .\deploy.ps1

$SERVER = "root@175.119.224.71"
$REMOTE_PATH = "/home/webapp/goldenrabbit/frontend/public"
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot

Write-Host "=== 부동산백과 마케팅 파일 배포 ===" -ForegroundColor Cyan

# 1. 서버 디렉토리 생성
Write-Host "`n[1/5] 서버 디렉토리 생성..." -ForegroundColor Yellow
ssh $SERVER "mkdir -p $REMOTE_PATH/proppedia/screenshots && mkdir -p $REMOTE_PATH/proppedia-app"

# 2. 랜딩 페이지 파일 업로드
Write-Host "`n[2/5] 랜딩 페이지 업로드..." -ForegroundColor Yellow
scp "$PROJECT_ROOT\marketing\proppedia\index.html" "${SERVER}:$REMOTE_PATH/proppedia/"
scp "$PROJECT_ROOT\marketing\robots.txt" "${SERVER}:$REMOTE_PATH/"
scp "$PROJECT_ROOT\marketing\sitemap.xml" "${SERVER}:$REMOTE_PATH/"

# 3. 스크린샷 업로드
Write-Host "`n[3/5] 스크린샷 업로드..." -ForegroundColor Yellow
scp "$PROJECT_ROOT\screenshots\01_home.png" "${SERVER}:$REMOTE_PATH/proppedia/screenshots/"
scp "$PROJECT_ROOT\screenshots\02_road_search.png" "${SERVER}:$REMOTE_PATH/proppedia/screenshots/"
scp "$PROJECT_ROOT\screenshots\03_jibun_search.png" "${SERVER}:$REMOTE_PATH/proppedia/screenshots/"
scp "$PROJECT_ROOT\screenshots\04_result_1.png" "${SERVER}:$REMOTE_PATH/proppedia/screenshots/"
scp "$PROJECT_ROOT\screenshots\05_result_2.png" "${SERVER}:$REMOTE_PATH/proppedia/screenshots/"
scp "$PROJECT_ROOT\screenshots\06_map_search.png" "${SERVER}:$REMOTE_PATH/proppedia/screenshots/"
scp "$PROJECT_ROOT\screenshots\07_history.png" "${SERVER}:$REMOTE_PATH/proppedia/screenshots/"
scp "$PROJECT_ROOT\screenshots\08_favorites.png" "${SERVER}:$REMOTE_PATH/proppedia/screenshots/"

# 4. 로고 및 OG 이미지 업로드
Write-Host "`n[4/5] 로고 및 이미지 업로드..." -ForegroundColor Yellow
scp "$PROJECT_ROOT\assets\images\proppedia_logo.png" "${SERVER}:$REMOTE_PATH/proppedia/logo.png"
scp "$PROJECT_ROOT\screenshots\Feature Graphic_proppedia.png" "${SERVER}:$REMOTE_PATH/proppedia/og-image.png"
scp "$PROJECT_ROOT\screenshots\icon_512x512.png" "${SERVER}:$REMOTE_PATH/proppedia/apple-touch-icon.png"

# 5. Flutter Web 앱 업로드 (빌드 폴더가 있는 경우)
if (Test-Path "$PROJECT_ROOT\build\web") {
    Write-Host "`n[5/5] Flutter Web 앱 업로드..." -ForegroundColor Yellow
    scp -r "$PROJECT_ROOT\build\web\*" "${SERVER}:$REMOTE_PATH/proppedia-app/"
} else {
    Write-Host "`n[5/5] Flutter Web 빌드 폴더가 없습니다. flutter build web --base-href '/proppedia-app/' 먼저 실행하세요." -ForegroundColor Red
}

# 6. 권한 설정
Write-Host "`n권한 설정 중..." -ForegroundColor Yellow
ssh $SERVER "chown -R www-data:www-data $REMOTE_PATH/proppedia $REMOTE_PATH/proppedia-app && chmod -R 755 $REMOTE_PATH/proppedia $REMOTE_PATH/proppedia-app"

Write-Host "`n=== 배포 완료 ===" -ForegroundColor Green
Write-Host "확인할 URL:"
Write-Host "  - https://goldenrabbit.biz/proppedia/" -ForegroundColor Cyan
Write-Host "  - https://goldenrabbit.biz/proppedia-app/" -ForegroundColor Cyan
Write-Host "  - https://goldenrabbit.biz/robots.txt" -ForegroundColor Cyan
Write-Host "  - https://goldenrabbit.biz/sitemap.xml" -ForegroundColor Cyan

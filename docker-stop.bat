@echo off
REM LiveTranslate v2.0 - Docker Stop Script for Windows
REM 停止脚本 / Stop Script / 停止スクリプト

echo ====================================
echo LiveTranslate v2.0 Docker Stop
echo ====================================
echo.

echo Stopping Docker containers...
echo 停止 Docker 容器...
echo Dockerコンテナを停止中...
echo.

docker-compose stop

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Containers stopped successfully.
    echo [成功] 容器已成功停止。
    echo [成功] コンテナが正常に停止しました。
    echo.
) else (
    echo.
    echo [ERROR] Failed to stop containers.
    echo [错误] 停止容器失败。
    echo [エラー] コンテナの停止に失敗しました。
    echo.
)

pause

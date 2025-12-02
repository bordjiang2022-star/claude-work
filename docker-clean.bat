@echo off
REM LiveTranslate v2.0 - Docker Clean Script for Windows
REM 清理脚本 / Clean Script / クリーンスクリプト

echo ====================================
echo LiveTranslate v2.0 Docker Clean
echo ====================================
echo.
echo WARNING: This will remove all containers, volumes, and images!
echo 警告：这将删除所有容器、卷和镜像！
echo 警告：これによりすべてのコンテナ、ボリューム、イメージが削除されます！
echo.
echo Your database and user data will be deleted!
echo 您的数据库和用户数据将被删除！
echo データベースとユーザーデータが削除されます！
echo.

set /p confirm="Are you sure? Type YES to confirm / 确认请输入 YES / 確認するにはYESと入力: "

if /i "%confirm%" neq "YES" (
    echo.
    echo Cancelled / 已取消 / キャンセルされました
    pause
    exit /b 0
)

echo.
echo Removing containers, volumes, and images...
echo 删除容器、卷和镜像...
echo コンテナ、ボリューム、イメージを削除中...
echo.

docker-compose down -v --rmi all

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Cleanup completed.
    echo [成功] 清理完成。
    echo [成功] クリーンアップ完了。
    echo.
) else (
    echo.
    echo [ERROR] Cleanup failed.
    echo [错误] 清理失败。
    echo [エラー] クリーンアップ失敗。
    echo.
)

pause

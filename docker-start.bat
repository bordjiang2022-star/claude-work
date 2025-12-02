@echo off
REM LiveTranslate v2.0 - Docker Startup Script for Windows
REM 启动脚本 / Startup Script / 起動スクリプト

echo ====================================
echo LiveTranslate v2.0 Docker Startup
echo ====================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    echo [错误] Docker 未运行。请先启动 Docker Desktop。
    echo [エラー] Dockerが実行されていません。Docker Desktopを先に起動してください。
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found. Creating from template...
    echo [警告] 未找到 .env 文件。从模板创建中...
    echo [警告] .envファイルが見つかりません。テンプレートから作成中...
    copy .env.docker.example .env
    echo.
    echo [ACTION REQUIRED] Please edit .env file and add your DASHSCOPE_API_KEY
    echo [需要操作] 请编辑 .env 文件并添加您的 DASHSCOPE_API_KEY
    echo [アクション必要] .envファイルを編集してDASHSCOPE_API_KEYを追加してください
    echo.
    pause
)

echo Starting Docker containers...
echo 启动 Docker 容器...
echo Dockerコンテナを起動中...
echo.

docker-compose up -d

if %errorlevel% equ 0 (
    echo.
    echo ====================================
    echo [SUCCESS] LiveTranslate is running!
    echo [成功] LiveTranslate 正在运行！
    echo [成功] LiveTranslateが実行中です！
    echo ====================================
    echo.
    echo Frontend: http://localhost:3000
    echo Backend API: http://localhost:8000
    echo API Docs: http://localhost:8000/docs
    echo.
    echo To view logs / 查看日志 / ログを表示:
    echo   docker-compose logs -f
    echo.
    echo To stop / 停止 / 停止:
    echo   docker-compose stop
    echo.
) else (
    echo.
    echo [ERROR] Failed to start containers. Check logs with:
    echo [错误] 启动容器失败。查看日志：
    echo [エラー] コンテナの起動に失敗しました。ログを確認：
    echo   docker-compose logs
    echo.
)

pause

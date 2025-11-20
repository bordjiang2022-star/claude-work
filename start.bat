@echo off
REM LiveTranslate 启动脚本 (Windows)
REM 此脚本将启动后端服务器和前端开发服务器

echo ========================================
echo  LiveTranslate v2.0 启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.11+
    pause
    exit /b 1
)

REM 检查Node.js是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Node.js，请先安装Node.js 18+
    pause
    exit /b 1
)

REM 检查环境变量
if not defined DASHSCOPE_API_KEY (
    echo [警告] 未设置 DASHSCOPE_API_KEY 环境变量
    echo 请先设置：setx DASHSCOPE_API_KEY "your-api-key"
    echo 或创建 .env 文件
    pause
)

REM 安装后端依赖
echo [1/4] 安装后端Python依赖...
cd backend
if not exist venv (
    echo 创建虚拟环境...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..

REM 安装前端依赖
echo [2/4] 安装前端Node.js依赖...
cd frontend
if not exist node_modules (
    npm install
)
cd ..

REM 启动后端服务器（后台）
echo [3/4] 启动后端服务器...
cd backend
start "LiveTranslate Backend" cmd /k "venv\Scripts\activate.bat && python main.py"
cd ..

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端开发服务器
echo [4/4] 启动前端开发服务器...
cd frontend
start "LiveTranslate Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo  启动完成！
echo  后端: http://localhost:8000
echo  前端: http://localhost:3000
echo ========================================
echo.
echo 按任意键退出此窗口（服务器将在后台继续运行）
pause

#!/bin/bash
# LiveTranslate 启动脚本 (Linux/Mac)
# 此脚本将启动后端服务器和前端开发服务器

echo "========================================"
echo " LiveTranslate v2.0 启动脚本"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3，请先安装Python 3.11+"
    exit 1
fi

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "[错误] 未检测到Node.js，请先安装Node.js 18+"
    exit 1
fi

# 检查环境变量
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "[警告] 未设置 DASHSCOPE_API_KEY 环境变量"
    echo "请先设置：export DASHSCOPE_API_KEY='your-api-key'"
    echo "或创建 .env 文件"
fi

# 安装后端依赖
echo "[1/4] 安装后端Python依赖..."
cd backend
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 安装前端依赖
echo "[2/4] 安装前端Node.js依赖..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

# 启动后端服务器（后台）
echo "[3/4] 启动后端服务器..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端开发服务器
echo "[4/4] 启动前端开发服务器..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo " 启动完成！"
echo " 后端: http://localhost:8000"
echo " 前端: http://localhost:3000"
echo " 后端PID: $BACKEND_PID"
echo " 前端PID: $FRONTEND_PID"
echo "========================================"
echo ""
echo "按 Ctrl+C 停止服务器"

# 等待用户中断
wait

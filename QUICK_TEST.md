# LiveTranslate v2.0 - 快速测试指南

## 🚀 5分钟快速测试流程

### 前提检查

```bash
# 1. 检查Python版本
python --version
# 应该显示: Python 3.11.x 或更高

# 2. 检查Node.js版本
node --version
# 应该显示: v18.x.x 或更高

# 3. 检查项目文件
ls -la
# 应该看到 backend/, frontend/, start.bat/start.sh 等文件
```

### 步骤1: 设置API密钥 (30秒)

**Windows:**
```cmd
setx DASHSCOPE_API_KEY "sk-your-actual-api-key-here"
# 然后重启命令行窗口
```

**Linux/Mac:**
```bash
export DASHSCOPE_API_KEY="sk-your-actual-api-key-here"
```

### 步骤2: 安装依赖 (2-3分钟)

#### 方式A: 使用启动脚本（推荐）

**Windows:**
```cmd
# 直接双击 start.bat
# 或在命令行运行:
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

脚本会自动：
- ✅ 创建Python虚拟环境
- ✅ 安装后端依赖
- ✅ 安装前端依赖
- ✅ 启动后端服务器
- ✅ 启动前端开发服务器

#### 方式B: 手动安装

**后端依赖:**
```bash
cd backend
python -m venv venv

# Windows激活
venv\Scripts\activate

# Linux/Mac激活
source venv/bin/activate

pip install -r requirements.txt
cd ..
```

**前端依赖:**
```bash
cd frontend
npm install
cd ..
```

### 步骤3: 启动服务 (30秒)

如果使用启动脚本，服务会自动启动。

如果手动安装，需要开两个终端：

**终端1 - 后端:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
```

看到以下输出表示成功：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
[Server] Database initialized
```

**终端2 - 前端:**
```bash
cd frontend
npm run dev
```

看到以下输出表示成功：
```
  VITE v5.0.5  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### 步骤4: 测试应用 (2分钟)

#### 4.1 打开浏览器

访问: **http://localhost:3000**

应该看到登录页面。

#### 4.2 注册账号

1. 点击"注册"或"Register"链接
2. 输入邮箱: `test@example.com`
3. 输入密码: `password123`
4. 确认密码: `password123`
5. 点击"Register"按钮

#### 4.3 登录系统

注册成功后会自动登录，进入主翻译界面。

#### 4.4 测试基本功能

**测试界面语言切换:**
- 点击右上角的语言选择器
- 切换到"简体中文"
- 界面应该变成中文

**测试语言选择:**
- 在"目标语言"下拉菜单中选择"日语"
- 在"TTS音色"下拉菜单中选择"Cherry (女声)"

**测试翻译控制:**
- 点击"开始"按钮
- 按钮应该变灰（禁用状态）
- "停止"按钮应该变为可用状态
- 看到"翻译中"的状态指示

- 点击"停止"按钮
- "开始"按钮恢复可用

**测试转录面板:**
- 应该看到两个面板："原文 (Source)"和"译文 (Translation)"
- 每个面板显示字符计数
- 有"清空"和"下载"按钮

#### 4.5 测试多语言界面

依次测试所有语言：
- English ✅
- 简体中文 ✅
- 繁體中文 ✅
- 日本語 ✅
- 한국어 ✅

### 步骤5: 验证后端API (可选)

打开新的浏览器标签，访问后端API文档：

**Swagger UI:** http://localhost:8000/docs

应该看到所有API接口：
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me
- POST /api/translation/start
- POST /api/translation/stop
- GET /api/translation/status
- GET /api/sessions
- GET /api/statistics
- WebSocket /ws

### ✅ 测试检查清单

- [ ] Python 3.11+ 已安装
- [ ] Node.js 18+ 已安装
- [ ] API密钥已设置
- [ ] 后端依赖已安装
- [ ] 前端依赖已安装
- [ ] 后端服务器成功启动 (localhost:8000)
- [ ] 前端服务器成功启动 (localhost:3000)
- [ ] 可以打开登录页面
- [ ] 可以注册新账号
- [ ] 可以登录系统
- [ ] 可以切换界面语言
- [ ] 可以选择目标语言
- [ ] 可以选择TTS音色
- [ ] START/STOP按钮正常工作
- [ ] 转录面板正常显示
- [ ] 后端API文档可访问

### 🎯 快速功能测试

如果所有基础测试通过，可以进行以下功能测试：

#### 测试1: 完整翻译流程（需要VB-Cable）

```
1. 确保已安装VB-Cable虚拟音频驱动
2. 点击START开始翻译
3. 播放音频或对着麦克风说话
4. 观察原文和译文实时显示
5. 点击STOP停止翻译
```

#### 测试2: 文件下载

```
1. 进行一些翻译操作
2. 点击"下载原文"按钮
3. 应该下载 transcript_source_X.txt 文件
4. 点击"下载译文"按钮
5. 应该下载 transcript_translation_X.txt 文件
```

#### 测试3: 清空功能

```
1. 点击"清空"按钮
2. 转录面板应该清空
3. 字符计数归零
```

## 🐛 常见问题快速解决

### 问题1: 后端启动失败

```bash
# 检查端口是否被占用
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# 如果被占用，杀死进程或修改端口
```

### 问题2: 前端启动失败

```bash
# 删除node_modules重新安装
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### 问题3: API密钥未设置

```bash
# 检查环境变量
echo $DASHSCOPE_API_KEY  # Linux/Mac
echo %DASHSCOPE_API_KEY%  # Windows

# 如果为空，重新设置
```

### 问题4: 数据库错误

```bash
# 删除数据库文件重新初始化
rm backend/livetranslate.db
# 然后重启后端
```

### 问题5: WebSocket连接失败

```bash
# 检查后端是否正在运行
curl http://localhost:8000/health

# 应该返回: {"status":"healthy"}
```

## 📊 性能测试（可选）

### 测试并发用户

```bash
# 使用Apache Bench测试
ab -n 100 -c 10 http://localhost:8000/health

# 或使用wrk
wrk -t4 -c10 -d10s http://localhost:8000/health
```

### 测试API响应时间

```bash
# 测试登录接口
time curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

## 📝 测试报告模板

```
测试日期: _____________
测试人员: _____________
系统环境: _____________

[ ] 所有基础功能测试通过
[ ] 多语言切换正常
[ ] 翻译功能正常
[ ] 文件下载正常
[ ] 性能可接受

问题记录:
1. _____________
2. _____________
3. _____________

建议:
1. _____________
2. _____________
3. _____________
```

---

**测试完成后，您就可以开始正式使用LiveTranslate进行实时翻译了！🎉**

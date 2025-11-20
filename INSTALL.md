# LiveTranslate Web应用 - 安装与使用指南

## 概述

LiveTranslate v2.0 是一个基于Web的实时语音翻译应用，支持多语言翻译和TTS语音合成。

### 技术栈

**后端:**
- Python 3.11+
- FastAPI (Web框架)
- SQLAlchemy (数据库ORM)
- WebSocket (实时通信)
- 阿里云通义千问 API

**前端:**
- React 18
- TypeScript
- Tailwind CSS
- i18next (多语言支持)
- Zustand (状态管理)

## 系统要求

### 必需软件

1. **Python 3.11 或更高版本**
   - Windows: 从 [python.org](https://www.python.org/downloads/) 下载
   - Mac: `brew install python3`
   - Linux: `sudo apt install python3.11`

2. **Node.js 18 或更高版本**
   - 从 [nodejs.org](https://nodejs.org/) 下载
   - 或使用 nvm: `nvm install 18`

3. **VB-Cable 虚拟音频驱动（Windows）**
   - 从 [VB-Audio](https://vb-audio.com/Cable/) 下载安装
   - 用于捕获系统音频进行翻译

4. **阿里云 DashScope API 密钥**
   - 注册账号: [DashScope](https://dashscope.aliyun.com/)
   - 获取 API Key

## 安装步骤

### 方法1: 使用启动脚本（推荐）

#### Windows用户

1. 克隆或下载项目到本地

2. 设置环境变量（永久设置）:
   ```cmd
   setx DASHSCOPE_API_KEY "sk-your-api-key-here"
   ```
   然后重启命令行窗口

3. 双击运行 `start.bat`

4. 浏览器将自动打开 http://localhost:3000

#### Linux/Mac用户

1. 克隆或下载项目到本地

2. 设置环境变量:
   ```bash
   export DASHSCOPE_API_KEY="sk-your-api-key-here"
   ```
   建议添加到 `~/.bashrc` 或 `~/.zshrc`

3. 赋予脚本执行权限:
   ```bash
   chmod +x start.sh
   ```

4. 运行启动脚本:
   ```bash
   ./start.sh
   ```

5. 打开浏览器访问 http://localhost:3000

### 方法2: 手动安装

#### 后端安装

1. 进入backend目录:
   ```bash
   cd backend
   ```

2. 创建虚拟环境:
   ```bash
   python -m venv venv

   # Windows激活
   venv\Scripts\activate

   # Linux/Mac激活
   source venv/bin/activate
   ```

3. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

4. 启动后端服务器:
   ```bash
   python main.py
   ```

#### 前端安装

1. 新开终端，进入frontend目录:
   ```bash
   cd frontend
   ```

2. 安装依赖:
   ```bash
   npm install
   ```

3. 启动开发服务器:
   ```bash
   npm run dev
   ```

4. 打开浏览器访问 http://localhost:3000

## 使用指南

### 首次使用

1. **注册账号**
   - 打开应用后，点击"注册"
   - 输入邮箱和密码
   - 点击"Register"按钮

2. **登录系统**
   - 使用注册的邮箱和密码登录
   - 登录成功后进入主翻译界面

### 开始翻译

1. **选择翻译语言**
   - 在"目标语言"下拉菜单中选择要翻译到的语言
   - 支持: 英语、中文、日语、韩语等

2. **选择TTS音色**
   - 在"TTS音色"下拉菜单中选择喜欢的声音
   - 支持多种男声和女声选项

3. **点击START按钮**
   - 系统会自动切换音频设备到VB-Cable
   - 开始采集音频并实时翻译
   - 原文和译文会实时显示在下方

4. **点击STOP按钮**
   - 停止翻译
   - 系统会自动恢复音频设备到扬声器

### 查看和导出转录文本

- **实时查看**: 翻译过程中，原文和译文会实时显示，带时间戳
- **清空转录**: 点击"清空"按钮清除当前转录
- **下载原文**: 点击"下载原文"按钮下载原文文本文件
- **下载译文**: 点击"下载译文"按钮下载译文文本文件

### 切换界面语言

点击右上角的语言选择器，可以切换界面语言：
- English (英语)
- 简体中文
- 繁體中文
- 日本語 (日语)
- 한국어 (韩语)

## 功能特性

### ✅ 已实现功能

- 用户注册和登录系统
- 多语言界面支持（5种语言）
- 实时语音翻译（支持中日英韩等语言）
- TTS语音合成播放
- 实时转录文本显示（带时间戳）
- 原文和译文对照显示
- 转录文本下载功能
- 自动音频设备切换
- 会话历史记录
- 使用统计功能

### 📊 数据统计

应用会自动记录以下统计数据：
- 总翻译会话数
- 总使用时长
- 总翻译字符数
- 会话历史记录

## 故障排除

### 问题1: 无法启动后端服务器

**解决方案:**
- 检查Python版本: `python --version` (需要3.11+)
- 检查是否设置了DASHSCOPE_API_KEY环境变量
- 查看是否有端口冲突（默认8000端口）

### 问题2: 无法启动前端

**解决方案:**
- 检查Node.js版本: `node --version` (需要18+)
- 删除`node_modules`文件夹，重新运行`npm install`
- 查看是否有端口冲突（默认3000端口）

### 问题3: 音频设备切换失败

**解决方案:**
- 确认已安装VB-Cable虚拟音频驱动
- 检查`tools/nircmd.exe`文件是否存在
- 在Windows声音设置中确认VB-Cable设备已启用

### 问题4: WebSocket连接失败

**解决方案:**
- 确认后端服务器正在运行
- 检查浏览器控制台是否有错误信息
- 尝试刷新页面

### 问题5: 翻译无响应

**解决方案:**
- 检查API密钥是否正确
- 确认网络连接正常
- 查看后端控制台的错误日志

## 开发模式

### 后端开发

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发

```bash
cd frontend
npm run dev
```

### 构建生产版本

```bash
cd frontend
npm run build
```

## 环境变量说明

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| DASHSCOPE_API_KEY | 阿里云API密钥 | 是 | - |
| SECRET_KEY | JWT密钥 | 否 | 默认值 |
| DATABASE_URL | 数据库连接 | 否 | sqlite:///./livetranslate.db |
| BACKEND_HOST | 后端主机 | 否 | 0.0.0.0 |
| BACKEND_PORT | 后端端口 | 否 | 8000 |
| FRONTEND_PORT | 前端端口 | 否 | 3000 |

## 目录结构

```
livetranslate_web/
├── backend/                 # 后端代码
│   ├── main.py             # FastAPI入口
│   ├── auth.py             # 用户认证
│   ├── database.py         # 数据库模型
│   ├── translation_service.py  # 翻译服务
│   ├── audio_control.py    # 音频控制
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # React组件
│   │   ├── pages/          # 页面组件
│   │   ├── hooks/          # 状态管理
│   │   ├── services/       # API服务
│   │   ├── i18n/           # 多语言配置
│   │   └── types/          # TypeScript类型
│   ├── package.json        # Node.js依赖
│   └── vite.config.ts      # Vite配置
├── tools/                  # 工具文件
│   └── nircmd.exe          # 音频切换工具
├── livetranslate_client.py # 翻译客户端核心
├── main.py                 # 原命令行版本
├── start.bat               # Windows启动脚本
├── start.sh                # Linux/Mac启动脚本
├── .env.example            # 环境变量示例
└── README.md               # 项目说明

```

## 支持和反馈

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- Email: support@livetranslate.com

## 许可证

MIT License

---

**享受实时翻译的便利！🌐**

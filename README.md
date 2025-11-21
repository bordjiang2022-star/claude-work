# LiveTranslate v2.0 - 实时语音翻译Web应用

## 🌟 项目简介

LiveTranslate 是一个基于Web的实时语音翻译应用，支持多语言翻译和TTS语音合成。用户可以通过浏览器进行实时语音翻译，支持中文、英语、日语、韩语等多种语言。

### ✨ 主要功能

- 🌐 **多语言支持**: 界面支持5种语言（英/简中/繁中/日/韩）
- 🎤 **实时语音翻译**: 支持中日英韩等多种语言互译
- 🔊 **TTS语音播放**: 多种音色选择，自然流畅
- 📝 **实时转录显示**: 原文与译文对照，带时间戳
- 💾 **文本下载**: 支持导出原文和译文文本文件
- 👤 **用户系统**: 邮箱注册登录，会话历史记录
- 📊 **使用统计**: 记录翻译时长和字符数
- 🎧 **自动音频切换**: Windows平台自动切换音频设备

## 🏗️ 技术架构

### 后端技术栈
- Python 3.11 (推荐使用3.11.9，已充分测试)
- FastAPI (Web框架)
- SQLAlchemy (数据库ORM)
- WebSocket (实时通信)
- 阿里云通义千问 API (qwen3-livetranslate-flash-realtime)

### 前端技术栈
- React 18 + TypeScript
- Tailwind CSS (UI框架)
- i18next (国际化)
- Zustand (状态管理)
- Vite (构建工具)

### 系统架构

```
┌─────────────────┐         WebSocket          ┌─────────────────┐
│   Web Frontend  │ ◄─────────────────────────► │  FastAPI Server │
│   (React App)   │                             │                 │
│  localhost:3000 │         HTTP API            │  localhost:8000 │
└─────────────────┘ ◄─────────────────────────► └─────────────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │ Translation     │
                                                 │ Service         │
                                                 │ (Qwen API)      │
                                                 └─────────────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  Audio Control  │
                                                 │  (VB-Cable)     │
                                                 └─────────────────┘
```

## 📁 目录结构

```
livetranslate_web/
├── backend/                    # 后端代码
│   ├── main.py                # FastAPI入口
│   ├── auth.py                # 用户认证
│   ├── database.py            # 数据库模型
│   ├── translation_service.py # 翻译服务
│   ├── audio_control.py       # 音频控制
│   └── requirements.txt       # Python依赖
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── components/        # React组件
│   │   ├── pages/             # 页面组件
│   │   ├── hooks/             # 状态管理
│   │   ├── services/          # API服务
│   │   ├── i18n/              # 多语言配置
│   │   └── types/             # TypeScript类型
│   ├── package.json           # Node.js依赖
│   └── vite.config.ts         # Vite配置
├── tools/                     # 工具文件
│   └── nircmd.exe             # 音频切换工具(Windows)
├── livetranslate_client.py    # 翻译客户端核心
├── main.py                    # 原命令行版本
├── start.bat                  # Windows启动脚本
├── start.sh                   # Linux/Mac启动脚本
├── .env.example               # 环境变量示例
├── INSTALL.md                 # 详细安装指南
└── README.md                  # 本文件
```

## 🚀 快速开始

### 前提条件

1. **Python 3.11** - [下载地址](https://www.python.org/downloads/release/python-3119/) ⚠️ **请使用3.11版本，已充分测试**
2. **Node.js 18+** - [下载地址](https://nodejs.org/)
3. **VB-Cable** (Windows) - [下载地址](https://vb-audio.com/Cable/)
4. **阿里云API密钥** - [获取地址](https://dashscope.aliyun.com/)

### 方法1：使用启动脚本（推荐）

#### Windows用户

1. 设置环境变量：
   ```cmd
   setx DASHSCOPE_API_KEY "sk-your-api-key-here"
   ```
   重启命令行窗口

2. 双击运行 `start.bat`

3. 浏览器访问 http://localhost:3000

#### Linux/Mac用户

1. 设置环境变量：
   ```bash
   export DASHSCOPE_API_KEY="sk-your-api-key-here"
   ```

2. 运行启动脚本：
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

3. 浏览器访问 http://localhost:3000

### 方法2：手动启动

#### 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### 前端启动

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:3000

详细安装说明请参考 [INSTALL.md](INSTALL.md)

## 📖 使用说明

### 首次使用

1. **注册账号**
   - 打开 http://localhost:3000
   - 点击"注册"按钮
   - 输入邮箱和密码

2. **登录系统**
   - 使用注册的邮箱和密码登录

### 开始翻译

1. **选择语言和音色**
   - 在"目标语言"下拉菜单选择要翻译到的语言
   - 在"TTS音色"下拉菜单选择喜欢的声音

2. **启动翻译**
   - 点击 **START** 按钮
   - 系统自动切换音频设备到VB-Cable
   - 开始实时翻译

3. **查看结果**
   - 原文和译文实时显示在下方
   - 每条记录带有时间戳

4. **停止翻译**
   - 点击 **STOP** 按钮
   - 系统自动恢复音频设备

5. **导出文本**
   - 点击"下载原文"或"下载译文"按钮
   - 保存转录文本文件

### 界面语言切换

点击右上角的语言选择器，可以切换界面语言：
- English
- 简体中文
- 繁體中文
- 日本語
- 한국어

## 📸 界面截图

参考UI如用户提供的截图，包含：
- 顶部导航栏（Logo、语言切换、用户信息）
- 语言和音色选择
- START/STOP控制按钮
- 实时转录双栏显示（原文/译文）
- 下载和清空按钮

## 🔧 常见问题

### 问题1: 后端启动失败
**解决方案:** 检查Python版本和API密钥设置

### 问题2: 音频设备切换失败
**解决方案:** 确认已安装VB-Cable驱动

### 问题3: WebSocket连接失败
**解决方案:** 确认后端服务正在运行

详细故障排除请参考 [INSTALL.md](INSTALL.md)

## 🛠️ 技术特色

- **响应式设计**: 适配桌面和移动设备
- **实时通信**: WebSocket低延迟数据传输
- **类型安全**: TypeScript全栈类型检查
- **现代化UI**: Tailwind CSS样式系统
- **国际化**: 完整的多语言支持
- **状态管理**: Zustand轻量级状态管理

## 📝 开发计划

- [x] 用户认证系统
- [x] 实时翻译功能
- [x] 多语言界面
- [x] 文本下载功能
- [x] 使用统计
- [ ] 会话历史查看
- [ ] 用户设置页面
- [ ] 音频录制功能
- [ ] 云端部署

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**享受实时翻译的便利！🌐✨**

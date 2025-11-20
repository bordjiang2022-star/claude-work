# LiveTranslate 本地客户端 v2.0

## 架构说明

这是一个**混合架构**的实时翻译系统：

```
本地客户端 (用户电脑) ←→ WebSocket ←→ 云端服务器
```

### 本地客户端功能
- 音频设备自动切换 (nircmd.exe)
- 音频采集 (麦克风/VB-Cable)
- TTS播放 (扬声器)
- Web界面 (localhost:3000)
- 实时文本显示和下载

### 云端服务器功能
- 用户认证和会话管理
- 调用阿里云翻译API
- 多用户并发支持

## 目录结构

```
livetranslate_client/
├── README.md                 # 本文件
├── requirements.txt          # Python依赖
├── config.yaml              # 配置文件
├── local_client.py          # 主程序入口
├── audio_switcher.py        # 音频设备切换模块
├── audio_handler.py         # 音频采集和播放
├── websocket_client.py      # WebSocket通信
├── tools/
│   └── nircmd.exe          # 音频切换工具
└── web_ui/
    ├── index.html          # Web界面
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## 快速开始

### 方法1：使用启动脚本（推荐）

Windows用户双击运行：
```
start.bat
```

### 方法2：手动启动

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **设置API密钥**
```bash
# Windows
set DASHSCOPE_API_KEY=sk-your-api-key-here

# Linux/Mac
export DASHSCOPE_API_KEY=sk-your-api-key-here
```

3. **运行测试（可选）**
测试阿里云翻译功能：
```bash
python test_alibaba_client.py
```

4. **启动服务**
```bash
python local_client.py
```

5. **打开浏览器**
```
http://localhost:3000
```

## 测试步骤

### 1. 测试阿里云翻译（不涉及音频）
```bash
python test_alibaba_client.py
```
这将测试：
- 连接到阿里云API
- 文本翻译功能
- TTS语音合成

### 2. 测试音频设备切换
```bash
python audio_switcher.py
```
这将测试：
- nircmd.exe是否正常工作
- 音频设备切换功能

### 3. 测试音频采集和播放
```bash
python audio_handler.py
```
这将测试：
- VB-Cable音频采集
- 扬声器音频播放
- 5秒回声测试

### 4. 完整系统测试
```bash
python local_client.py
```
打开浏览器测试完整功能。

## 使用流程

1. 登录账号
2. 选择翻译语言和音色
3. 点击 START
   - 自动切换系统音频到VB-Cable
   - 开始采集音频并发送到云端
   - 接收翻译结果和TTS
4. 实时查看原文和译文
5. 点击 STOP
   - 停止翻译
   - 自动恢复系统音频到扬声器
6. 下载转录文本

## 下一步

阶段2将部署云端服务器，提供多用户支持。

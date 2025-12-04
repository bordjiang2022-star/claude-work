# -*- coding: utf-8 -*-
# server_docker.py — LiveTranslate Web (Docker/Linux 版本)
# 移除了 Windows 特有的音频设备切换功能，适合容器化部署

import os
import asyncio
import contextlib
import json
import base64
import time
from typing import Optional, List

import uvicorn
from fastapi import FastAPI, HTTPException, Body, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import websockets
from websockets.asyncio.client import connect as ws_connect

# ---------------------------
# Web App & CORS
# ---------------------------
app = FastAPI(title="LiveTranslate Docker Edition")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Session State
# ---------------------------
class SessionState:
    def __init__(self):
        self.running: bool = False
        self.src_buf: List[str] = []
        self.dst_buf: List[str] = []
        self.ws_connection = None
        self.worker: Optional[asyncio.Task] = None

    def reset(self):
        self.src_buf.clear()
        self.dst_buf.clear()

SESS = SessionState()

# ---------------------------
# Alibaba Realtime Client (简化版)
# ---------------------------
class RealtimeTranslateClient:
    """简化的翻译客户端，不包含音频设备操作"""

    def __init__(self, api_key: str, target_language: str = "en", voice: str = "Cherry"):
        self.api_key = api_key
        self.target_language = target_language
        self.voice = voice
        self.api_url = (
            "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime"
            "?model=qwen3-livetranslate-flash-realtime"
        )
        self.ws = None
        self.is_connected = False

    async def connect(self):
        headers = [("Authorization", f"Bearer {self.api_key}")]
        try:
            self.ws = await ws_connect(self.api_url, additional_headers=headers)
            self.is_connected = True
            print(f"[WS] Connected to translation service")
            await self.configure_session()
        except Exception as e:
            self.is_connected = False
            raise RuntimeError(f"连接失败: {e}") from e

    async def configure_session(self):
        session = {
            "modalities": ["text", "audio"],
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "translation": {"language": self.target_language},
            "voice": self.voice,
        }
        event = {
            "event_id": f"event_{int(time.time() * 1000)}",
            "type": "session.update",
            "session": session,
        }
        await self.ws.send(json.dumps(event))

    async def send_audio(self, audio_data: bytes):
        if not self.is_connected or not self.ws:
            return
        event = {
            "event_id": f"event_{int(time.time() * 1000)}",
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(audio_data).decode(),
        }
        await self.ws.send(json.dumps(event))

    async def receive_messages(self, on_text=None, on_audio=None):
        try:
            async for message in self.ws:
                event = json.loads(message)
                et = event.get("type")

                if et == "error":
                    print(f"[ERROR] {message}")
                    continue

                if et == "response.audio_transcript.delta":
                    text = event.get("transcript", "")
                    if text and on_text:
                        on_text(text, delta=True)

                elif et == "response.audio.delta":
                    b64 = event.get("delta")
                    if b64 and on_audio:
                        on_audio(base64.b64decode(b64))

                elif et in ("response.audio_transcript.done", "response.text.done"):
                    text = event.get("transcript") or event.get("text") or ""
                    if text and on_text:
                        on_text(text, delta=False)

        except websockets.exceptions.ConnectionClosed as e:
            print(f"[WS] Closed: {e}")
            self.is_connected = False
        except Exception as e:
            print(f"[WS] Error: {e}")
            self.is_connected = False

    async def close(self):
        self.is_connected = False
        if self.ws:
            with contextlib.suppress(Exception):
                await self.ws.close()

# ---------------------------
# API Endpoints
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse("""
<!doctype html>
<html><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LiveTranslate (Docker Edition)</title>
<style>
:root {
  --bg-dark: #0f172a;
  --bg-card: #1e293b;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --success: #22c55e;
  --border: #334155;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: var(--bg-dark);
  color: var(--text-primary);
  min-height: 100vh;
  padding: 20px;
}
.container { max-width: 1200px; margin: 0 auto; }
h1 { font-size: 24px; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
h1 .badge {
  font-size: 12px;
  background: var(--accent);
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: normal;
}

.card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid var(--border);
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.status-indicator {
  width: 12px; height: 12px;
  border-radius: 50%;
  background: #64748b;
}
.status-indicator.running { background: var(--success); animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.form-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group label { font-size: 12px; color: var(--text-secondary); }

input, select {
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-dark);
  color: var(--text-primary);
  font-size: 14px;
}
input:focus, select:focus { outline: none; border-color: var(--accent); }

button {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-primary { background: var(--accent); color: white; }
.btn-primary:hover { background: var(--accent-hover); }
.btn-secondary { background: #475569; color: white; }
.btn-secondary:hover { background: #64748b; }
.btn-success { background: var(--success); color: white; }
.btn-danger { background: #ef4444; color: white; }

.transcript-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 768px) { .transcript-container { grid-template-columns: 1fr; } }

.transcript-box {
  background: var(--bg-dark);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  height: 400px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.6;
}
.transcript-box h3 {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

.download-links { display: flex; gap: 12px; margin-top: 12px; }
.download-links a {
  font-size: 12px;
  color: var(--accent);
  text-decoration: none;
}
.download-links a:hover { text-decoration: underline; }

.mic-control {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--bg-dark);
  border-radius: 8px;
  margin-top: 12px;
}
.mic-btn {
  width: 60px; height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}
.mic-btn.recording { background: #ef4444; animation: pulse 1s infinite; }

.visualizer {
  flex: 1;
  height: 40px;
  background: var(--bg-card);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
}
.bar {
  width: 4px;
  background: var(--accent);
  border-radius: 2px;
  transition: height 0.1s;
}

#msg { font-size: 14px; color: var(--text-secondary); }
</style>
</head>
<body>
<div class="container">
  <h1>
    LiveTranslate
    <span class="badge">Docker Edition</span>
  </h1>

  <div class="card">
    <div class="status-bar">
      <div class="status-indicator" id="statusDot"></div>
      <span id="statusText">Idle</span>
      <span id="msg"></span>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label>Email</label>
        <input id="email" placeholder="user@example.com" value="user@example.com"/>
      </div>
      <div class="form-group">
        <label>Password</label>
        <input id="pwd" type="password" placeholder="password"/>
      </div>
      <button class="btn-secondary" onclick="login()">Login</button>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label>Target Language</label>
        <select id="target">
          <option value="en">English</option>
          <option value="zh">中文</option>
          <option value="ja">日本語</option>
          <option value="ko">한국어</option>
          <option value="fr">Français</option>
          <option value="de">Deutsch</option>
          <option value="es">Español</option>
          <option value="it">Italiano</option>
          <option value="pt">Português</option>
          <option value="ru">Русский</option>
          <option value="yue">粵語</option>
        </select>
      </div>
      <div class="form-group">
        <label>Voice</label>
        <select id="voice">
          <option>Cherry</option>
          <option>Nofish</option>
          <option>晴儿 Sunny</option>
          <option>阿珍 Jada</option>
          <option>晓东 Dylan</option>
          <option>李彼得 Peter</option>
          <option>程川 Eric</option>
          <option>阿清 Kiki</option>
        </select>
      </div>
      <button class="btn-success" id="btnStart" onclick="start()">▶ Start</button>
      <button class="btn-danger" onclick="stopit()">■ Stop</button>
    </div>

    <div class="mic-control" id="micControl" style="display:none;">
      <button class="mic-btn btn-danger" id="micBtn" onclick="toggleMic()">🎤</button>
      <div class="visualizer" id="visualizer">
        <div class="bar" style="height: 10px;"></div>
        <div class="bar" style="height: 20px;"></div>
        <div class="bar" style="height: 15px;"></div>
        <div class="bar" style="height: 25px;"></div>
        <div class="bar" style="height: 10px;"></div>
      </div>
      <span id="micStatus">Click mic to start recording</span>
    </div>
  </div>

  <div class="card">
    <h2 style="margin-bottom: 16px;">Live Transcript</h2>
    <div class="transcript-container">
      <div>
        <div class="transcript-box" id="srcBox">
          <h3>Original (Source)</h3>
          <div id="srcContent"></div>
        </div>
        <div class="download-links">
          <a href="/translate/script?type=src" target="_blank">📥 Download Source</a>
        </div>
      </div>
      <div>
        <div class="transcript-box" id="dstBox">
          <h3>Translation (Target)</h3>
          <div id="dstContent"></div>
        </div>
        <div class="download-links">
          <a href="/translate/script?type=dst" target="_blank">📥 Download Translation</a>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
let timer = null;
let mediaRecorder = null;
let audioContext = null;
let isRecording = false;
let wsAudio = null;

function login() {
  fetch('/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      email: document.getElementById('email').value,
      password: document.getElementById('pwd').value
    })
  })
  .then(r => r.json())
  .then(j => {
    document.getElementById('msg').innerText = j.message || 'Logged in';
  });
}

function start() {
  const target = document.getElementById('target').value;
  const voice = document.getElementById('voice').value;

  fetch('/translate/start', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({target, voice})
  })
  .then(r => r.json())
  .then(j => {
    document.getElementById('msg').innerText = j.message || '';
    if (!timer) {
      timer = setInterval(poll, 500);
    }
    document.getElementById('micControl').style.display = 'flex';
  });
}

function stopit() {
  stopMic();
  fetch('/translate/stop', {method: 'POST'})
  .then(r => r.json())
  .then(j => {
    document.getElementById('msg').innerText = j.message || '';
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
    document.getElementById('micControl').style.display = 'none';
    poll();
  });
}

function poll() {
  fetch('/translate/status')
  .then(r => r.json())
  .then(j => {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    if (j.running) {
      dot.classList.add('running');
      text.innerText = 'Running';
    } else {
      dot.classList.remove('running');
      text.innerText = 'Idle';
    }
    document.getElementById('srcContent').innerText = j.src || '';
    document.getElementById('dstContent').innerText = j.dst || '';
  });
}

async function toggleMic() {
  if (isRecording) {
    stopMic();
  } else {
    await startMic();
  }
}

async function startMic() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true
      }
    });

    audioContext = new AudioContext({sampleRate: 16000});
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
      if (!isRecording) return;
      const inputData = e.inputBuffer.getChannelData(0);
      const pcm16 = new Int16Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        pcm16[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
      }

      // Send to server via POST
      const b64 = btoa(String.fromCharCode.apply(null, new Uint8Array(pcm16.buffer)));
      fetch('/translate/audio', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({audio: b64})
      });
    };

    source.connect(processor);
    processor.connect(audioContext.destination);

    isRecording = true;
    document.getElementById('micBtn').classList.add('recording');
    document.getElementById('micStatus').innerText = 'Recording... Click to stop';

  } catch (err) {
    console.error('Mic error:', err);
    document.getElementById('msg').innerText = 'Microphone access denied';
  }
}

function stopMic() {
  isRecording = false;
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  document.getElementById('micBtn').classList.remove('recording');
  document.getElementById('micStatus').innerText = 'Click mic to start recording';
}

// Initial poll
poll();
setInterval(poll, 2000);
</script>
</body>
</html>
""")

@app.post("/auth/login")
def auth_login(payload: dict = Body(...)):
    email = payload.get("email", "")
    return {"ok": True, "message": f"Logged in: {email}"}

@app.get("/translate/status")
def translate_status():
    return {
        "ok": True,
        "running": SESS.running,
        "src": "".join(SESS.src_buf),
        "dst": "".join(SESS.dst_buf),
        "message": "LiveTranslate Docker server up",
    }

@app.get("/translate/script")
def translate_script(type: str = "dst"):
    if type not in ("src", "dst"):
        raise HTTPException(400, "type must be src|dst")
    text = "".join(SESS.src_buf if type == "src" else SESS.dst_buf)
    return PlainTextResponse(text, media_type="text/plain; charset=utf-8")

@app.post("/translate/start")
async def translate_start(payload: dict = Body(...)):
    if SESS.running:
        return JSONResponse({"ok": False, "message": "Session already running"}, status_code=409)

    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(400, "DASHSCOPE_API_KEY 未设置")

    target = (payload.get("target") or "en").strip()
    voice = (payload.get("voice") or "Cherry").strip()

    SESS.reset()

    client = RealtimeTranslateClient(
        api_key=api_key,
        target_language=target,
        voice=voice,
    )

    SESS.running = True

    def on_text(t: str, delta: bool = True):
        if delta:
            SESS.dst_buf.append(t)
        else:
            SESS.dst_buf.append(t + "\n")
            print(f"[TRANS] {t}")

    async def runner():
        try:
            await client.connect()
            SESS.ws_connection = client
            await client.receive_messages(on_text=on_text)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[RUNNER] error: {e}")
        finally:
            with contextlib.suppress(Exception):
                await client.close()
            SESS.running = False
            SESS.ws_connection = None
            SESS.worker = None

    SESS.worker = asyncio.create_task(runner())
    return {"ok": True, "message": f"Started: target={target}, voice={voice}"}

@app.post("/translate/audio")
async def translate_audio(payload: dict = Body(...)):
    """接收前端发送的音频数据"""
    if not SESS.running or not SESS.ws_connection:
        return {"ok": False, "message": "No active session"}

    audio_b64 = payload.get("audio", "")
    if audio_b64:
        try:
            audio_data = base64.b64decode(audio_b64)
            await SESS.ws_connection.send_audio(audio_data)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "message": str(e)}
    return {"ok": False, "message": "No audio data"}

@app.post("/translate/stop")
async def translate_stop():
    if SESS.worker:
        SESS.worker.cancel()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(SESS.worker, timeout=2)

    with contextlib.suppress(Exception):
        if SESS.ws_connection:
            await SESS.ws_connection.close()

    SESS.running = False
    SESS.ws_connection = None
    SESS.worker = None

    return {"ok": True, "message": "Stopped"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "livetranslate-docker"}

# ---------------------------
# Entrypoint
# ---------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

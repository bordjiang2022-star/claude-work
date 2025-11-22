# -*- coding: utf-8 -*-
# server.py — LiveTranslate Web (稳定版，加入“开始→自动切虚拟麦 / 停止→恢复扬声器、麦克风”)
import os, asyncio, contextlib, subprocess, tempfile
from typing import Optional, List, Tuple

import pyaudio
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from livetranslate_client import LiveTranslateClient

# === [AUDIO AUTO SWITCH] imports & state BEGIN ===
# 方案B：优先使用你项目中的 coreaudio_switch（纯 comtypes/CoreAudio，不依赖 NirCmd/SVV）
# 若没有该模块，请把我之前给你的 coreaudio_switch.py 放到同目录；或按需在此文件内嵌。
from coreaudio_switch import (
    get_default_playback_id, set_default_playback, find_playback_id_by_substring,
    get_default_capture_id,  set_default_capture,  find_capture_id_by_substring,
)

# 用一个全局槽位保存“开始时”的默认设备，停止时恢复
_AUDIO_RESTORE = {
    "play_id": None,  # 默认播放(扬声器) ID
    "play_name": None,
    "cap_id":  None,  # 默认录音(麦克风) ID
    "cap_name": None,
}
# === [AUDIO AUTO SWITCH] imports & state END ===


# ---------------------------
# Web App & CORS
# ---------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# ---------------------------
# utils: 设备枚举（与你当前可用逻辑一致）
# ---------------------------
def _pyaudio_info(idx: int) -> Optional[dict]:
    pa = pyaudio.PyAudio()
    try:
        return pa.get_device_info_by_index(idx)
    finally:
        pa.terminate()

def pick_cable_output_index() -> Optional[int]:
    """找到作为“虚拟麦克风”的 CABLE Output（录音设备）。"""
    pa = pyaudio.PyAudio()
    try:
        found = None
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if int(info.get("maxInputChannels", 0)) > 0:
                name = (info.get("name") or "").lower()
                # 兼容不同命名：CABLE Output / CABLE Output 16ch 等
                if "cable" in name and "output" in name:
                    found = i
                    break
        if found is not None:
            print(f"[PickIn ] {found} {pa.get_device_info_by_index(found).get('name')}")
        else:
            print("[PickIn ] 未找到 CABLE Output，请检查 VB-Audio Virtual Cable 安装/启用")
        return found
    finally:
        pa.terminate()

def pick_speaker_index() -> Optional[int]:
    """找到看起来像实体扬声器/耳机的播放设备，用于TTS直接播放（避开CABLE）。"""
    pa = pyaudio.PyAudio()
    try:
        cand = None
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if int(info.get("maxOutputChannels", 0)) > 0:
                name = (info.get("name") or "").lower()
                if "cable" in name:
                    continue
                if any(k in name for k in ["speaker", "扬声器", "headphone", "耳机", "realtek", "bt", "bluetooth"]):
                    cand = i
                    print(f"[PickOut] {i} {info.get('name')}")
                    break
        if cand is None:
            print("[PickOut] 未找到明显的实体扬声器，TTS 将走系统默认输出设备")
        return cand
    finally:
        pa.terminate()

def device_name_by_index(idx: Optional[int]) -> Optional[str]:
    if idx is None:
        return None
    info = _pyaudio_info(idx)
    return None if not info else (info.get("name") or None)

# ---------------------------
# （以下保留了一个 *未使用* 的 SoundVolumeView 备用实现；方案B不会调用它们。
#  如你不需要，可删除 _svv_* 与 set_default_playback_by_name/switch_default_to_cable_input 相关代码。）
# ---------------------------
def _svv_path() -> Optional[str]:
    p = os.getenv("SOUNDVOLUMEVIEW_EXE")
    if p and os.path.exists(p):
        return p
    for cand in [
        os.path.join(os.getcwd(), "SoundVolumeView.exe"),
        r"C:\Tools\SoundVolumeView\SoundVolumeView.exe",
    ]:
        if os.path.exists(cand):
            return cand
    return None

def _svv_set_default_playback(name: str) -> bool:
    exe = _svv_path()
    if not exe:
        return False
    ok = True
    for role in ("0", "1", "2"):  # 0=Console,1=Multimedia,2=Communications
        r = subprocess.run([exe, "/SetDefault", name, role], capture_output=True)
        ok = ok and (r.returncode == 0)
    return ok

def _svv_try_candidates(candidates: List[str]) -> Optional[str]:
    for nm in candidates:
        if _svv_set_default_playback(nm):
            return nm
    return None

def set_default_playback_by_name(name_or_sub: str) -> bool:
    # 方案B不使用此函数；仅保留以防你手工调用。
    tried = [name_or_sub]
    ok_name = _svv_try_candidates(tried)
    if ok_name:
        print(f"[AUDIO] Default playback => {ok_name} (SoundVolumeView)")
        return True
    return False

def switch_default_to_cable_input() -> Optional[str]:
    # 方案B不使用此函数；仅保留以防你手工调用。
    candidates = [
        "CABLE Input (VB-Audio Virtual Cable)",
        "CABLE In 16ch (VB-Audio Virtual Cable)",
        "CABLE Input",
        "CABLE In 16ch",
    ]
    for nm in candidates:
        if set_default_playback_by_name(nm):
            return nm
    print("[AUDIO] 未能把默认播放设备切到 CABLE Input，请检查系统设备名。")
    return None

# ---------------------------
# Session
# ---------------------------
class SessionState:
    def __init__(self):
        self.running: bool = False
        self.client: Optional[LiveTranslateClient] = None
        self.worker: Optional[asyncio.Task] = None
        self.src_buf: List[str] = []
        self.dst_buf: List[str] = []
        self.restore_playback_name: Optional[str] = None  # 兼容旧逻辑；当前不再使用

    def reset(self):
        self.src_buf.clear()
        self.dst_buf.clear()

SESS = SessionState()

# ---------------------------
# UI（保留你现有的）
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(
        """
<!doctype html>
<html><head><meta charset="utf-8"/>
<title>LiveTranslate (Qwen3)</title>
<style>
 body{font-family:system-ui,Segoe UI,Helvetica,Arial;margin:18px}
 .row{display:flex;gap:16px;margin-top:12px}
 .box{flex:1;border:1px solid #ddd;border-radius:8px;padding:8px;height:360px;overflow:auto;background:#0b0f19;color:#d5e1f9}
 h2{margin:0 0 8px 0;font-size:16px}
 button{padding:8px 14px;border-radius:8px;border:0;background:#2563eb;color:#fff;cursor:pointer}
 button.secondary{background:#64748b}
 select,input{padding:6px 8px;border:1px solid #ccc;border-radius:6px}
 .toolbar{display:flex;gap:10px;align-items:center;margin-top:8px}
 .muted{color:#6b7280;font-size:12px}
 .pill{font-size:12px;padding:2px 8px;border-radius:999px;background:#eef2ff;color:#3730a3}
 .footer{display:flex;gap:12px;margin-top:8px}
 a.dl{font-size:12px}
</style></head>
<body>
  <div class="toolbar">
    <span class="pill" id="status">Idle</span>
    <span class="muted" id="msg"></span>
  </div>

  <h2>Login</h2>
  <div class="toolbar">
    <input id="email" placeholder="email" value="user@example.com"/>
    <input id="pwd" placeholder="password" type="password"/>
    <button onclick="login()">Login</button>
  </div>

  <h2>Controls</h2>
  <div class="toolbar">
    <label>Target:&nbsp;</label>
    <select id="target">
      <option value="en">English</option><option value="zh">中文</option>
      <option value="ja">日本語</option><option value="ko">한국어</option>
      <option value="fr">Français</option><option value="de">Deutsch</option>
      <option value="es">Español</option><option value="it">Italiano</option>
      <option value="pt">Português</option><option value="ru">Русский</option>
      <option value="yue">粵語</option>
    </select>
    <select id="voice">
      <option>Cherry</option><option>Nofish</option><option>晴儿 Sunny</option>
      <option>阿珍 Jada</option><option>晓东 Dylan</option><option>李彼得 Peter</option>
      <option>程川 Eric</option><option>阿清 Kiki</option>
    </select>
    <button id="btnStart" onclick="start()">Start</button>
    <button class="secondary" onclick="stopit()">Stop</button>
  </div>

  <h2>Live Transcript</h2>
  <div class="row">
    <div style="flex:1">
      <div class="box" id="srcBox"></div>
      <div class="footer"><a class="dl" href="/translate/script?type=src" target="_blank">Download source</a></div>
    </div>
    <div style="flex:1">
      <div class="box" id="dstBox"></div>
      <div class="footer"><a class="dl" href="/translate/script?type=dst" target="_blank">Download translation</a></div>
    </div>
  </div>

<script>
let timer=null;
function login(){
  fetch('/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({email:document.getElementById('email').value, password:document.getElementById('pwd').value})
  }).then(r=>r.json()).then(j=>{ document.getElementById('msg').innerText=j.message||'Logged in'; });
}
function start(){
  const target=document.getElementById('target').value;
  const voice=document.getElementById('voice').value;
  fetch('/translate/start',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({target,voice})
  }).then(r=>r.json()).then(j=>{
    document.getElementById('msg').innerText=j.message||'';
    if(!timer){ timer=setInterval(poll,600); }
  });
}
function stopit(){
  fetch('/translate/stop',{method:'POST'}).then(r=>r.json()).then(j=>{
    document.getElementById('msg').innerText=j.message||'';
    if(timer){ clearInterval(timer); timer=null; }
    poll();
  });
}
function poll(){
  fetch('/translate/status').then(r=>r.json()).then(j=>{
    document.getElementById('status').innerText=j.running?'Running':'Idle';
    document.getElementById('srcBox').innerText=j.src||'';
    document.getElementById('dstBox').innerText=j.dst||'';
  });
}
setInterval(poll,1500);
</script>
</body></html>
"""
    )

# ---------------------------
# API
# ---------------------------
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
        "message": "Live Translate server up",
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
    voice  = (payload.get("voice")  or "Cherry").strip()

    # === [AUDIO AUTO SWITCH] Start: 自动切到虚拟麦克风，仅此，不动扬声器 ===
    try:
        # 0) 供“同传逻辑”使用：拾取 PyAudio 输入/输出索引（保持你当前可用的做法）
        in_idx  = pick_cable_output_index()  # 作为麦克风采集的“CABLE Output”
        out_idx = pick_speaker_index()       # TTS 直出实体扬声器
        if in_idx is None:
            raise HTTPException(500, "未找到 CABLE Output（虚拟麦克风）。")

        # 1) 记住当前默认的录音/播放设备，Stop 时恢复
        _AUDIO_RESTORE["cap_id"],  _AUDIO_RESTORE["cap_name"]  = get_default_capture_id()
        _AUDIO_RESTORE["play_id"], _AUDIO_RESTORE["play_name"] = get_default_playback_id()
        print(f"[AUDIO] Will restore Mic: {_AUDIO_RESTORE['cap_name'] or _AUDIO_RESTORE['cap_id']}")
        print(f"[AUDIO] Will restore Spk: {_AUDIO_RESTORE['play_name'] or _AUDIO_RESTORE['play_id']}")

        # 2) 将“默认录音设备(麦克风)”切到 VB-Cable 的 Output（虚拟麦克风）
        target_mic = find_capture_id_by_substring([
            "cable output (vb-audio virtual cable)", "vb-audio virtual", "cable output"
        ])
        if target_mic:
            dev_id, dev_name = target_mic
            ok = set_default_capture(dev_id)
            print(f"[AUDIO] Default CAPTURE switched to: {dev_name} -> {ok}")
        else:
            print("[AUDIO] 未找到虚拟麦克风(CABLE Output)，跳过切换（不影响同传主流程）")
    except Exception as e:
        print(f"[AUDIO] Auto mic switch failed: {e}")
        # 保底：若 in_idx 未定义，明确失败
        try:
            in_idx
        except NameError:
            raise HTTPException(500, f"音频初始化失败：{e}")

    # ——以下同传逻辑保持不动——
    SESS.reset()
    client = LiveTranslateClient(
        api_key=api_key,
        target_language=target,
        voice=voice,
        audio_enabled=True,
        input_device_index=in_idx,
        output_device_index=out_idx,  # TTS 直出扬声器
    )
    SESS.client = client
    SESS.running = True

    def on_delta(t: str):
        SESS.dst_buf.append(t)

    def on_done(t: str):
        SESS.dst_buf.append(t + "\n")

    async def runner():
        try:
            await client.connect()
            client.start_audio_player()
            t1 = asyncio.create_task(client.handle_server_messages(on_text_delta=on_delta, on_text_done=on_done))
            t2 = asyncio.create_task(client.start_microphone_streaming())
            await asyncio.gather(t1, t2)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("[RUNNER] error:", e)
        finally:
            with contextlib.suppress(Exception):
                await client.close()
            SESS.running = False
            SESS.client = None
            SESS.worker = None
    SESS.worker = asyncio.create_task(runner())
    return {"ok": True, "message": f"Started: target={target}, voice={voice}"}

@app.post("/translate/stop")
async def translate_stop():
    # 停止同传
    if SESS.worker:
        SESS.worker.cancel()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(SESS.worker, timeout=2)
    with contextlib.suppress(Exception):
        if SESS.client:
            await SESS.client.close()
    SESS.running = False
    SESS.client = None
    SESS.worker = None

    # === [AUDIO AUTO SWITCH] Stop: 恢复默认设备（扬声器 & 麦克风） ===
    try:
        # 先恢复扬声器（你的重点需求）
        if _AUDIO_RESTORE.get("play_id"):
            ok = set_default_playback(_AUDIO_RESTORE["play_id"])
            print(f"[AUDIO] Restore Speaker -> {_AUDIO_RESTORE['play_name'] or _AUDIO_RESTORE['play_id']}: {ok}")
        else:
            print("[AUDIO] 没有记录到启动前的扬声器，跳过")

        # 再恢复麦克风（避免系统残留在虚拟麦）
        if _AUDIO_RESTORE.get("cap_id"):
            ok2 = set_default_capture(_AUDIO_RESTORE["cap_id"])
            print(f"[AUDIO] Restore Mic -> {_AUDIO_RESTORE['cap_name'] or _AUDIO_RESTORE['cap_id']}: {ok2}")
        else:
            print("[AUDIO] 没有记录到启动前的麦克风，跳过")
    except Exception as e:
        print(f"[AUDIO] Restore failed: {e}")

    return {"ok": True, "message": "Stopped and restored audio defaults."}

# ---------------------------
# Entrypoint
# ---------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

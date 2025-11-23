# livetranslate_client.py
# -*- coding: utf-8 -*-

import time
import base64
import asyncio
import json
import queue
import threading
import traceback
import contextlib
import audioop  # Python 3.11 内置，用于重采样
import inspect
import tempfile
import os
import wave

import pyaudio
import websockets
from websockets import connect

# Windows TTS 支持（可选）
PYTTSX3_AVAILABLE = False
pyttsx3 = None
try:
    import pyttsx3 as _pyttsx3
    # 尝试初始化以验证真正可用（Windows COM 组件可能导入成功但初始化失败）
    _test_engine = _pyttsx3.init()
    _test_engine.stop()
    pyttsx3 = _pyttsx3
    PYTTSX3_AVAILABLE = True
    print("[TTS] pyttsx3 initialized successfully, Windows TTS available")
except ImportError as e:
    print(f"[TTS] pyttsx3 not installed: {e}")
except Exception as e:
    print(f"[TTS] pyttsx3 import/init failed: {type(e).__name__}: {e}")

# Windows SAPI COM 直接访问支持（低延迟内存流 TTS）
SAPI_AVAILABLE = False
try:
    import comtypes.client
    # 初始化 SAPI 类型库
    comtypes.client.GetModule("SAPI.SpVoice")
    from comtypes.gen import SpeechLib
    SAPI_AVAILABLE = True
    print("[TTS] SAPI COM interface available for low-latency TTS")
except ImportError:
    print("[TTS] comtypes not installed, falling back to pyttsx3")
except Exception as e:
    print(f"[TTS] SAPI COM init failed: {type(e).__name__}: {e}")


# ===================== 全局 Windows TTS 管理器（单例） =====================
# pyttsx3 在 Windows 上使用 SAPI，不支持多实例同时运行
# 所有翻译会话共享同一个 TTS 引擎和播放线程

class WindowsTTSManager:
    """
    全局 Windows TTS 管理器（单例模式）
    - 确保只有一个 pyttsx3 引擎实例
    - 所有翻译会话共享同一个播放队列和线程
    - 避免 "run loop already started" 错误
    - 支持输出到指定的扬声器设备
    - 优先使用 SAPI COM 内存流（低延迟），回退到 pyttsx3 文件方式
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.queue: "queue.Queue[tuple[str, str] | None]" = queue.Queue()  # (text, target_language)
        self.thread: threading.Thread | None = None
        self.is_running = False
        self.current_language = "en"
        self._engine_lock = threading.Lock()
        self.output_device_index: int | None = None  # 输出设备索引
        self.pyaudio_instance: pyaudio.PyAudio | None = None
        self.use_sapi_direct = SAPI_AVAILABLE  # 优先使用 SAPI 直接内存输出
        self._sapi_voice = None  # 缓存的 SAPI 语音对象
        print(f"[TTS-MGR] WindowsTTSManager singleton initialized (SAPI direct: {self.use_sapi_direct})")

    def set_output_device(self, device_index: int | None):
        """设置输出设备索引"""
        self.output_device_index = device_index
        print(f"[TTS-MGR] Output device set to index: {device_index}")

    def start(self, output_device_index: int | None = None):
        """启动全局 TTS 播放线程"""
        if output_device_index is not None:
            self.output_device_index = output_device_index

        with self._engine_lock:
            if self.thread is None or not self.thread.is_alive():
                self.is_running = True
                # 初始化 PyAudio
                if self.pyaudio_instance is None:
                    self.pyaudio_instance = pyaudio.PyAudio()
                self.thread = threading.Thread(target=self._player_task, daemon=True)
                self.thread.start()
                print(f"[TTS-MGR] Global Windows TTS player thread started, output_device={self.output_device_index}")

    def stop(self):
        """停止全局 TTS 播放线程"""
        self.is_running = False
        self.queue.put(None)
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
            self.pyaudio_instance = None
        print("[TTS-MGR] Global Windows TTS player stopped")

    def speak(self, text: str, target_language: str = "en"):
        """添加文本到全局播放队列"""
        if not PYTTSX3_AVAILABLE:
            return
        # 确保播放线程在运行
        if not self.thread or not self.thread.is_alive():
            self.start()
        self.queue.put((text, target_language))

    def _select_voice(self, engine, target_language: str):
        """根据目标语言选择合适的语音"""
        voices = engine.getProperty('voices')

        lang_map = {
            'ja': ['japanese', 'japan', 'haruka', 'sayaka'],
            'zh': ['chinese', 'china', 'huihui', 'yaoyao'],
            'ko': ['korean', 'korea', 'heami'],
            'en': ['english', 'david', 'zira', 'mark'],
        }

        search_keywords = lang_map.get(target_language, lang_map['en'])

        for voice in voices:
            voice_name_lower = voice.name.lower()
            for keyword in search_keywords:
                if keyword in voice_name_lower:
                    return voice.id
        return None

    def _pick_real_speaker_index(self) -> tuple[int | None, int, str]:
        """
        自动选择真实扬声器/耳机，避免把TTS回灌到虚拟线。
        Returns: (device_index, sample_rate, device_name)
        """
        if self.pyaudio_instance is None:
            return None, 44100, "Unknown"

        speaker_keywords = ("Speakers", "Headphones", "Realtek", "耳机", "扬声器")
        virtual_keywords = ("cable", "virtual", "vb-audio")

        for i in range(self.pyaudio_instance.get_device_count()):
            info = self.pyaudio_instance.get_device_info_by_index(i)
            if int(info.get('maxOutputChannels', 0)) > 0:
                name = info.get('name', '')
                name_lower = name.lower()

                # 跳过虚拟音频线缆
                if any(vk in name_lower for vk in virtual_keywords):
                    continue

                # 选择真实扬声器/耳机
                if any(sk.lower() in name_lower for sk in speaker_keywords):
                    rate = int(info.get('defaultSampleRate', 44100))
                    print(f"[TTS-MGR] Auto-detected real speaker: [{i}] {name}")
                    return i, rate, name

        return None, 44100, "Unknown"

    def _play_wav_to_device(self, wav_path: str, device_index: int | None) -> bool:
        """播放 WAV 文件到指定设备"""
        if self.pyaudio_instance is None:
            print("[TTS-MGR] PyAudio not initialized")
            return False

        try:
            with wave.open(wav_path, 'rb') as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                frame_rate = wf.getframerate()

                # 确定实际使用的设备
                effective_device = device_index
                if effective_device is None:
                    # 自动选择真实扬声器
                    effective_device, _, dev_name = self._pick_real_speaker_index()
                    if effective_device is not None:
                        print(f"[TTS-MGR] Auto-selected speaker: {dev_name}")

                # 打开音频流
                open_kwargs = {
                    "format": self.pyaudio_instance.get_format_from_width(sample_width),
                    "channels": channels,
                    "rate": frame_rate,
                    "output": True,
                }
                if effective_device is not None:
                    open_kwargs["output_device_index"] = effective_device

                stream = self.pyaudio_instance.open(**open_kwargs)

                # 播放音频
                chunk_size = 1024
                data = wf.readframes(chunk_size)
                while data:
                    stream.write(data)
                    data = wf.readframes(chunk_size)

                stream.stop_stream()
                stream.close()
                return True

        except Exception as e:
            print(f"[TTS-MGR] Error playing WAV: {e}")
            return False

    def _speak_with_sapi_direct(self, text: str, target_language: str) -> bool:
        """
        使用 SAPI COM 直接输出到内存，然后通过 PyAudio 播放到指定设备。
        这种方式避免了文件 I/O，大大降低延迟。
        """
        if not SAPI_AVAILABLE:
            return False

        try:
            import comtypes.client
            from comtypes.gen import SpeechLib

            # 创建 SAPI 语音对象
            voice = comtypes.client.CreateObject("SAPI.SpVoice")

            # 选择语音
            voices = voice.GetVoices()
            lang_map = {
                'ja': ['japanese', 'japan', 'haruka', 'sayaka'],
                'zh': ['chinese', 'china', 'huihui', 'yaoyao'],
                'ko': ['korean', 'korea', 'heami'],
                'en': ['english', 'david', 'zira', 'mark'],
            }
            search_keywords = lang_map.get(target_language, lang_map['en'])

            for i in range(voices.Count):
                v = voices.Item(i)
                desc = v.GetDescription().lower()
                for keyword in search_keywords:
                    if keyword in desc:
                        voice.Voice = v
                        break

            # 设置语速 (-10 到 10，0 为正常)
            voice.Rate = 2  # 稍快

            # 创建内存流
            stream = comtypes.client.CreateObject("SAPI.SpMemoryStream")

            # 设置音频格式：22kHz, 16-bit, Mono
            format_obj = comtypes.client.CreateObject("SAPI.SpAudioFormat")
            format_obj.Type = SpeechLib.SAFT22kHz16BitMono
            stream.Format = format_obj

            # 将语音输出到内存流
            voice.AudioOutputStream = stream

            # 合成语音
            voice.Speak(text, 0)  # 0 = 同步

            # 获取音频数据
            stream.Seek(0, 0)  # 回到开头
            audio_data = stream.GetData()

            if not audio_data or len(audio_data) == 0:
                print("[TTS-MGR] SAPI produced no audio data")
                return False

            # 将 audio_data 转换为 bytes
            if hasattr(audio_data, 'tobytes'):
                audio_bytes = audio_data.tobytes()
            elif isinstance(audio_data, (bytes, bytearray)):
                audio_bytes = bytes(audio_data)
            else:
                # comtypes 返回的可能是 SAFEARRAY
                audio_bytes = bytes(audio_data)

            # 通过 PyAudio 播放到指定设备
            return self._play_audio_data(audio_bytes, 22050, 2, 1)

        except Exception as e:
            print(f"[TTS-MGR] SAPI direct error: {e}")
            traceback.print_exc()
            return False

    def _play_audio_data(self, audio_data: bytes, sample_rate: int, sample_width: int, channels: int) -> bool:
        """
        直接播放内存中的音频数据到指定设备
        """
        if self.pyaudio_instance is None:
            print("[TTS-MGR] PyAudio not initialized")
            return False

        try:
            # 确定实际使用的设备
            effective_device = self.output_device_index
            if effective_device is None:
                effective_device, _, dev_name = self._pick_real_speaker_index()
                if effective_device is not None:
                    print(f"[TTS-MGR] Auto-selected speaker: {dev_name}")

            # 获取设备原生采样率
            dev_rate = sample_rate
            if effective_device is not None:
                try:
                    dev_info = self.pyaudio_instance.get_device_info_by_index(effective_device)
                    dev_rate = int(dev_info.get('defaultSampleRate', sample_rate))
                except:
                    pass

            # 如果设备采样率不同，需要重采样
            if dev_rate != sample_rate:
                audio_data, _ = audioop.ratecv(
                    audio_data, sample_width, channels, sample_rate, dev_rate, None
                )
                actual_rate = dev_rate
            else:
                actual_rate = sample_rate

            # 打开音频流
            open_kwargs = {
                "format": self.pyaudio_instance.get_format_from_width(sample_width),
                "channels": channels,
                "rate": actual_rate,
                "output": True,
            }
            if effective_device is not None:
                open_kwargs["output_device_index"] = effective_device

            stream = self.pyaudio_instance.open(**open_kwargs)

            # 分块播放
            chunk_size = 4096
            offset = 0
            while offset < len(audio_data):
                chunk = audio_data[offset:offset + chunk_size]
                stream.write(chunk)
                offset += chunk_size

            stream.stop_stream()
            stream.close()
            return True

        except Exception as e:
            print(f"[TTS-MGR] Error playing audio data: {e}")
            return False

    def _player_task(self):
        """全局 TTS 播放器线程任务"""
        print("[TTS-MGR] ========================================")
        print("[TTS-MGR] Global Windows TTS player task STARTED")
        print(f"[TTS-MGR] Output device index: {self.output_device_index}")
        print(f"[TTS-MGR] Using SAPI direct (low-latency): {self.use_sapi_direct}")
        print("[TTS-MGR] ========================================")

        engine = None
        sentences_spoken = 0
        sapi_failures = 0  # 跟踪 SAPI 失败次数

        try:
            while self.is_running or not self.queue.empty():
                try:
                    item = self.queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                if item is None:
                    print("[TTS-MGR] Received stop signal")
                    break

                text, target_language = item
                text = text.strip()
                if not text:
                    self.queue.task_done()
                    continue

                print(f"[TTS-MGR] Speaking: {text[:50]}...")
                start_time = time.time()

                # 方案1：优先使用 SAPI 直接内存输出（低延迟）
                if self.use_sapi_direct and sapi_failures < 3:
                    try:
                        if self._speak_with_sapi_direct(text, target_language):
                            elapsed = time.time() - start_time
                            print(f"[TTS-MGR] SAPI direct succeeded in {elapsed:.2f}s")
                            sentences_spoken += 1
                            self.queue.task_done()
                            continue
                        else:
                            sapi_failures += 1
                            print(f"[TTS-MGR] SAPI direct failed, falling back to pyttsx3")
                    except Exception as sapi_err:
                        sapi_failures += 1
                        print(f"[TTS-MGR] SAPI direct error: {sapi_err}")

                # 方案2：回退到 pyttsx3 文件方式
                try:
                    # 每次说话前重新初始化引擎（避免 "run loop already started" 错误）
                    if engine is not None:
                        try:
                            engine.stop()
                        except:
                            pass

                    engine = pyttsx3.init()
                    engine.setProperty('rate', 180)
                    engine.setProperty('volume', 1.0)

                    # 切换语音（如果语言改变）
                    if target_language != self.current_language:
                        voice_id = self._select_voice(engine, target_language)
                        if voice_id:
                            engine.setProperty('voice', voice_id)
                            print(f"[TTS-MGR] Switched voice for language: {target_language}")
                        self.current_language = target_language

                    # 使用 save_to_file + PyAudio 播放到指定设备
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                        tmp_path = tmp.name

                    try:
                        engine.save_to_file(text, tmp_path)
                        engine.runAndWait()

                        # 播放到指定设备
                        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                            self._play_wav_to_device(tmp_path, self.output_device_index)
                            elapsed = time.time() - start_time
                            print(f"[TTS-MGR] pyttsx3 file method succeeded in {elapsed:.2f}s")
                        else:
                            print(f"[TTS-MGR] WAV file not generated or empty")
                    finally:
                        # 清理临时文件
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)

                    sentences_spoken += 1

                except Exception as speak_err:
                    print(f"[TTS-MGR] Error speaking: {speak_err}")
                    traceback.print_exc()
                    # 出错后清理引擎
                    if engine:
                        try:
                            engine.stop()
                        except:
                            pass
                        engine = None

                self.queue.task_done()

            print(f"[TTS-MGR] Playback loop ended, total sentences spoken: {sentences_spoken}")

        except Exception as e:
            print(f"[TTS-MGR] Error in global TTS player: {e}")
            traceback.print_exc()
        finally:
            if engine:
                try:
                    engine.stop()
                except:
                    pass
            print("[TTS-MGR] Global Windows TTS player stopped")


# 全局单例实例
_windows_tts_manager: WindowsTTSManager | None = None


def get_windows_tts_manager() -> WindowsTTSManager:
    """获取全局 Windows TTS 管理器实例"""
    global _windows_tts_manager
    if _windows_tts_manager is None:
        _windows_tts_manager = WindowsTTSManager()
    return _windows_tts_manager


class LiveTranslateClient:
    """
    连接通义 Qwen 实时同传（qwen3-livetranslate-flash-realtime）的轻量客户端。
    - 支持从指定输入设备采集音频，必要时重采样为 16k PCM16。
    - 可选播放返回的 TTS。
    - 通过 on_text_received 回调向上层抛出“增量/结句”文本。
    """

    def __init__(
        self,
        api_key: str,
        target_language: str = "en",
        voice: str | None = "Cherry",
        *,
        audio_enabled: bool = True,
        input_device_index: int | None = None,
        output_device_index: int | None = None,  # TTS 输出设备索引
        tts_engine: str = "alibaba",  # TTS引擎: alibaba 或 windows
    ):
        if not api_key:
            raise ValueError("API key cannot be empty.")

        # 基本配置
        self.api_key = api_key
        self.target_language = target_language
        self.audio_enabled = audio_enabled
        self.voice = voice if audio_enabled else "Cherry"
        self.output_device_index = output_device_index  # TTS 输出设备
        self.tts_engine = tts_engine  # TTS引擎选择

        # Windows TTS 引擎（pyttsx3）
        self.windows_tts_engine = None
        self.windows_tts_queue: "queue.Queue[str | None]" = queue.Queue()
        self.windows_tts_thread: threading.Thread | None = None

        # Realtime WS endpoint
        self.api_url = (
            "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime"
            "?model=qwen3-livetranslate-flash-realtime"
        )

        # 发送到模型的音频参数（固定 16k/mono/pcm16）
        self.input_rate = 16000
        self.input_chunk = 1600  # 100ms
        self.input_format = pyaudio.paInt16
        self.input_channels = 1

        # 本地播放（可选）
        self.output_rate = 24000
        self.output_chunk = 2400
        self.output_format = pyaudio.paInt16
        self.output_channels = 1

        # 运行态
        self.is_connected = False
        self.ws = None
        self.pyaudio_instance = pyaudio.PyAudio()
        self.audio_playback_queue: "queue.Queue[bytes | None]" = queue.Queue()
        self.audio_player_thread: threading.Thread | None = None
        self.input_device_index = input_device_index

    # --------------------- Connection ---------------------

    async def connect(self):
        """建立 WebSocket 连接并发送会话配置。"""
        headers = [("Authorization", f"Bearer {self.api_key}")]
        try:
            self.ws = await connect(self.api_url, extra_headers=headers)
            self.is_connected = True
            print(f"[WS] Connected: {self.api_url}")
            await self.configure_session()
        except Exception as e:
            self.is_connected = False
            raise RuntimeError(f"连接失败: {e}") from e

    async def configure_session(self):
        """配置翻译会话：输出类型/音色/目标语言等。"""
        # 当使用 Windows TTS 时，不请求阿里云返回音频
        use_alibaba_audio = self.audio_enabled and self.tts_engine == "alibaba"

        session = {
            "modalities": ["text", "audio"] if use_alibaba_audio else ["text"],
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "translation": {"language": self.target_language},
        }
        if use_alibaba_audio and self.voice:
            session["voice"] = self.voice

        print(f"[WS] Configuring session: tts_engine={self.tts_engine}, use_alibaba_audio={use_alibaba_audio}")

        event = {
            "event_id": f"event_{int(time.time() * 1000)}",
            "type": "session.update",
            "session": session,
        }
        await self.ws.send(json.dumps(event))

    # --------------------- Send ---------------------

    async def send_audio_chunk(self, audio_data: bytes):
        """发送一帧（~100ms）音频到服务端。"""
        if not self.is_connected or not self.ws:
            return
        event = {
            "event_id": f"event_{int(time.time() * 1000)}",
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(audio_data).decode(),
        }
        await self.ws.send(json.dumps(event))

    # --------------------- Audio Out (TTS) ---------------------

    def _pick_real_speaker_index(self) -> tuple[int | None, int, str]:
        """
        自动选择真实扬声器/耳机，避免把TTS回灌到虚拟线。
        参照成功的 main.py 中的 pick_speaker_index() 逻辑。

        Returns:
            tuple: (device_index, sample_rate, device_name)
        """
        speaker_keywords = ("Speakers", "Headphones", "Realtek", "耳机", "扬声器")
        virtual_keywords = ("cable", "virtual", "vb-audio")

        candidate_index = None
        candidate_rate = 44100
        candidate_name = "Unknown"

        for i in range(self.pyaudio_instance.get_device_count()):
            info = self.pyaudio_instance.get_device_info_by_index(i)
            if int(info.get('maxOutputChannels', 0)) > 0:
                name = info.get('name', '')
                name_lower = name.lower()

                # 跳过虚拟音频线缆
                if any(vk in name_lower for vk in virtual_keywords):
                    continue

                # 选择真实扬声器/耳机
                if any(sk.lower() in name_lower for sk in speaker_keywords):
                    candidate_index = i
                    candidate_rate = int(info.get('defaultSampleRate', 44100))
                    candidate_name = name
                    print(f"[TTS] Found real speaker: [{i}] {name}")
                    break

        return candidate_index, candidate_rate, candidate_name

    def _audio_player_task(self):
        # 独立线程播放返回的 TTS
        # 支持指定输出设备（扬声器）
        print(f"[TTS] ========================================")
        print(f"[TTS] Audio player task STARTED")
        print(f"[TTS] audio_enabled={self.audio_enabled}")
        print(f"[TTS] output_device_index={self.output_device_index}")

        # 列出所有可用的输出设备
        print(f"[TTS] Available output devices:")
        for i in range(self.pyaudio_instance.get_device_count()):
            info = self.pyaudio_instance.get_device_info_by_index(i)
            if info.get('maxOutputChannels', 0) > 0:
                print(f"[TTS]   [{i}] {info.get('name')} (rate: {int(info.get('defaultSampleRate', 0))}Hz)")
        print(f"[TTS] ========================================")

        stream = None
        actual_rate = self.output_rate  # TTS 输出采样率 24kHz
        need_resample = False

        # 确定要使用的输出设备索引
        effective_output_index = self.output_device_index

        try:
            # 获取设备支持的采样率
            dev_rate = 44100  # 默认安全值
            dev_name = "Unknown"
            if self.output_device_index is not None:
                dev_info = self.pyaudio_instance.get_device_info_by_index(self.output_device_index)
                dev_rate = int(dev_info.get('defaultSampleRate', 44100))
                dev_name = dev_info.get('name', 'Unknown')
                print(f"[TTS] Using SPECIFIED output device: {dev_name} (index={self.output_device_index})")
            else:
                # 关键修复：自动选择真实扬声器，避免虚拟音频线缆
                # 参照成功的 main.py 中的 pick_speaker_index() 逻辑
                print(f"[TTS] No output device specified, auto-detecting real speaker...")
                speaker_idx, speaker_rate, speaker_name = self._pick_real_speaker_index()

                if speaker_idx is not None:
                    effective_output_index = speaker_idx
                    dev_rate = speaker_rate
                    dev_name = speaker_name
                    print(f"[TTS] AUTO-SELECTED real speaker: {dev_name} (index={speaker_idx})")
                else:
                    # 找不到明确的扬声器，回退到系统默认（但警告用户）
                    print(f"[TTS] WARNING: No real speaker found, falling back to system default")
                    try:
                        default_out = self.pyaudio_instance.get_default_output_device_info()
                        dev_rate = int(default_out.get('defaultSampleRate', 44100))
                        dev_name = default_out.get('name', 'Unknown')
                        print(f"[TTS] Using SYSTEM DEFAULT output device: {dev_name}")
                        print(f"[TTS] WARNING: If this is a virtual cable, you won't hear audio!")
                    except Exception as e:
                        print(f"[TTS] Could not get default device info: {e}")
                        print(f"[TTS] Will let PyAudio choose automatically")
            print(f"[TTS] Device native rate: {dev_rate}Hz, TTS rate: {self.output_rate}Hz")

            # Windows 音频驱动器对非原生采样率支持不佳，可能导致堆损坏
            # 始终使用设备原生采样率并重采样 TTS 音频
            if dev_rate != self.output_rate:
                actual_rate = dev_rate
                need_resample = True
                print(f"[TTS] Will resample from {self.output_rate}Hz to {dev_rate}Hz for compatibility")
            else:
                actual_rate = self.output_rate
                need_resample = False
                print(f"[TTS] Device natively supports {self.output_rate}Hz, no resampling needed")

            # 计算缓冲区大小（基于实际采样率）
            frames_per_buffer = int(self.output_chunk * actual_rate // self.output_rate)

            open_kwargs = {
                "format": self.output_format,
                "channels": self.output_channels,
                "rate": actual_rate,
                "output": True,
                "frames_per_buffer": frames_per_buffer,
            }
            # 使用 effective_output_index（可能是用户指定的，也可能是自动检测的真实扬声器）
            if effective_output_index is not None:
                open_kwargs["output_device_index"] = effective_output_index

            print(f"[TTS] Opening stream with kwargs: {open_kwargs}")
            stream = self.pyaudio_instance.open(**open_kwargs)
            print(f"[TTS] SUCCESS: Opened stream at {actual_rate}Hz")

        except Exception as e:
            print(f"[TTS] Failed to open output stream: {e}")
            return  # 无法打开流，退出

        if stream is None:
            print("[TTS] Stream is None, cannot play audio")
            return

        try:
            resample_state = None
            chunks_played = 0
            print(f"[TTS] Starting playback loop, is_connected={self.is_connected}")
            while self.is_connected or not self.audio_playback_queue.empty():
                try:
                    chunk = self.audio_playback_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                if chunk is None:
                    print("[TTS] Received stop signal")
                    break
                try:
                    # 如果需要重采样（从 24kHz 到设备采样率）
                    if need_resample and actual_rate != self.output_rate:
                        chunk, resample_state = audioop.ratecv(
                            chunk, 2, 1, self.output_rate, actual_rate, resample_state
                        )
                    stream.write(chunk)
                    chunks_played += 1
                    if chunks_played % 50 == 0:
                        print(f"[TTS] Played {chunks_played} chunks")
                except Exception as write_err:
                    print(f"[TTS] Error writing audio: {write_err}")
                self.audio_playback_queue.task_done()
            print(f"[TTS] Playback loop ended, total chunks played: {chunks_played}")
        finally:
            with contextlib.suppress(Exception):
                stream.stop_stream()
                stream.close()
            print("[TTS] Audio player stopped")

    def start_audio_player(self):
        print(f"[TTS] start_audio_player called, audio_enabled={self.audio_enabled}, tts_engine={self.tts_engine}")
        if not self.audio_enabled:
            print("[TTS] Audio disabled, skipping player start")
            return

        if self.tts_engine == "windows":
            # 使用 Windows TTS (pyttsx3)
            self._start_windows_tts_player()
        else:
            # 使用阿里云 TTS（默认）
            if self.audio_player_thread is None or not self.audio_player_thread.is_alive():
                print("[TTS] Creating and starting Alibaba audio player thread")
                self.audio_player_thread = threading.Thread(
                    target=self._audio_player_task, daemon=True
                )
                self.audio_player_thread.start()
                print("[TTS] Alibaba audio player thread started")
            else:
                print("[TTS] Alibaba audio player thread already running")

    # --------------------- Windows TTS (pyttsx3) ---------------------

    def _start_windows_tts_player(self):
        """启动 Windows TTS 播放器（使用全局管理器）"""
        if not PYTTSX3_AVAILABLE:
            print("[TTS] ERROR: pyttsx3 not available, cannot use Windows TTS")
            return

        # 使用全局 Windows TTS 管理器（单例），避免多实例冲突
        tts_manager = get_windows_tts_manager()
        # 传递输出设备索引，支持输出到指定扬声器
        tts_manager.start(output_device_index=self.output_device_index)
        print(f"[TTS] Using global Windows TTS manager, output_device={self.output_device_index}")

    def _windows_tts_player_task(self):
        """Windows TTS 播放器线程任务"""
        print(f"[TTS-WIN] ========================================")
        print(f"[TTS-WIN] Windows TTS player task STARTED")
        print(f"[TTS-WIN] target_language={self.target_language}")
        print(f"[TTS-WIN] ========================================")

        try:
            # 初始化 pyttsx3 引擎（必须在同一线程中初始化和使用）
            engine = pyttsx3.init()

            # 设置语音属性
            engine.setProperty('rate', 180)  # 语速
            engine.setProperty('volume', 1.0)  # 音量

            # 尝试选择合适的语音
            voices = engine.getProperty('voices')
            target_voice = None

            # 根据目标语言选择语音
            lang_map = {
                'ja': ['japanese', 'japan', 'haruka', 'sayaka', 'microsoft haruka', 'microsoft sayaka'],
                'zh': ['chinese', 'china', 'huihui', 'yaoyao', 'microsoft huihui', 'microsoft yaoyao'],
                'ko': ['korean', 'korea', 'heami', 'microsoft heami'],
                'en': ['english', 'david', 'zira', 'mark', 'microsoft david', 'microsoft zira'],
            }

            search_keywords = lang_map.get(self.target_language, lang_map['en'])

            print(f"[TTS-WIN] Available voices:")
            for voice in voices:
                voice_name_lower = voice.name.lower()
                print(f"[TTS-WIN]   - {voice.name} ({voice.id})")
                if target_voice is None:
                    for keyword in search_keywords:
                        if keyword in voice_name_lower:
                            target_voice = voice.id
                            print(f"[TTS-WIN] Selected voice: {voice.name}")
                            break

            if target_voice:
                engine.setProperty('voice', target_voice)
            else:
                print(f"[TTS-WIN] No matching voice found for '{self.target_language}', using default")

            sentences_spoken = 0
            print(f"[TTS-WIN] Starting playback loop, is_connected={self.is_connected}")

            while self.is_connected or not self.windows_tts_queue.empty():
                try:
                    text = self.windows_tts_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                if text is None:
                    print("[TTS-WIN] Received stop signal")
                    break

                # 清理文本
                text = text.strip()
                if not text:
                    self.windows_tts_queue.task_done()
                    continue

                try:
                    print(f"[TTS-WIN] Speaking: {text[:50]}...")
                    engine.say(text)
                    engine.runAndWait()
                    sentences_spoken += 1
                    if sentences_spoken % 10 == 0:
                        print(f"[TTS-WIN] Spoken {sentences_spoken} sentences")
                except Exception as speak_err:
                    print(f"[TTS-WIN] Error speaking: {speak_err}")

                self.windows_tts_queue.task_done()

            print(f"[TTS-WIN] Playback loop ended, total sentences spoken: {sentences_spoken}")

        except Exception as e:
            print(f"[TTS-WIN] Error in Windows TTS player: {e}")
            traceback.print_exc()
        finally:
            print("[TTS-WIN] Windows TTS player stopped")

    def speak_with_windows_tts(self, text: str):
        """将文本添加到全局 Windows TTS 队列"""
        if self.tts_engine == "windows" and self.audio_enabled:
            tts_manager = get_windows_tts_manager()
            tts_manager.speak(text, self.target_language)

    # --------------------- Receive ---------------------

    async def handle_server_messages(self, on_text_received=None):
        """
        读取服务端事件：文本增量/音频增量/完成通知等。
        把“句子完成”事件也通过回调抛给上层，从而让前端显示文本。
        """
        try:
            async for message in self.ws:
                event = json.loads(message)
                et = event.get("type")

                if et == "error":
                    print(f"[WS][ERROR EVT] {message}")
                    continue

                # 增量文本 —— 直接回调
                if et == "response.audio_transcript.delta":
                    text = event.get("transcript", "")
                    if text and on_text_received:
                        if inspect.iscoroutinefunction(on_text_received):
                            await on_text_received(text)
                        else:
                            on_text_received(text)

                # 增量音频（TTS）
                elif et == "response.audio.delta" and self.audio_enabled:
                    b64 = event.get("delta")
                    if b64:
                        audio_data = base64.b64decode(b64)
                        queue_size = self.audio_playback_queue.qsize()
                        # 每10个音频块打印一次日志，避免刷屏
                        if queue_size % 10 == 0:
                            print(f"[TTS] Received audio delta: {len(audio_data)} bytes, queue size: {queue_size}")
                        self.audio_playback_queue.put(audio_data)

                # 句子完成 —— 也回调（关键：驱动前端显示）
                elif et in ("response.audio_transcript.done", "response.text.done"):
                    text = event.get("transcript") or event.get("text") or ""
                    if text:
                        if on_text_received:
                            if inspect.iscoroutinefunction(on_text_received):
                                await on_text_received(text + "\n")
                            else:
                                on_text_received(text + "\n")
                        print(f"[TRANS] {text}")

                        # 如果使用 Windows TTS，将完整句子发送到朗读队列
                        if self.tts_engine == "windows" and self.audio_enabled:
                            self.speak_with_windows_tts(text)

                elif et == "response.done":
                    usage = event.get("response", {}).get("usage", {})
                    if usage:
                        print(f"[USAGE] {json.dumps(usage, ensure_ascii=False)}")

        except websockets.exceptions.ConnectionClosed as e:
            print(f"[WS] Closed: {e}")
            self.is_connected = False
        except Exception as e:
            print(f"[WS] Error: {e}")
            traceback.print_exc()
            self.is_connected = False

    # --------------------- Mic capture ---------------------

    async def start_microphone_streaming(self):
        """
        从指定输入设备采集并推流：
        - 设备采样率可能是 44100/48000，统一重采样为 16000 再发送。
        """
        # 计算设备参数（如果用户指定了 input_device_index，就用它）
        dev_index = self.input_device_index
        dev_rate = None

        if dev_index is not None:
            with contextlib.suppress(Exception):
                info = self.pyaudio_instance.get_device_info_by_index(dev_index)
                dev_rate = int(info.get("defaultSampleRate", 44100))

        # 未指定或获取失败时，PyAudio 会用系统默认输入
        if not dev_rate:
            dev_rate = 44100

        frames_per_buffer_dev = max(1, int(self.input_chunk * dev_rate // self.input_rate))

        stream = self.pyaudio_instance.open(
            format=self.input_format,
            channels=self.input_channels,
            rate=dev_rate,
            input=True,
            input_device_index=dev_index,
            frames_per_buffer=frames_per_buffer_dev,
        )
        print(f"Mic/Virtual Source is ON. DeviceRate={dev_rate} -> SendRate={self.input_rate}")

        try:
            loop = asyncio.get_event_loop()
            while self.is_connected:
                raw = await loop.run_in_executor(None, stream.read, frames_per_buffer_dev)
                # 重采样到 16k
                if dev_rate != self.input_rate:
                    raw, _ = audioop.ratecv(raw, 2, 1, dev_rate, self.input_rate, None)
                await self.send_audio_chunk(raw)
        finally:
            with contextlib.suppress(Exception):
                stream.stop_stream()
                stream.close()

    # --------------------- Close ---------------------

    async def close(self):
        """优雅关闭。"""
        self.is_connected = False
        if self.ws:
            with contextlib.suppress(Exception):
                await self.ws.close()
            print("[WS] Closed.")

        # 关闭阿里云 TTS 播放器线程
        if self.audio_player_thread:
            self.audio_playback_queue.put(None)
            with contextlib.suppress(Exception):
                self.audio_player_thread.join(timeout=1)
            print("[AUDIO] Alibaba TTS player stopped.")

        # Windows TTS 使用全局管理器，不需要在会话关闭时停止
        # 全局管理器会持续运行以服务所有会话
        if self.tts_engine == "windows":
            print("[AUDIO] Windows TTS uses global manager, not stopping.")

        with contextlib.suppress(Exception):
            self.pyaudio_instance.terminate()
        print("[AUDIO] PyAudio terminated.")

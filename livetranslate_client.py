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

import pyaudio
import websockets
from websockets import connect


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
    ):
        if not api_key:
            raise ValueError("API key cannot be empty.")

        # 基本配置
        self.api_key = api_key
        self.target_language = target_language
        self.audio_enabled = audio_enabled
        self.voice = voice if audio_enabled else "Cherry"
        self.output_device_index = output_device_index  # TTS 输出设备

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
        session = {
            "modalities": ["text", "audio"] if self.audio_enabled else ["text"],
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "translation": {"language": self.target_language},
        }
        if self.audio_enabled and self.voice:
            session["voice"] = self.voice

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

        try:
            # 获取设备支持的采样率
            dev_rate = 44100  # 默认安全值
            dev_name = "Unknown"
            if self.output_device_index is not None:
                dev_info = self.pyaudio_instance.get_device_info_by_index(self.output_device_index)
                dev_rate = int(dev_info.get('defaultSampleRate', 44100))
                dev_name = dev_info.get('name', 'Unknown')
                print(f"[TTS] Using output device: {dev_name} (index={self.output_device_index})")
            else:
                # 获取系统默认输出设备的信息
                default_out = self.pyaudio_instance.get_default_output_device_info()
                dev_rate = int(default_out.get('defaultSampleRate', 44100))
                dev_name = default_out.get('name', 'Unknown')
                print(f"[TTS] Using DEFAULT output device: {dev_name}")
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
            if self.output_device_index is not None:
                open_kwargs["output_device_index"] = self.output_device_index

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
        print(f"[TTS] start_audio_player called, audio_enabled={self.audio_enabled}")
        if not self.audio_enabled:
            print("[TTS] Audio disabled, skipping player start")
            return
        if self.audio_player_thread is None or not self.audio_player_thread.is_alive():
            print("[TTS] Creating and starting audio player thread")
            self.audio_player_thread = threading.Thread(
                target=self._audio_player_task, daemon=True
            )
            self.audio_player_thread.start()
            print("[TTS] Audio player thread started")
        else:
            print("[TTS] Audio player thread already running")

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
        if self.audio_player_thread:
            self.audio_playback_queue.put(None)
            with contextlib.suppress(Exception):
                self.audio_player_thread.join(timeout=1)
            print("[AUDIO] Player stopped.")
        with contextlib.suppress(Exception):
            self.pyaudio_instance.terminate()
        print("[AUDIO] PyAudio terminated.")

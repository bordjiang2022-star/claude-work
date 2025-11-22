# translation_service.py - 翻译服务管理
import os
import sys
import asyncio
from typing import Optional, Callable, Dict
from datetime import datetime

# 添加父目录到路径以导入livetranslate_client
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from livetranslate_client import LiveTranslateClient


class TranslationService:
    """翻译服务管理器 - 管理用户的翻译会话"""

    def __init__(self):
        self.active_sessions: Dict[int, LiveTranslateClient] = {}  # user_id -> client

    async def start_translation(
        self,
        user_id: int,
        api_key: str,
        target_language: str = "en",
        voice: Optional[str] = "Cherry",
        audio_enabled: bool = True,
        input_device_index: Optional[int] = None,
        output_device_index: Optional[int] = None,
        on_text_callback: Optional[Callable] = None
    ) -> bool:
        """
        启动翻译会话

        Args:
            user_id: 用户ID
            api_key: API密钥
            target_language: 目标语言
            voice: TTS声音
            audio_enabled: 是否启用音频
            input_device_index: 输入设备索引（麦克风/虚拟音频）
            output_device_index: 输出设备索引（扬声器，用于TTS播放）
            on_text_callback: 文本接收回调

        Returns:
            bool: 是否成功启动
        """
        # 检查是否已有活动会话
        if user_id in self.active_sessions:
            print(f"[TransService] User {user_id} already has an active session")
            return False

        try:
            # 打印配置信息用于调试
            print(f"[TransService] Starting with config:")
            print(f"  - target_language: {target_language}")
            print(f"  - voice: {voice}")
            print(f"  - audio_enabled: {audio_enabled}")
            print(f"  - input_device_index: {input_device_index}")
            print(f"  - output_device_index: {output_device_index}")

            # 创建客户端
            client = LiveTranslateClient(
                api_key=api_key,
                target_language=target_language,
                voice=voice,
                audio_enabled=audio_enabled,
                input_device_index=input_device_index,
                output_device_index=output_device_index  # TTS 输出设备
            )

            # 连接到服务
            await client.connect()

            # 启动音频播放器
            if audio_enabled:
                client.start_audio_player()

            # 保存会话
            self.active_sessions[user_id] = client

            # 启动音频采集和消息处理
            asyncio.create_task(self._run_translation_session(user_id, client, on_text_callback))

            print(f"[TransService] Started translation session for user {user_id}")
            return True

        except Exception as e:
            print(f"[TransService] Error starting translation: {e}")
            return False

    async def _run_translation_session(
        self,
        user_id: int,
        client: LiveTranslateClient,
        on_text_callback: Optional[Callable]
    ):
        """运行翻译会话的主循环"""
        try:
            # 创建两个任务：消息处理和音频采集
            tasks = [
                asyncio.create_task(client.handle_server_messages(on_text_received=on_text_callback)),
                asyncio.create_task(client.start_microphone_streaming())
            ]
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"[TransService] Session error for user {user_id}: {e}")
        finally:
            # 清理会话
            if user_id in self.active_sessions:
                del self.active_sessions[user_id]

    async def stop_translation(self, user_id: int) -> bool:
        """
        停止翻译会话

        Args:
            user_id: 用户ID

        Returns:
            bool: 是否成功停止
        """
        if user_id not in self.active_sessions:
            print(f"[TransService] No active session for user {user_id}")
            return False

        try:
            client = self.active_sessions[user_id]
            await client.close()
            del self.active_sessions[user_id]
            print(f"[TransService] Stopped translation session for user {user_id}")
            return True
        except Exception as e:
            print(f"[TransService] Error stopping translation: {e}")
            return False

    def is_session_active(self, user_id: int) -> bool:
        """检查用户是否有活动会话"""
        return user_id in self.active_sessions

    async def get_session_status(self, user_id: int) -> dict:
        """获取会话状态"""
        if user_id not in self.active_sessions:
            return {"active": False}

        client = self.active_sessions[user_id]
        return {
            "active": True,
            "connected": client.is_connected,
            "target_language": client.target_language,
            "voice": client.voice,
            "audio_enabled": client.audio_enabled
        }


# 全局翻译服务实例
translation_service = TranslationService()

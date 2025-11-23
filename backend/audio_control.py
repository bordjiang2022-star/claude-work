# audio_control.py - 音频设备切换控制
import os
import sys
import subprocess
import platform
from typing import Optional


class AudioController:
    """音频设备控制器"""

    def __init__(self):
        self.platform = platform.system()
        self.original_device = None
        self.nircmd_path = None
        self.saved_speaker_device = None  # 保存TTS使用的扬声器设备名称

        # 查找nircmd.exe路径
        if self.platform == "Windows":
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "..", "tools", "nircmd.exe"),
                os.path.join(os.getcwd(), "tools", "nircmd.exe"),
                "nircmd.exe"  # 系统PATH中
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    self.nircmd_path = os.path.abspath(path)
                    break

    def _run_nircmd(self, *args) -> bool:
        """运行nircmd命令"""
        if not self.nircmd_path:
            print("[AudioControl] nircmd.exe not found")
            return False

        try:
            cmd = [self.nircmd_path] + list(args)
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception as e:
            print(f"[AudioControl] Error running nircmd: {e}")
            return False

    def switch_to_virtual_cable(self) -> bool:
        """切换到虚拟音频线缆 (VB-Cable)"""
        if self.platform != "Windows":
            print("[AudioControl] Virtual cable switching only supported on Windows")
            return False

        # 使用nircmd设置默认音频设备
        # 语法: nircmd.exe setdefaultsounddevice "CABLE Input" 1
        # 1 = 默认设备, 2 = 通信设备
        success = self._run_nircmd("setdefaultsounddevice", "CABLE Input", "1")

        if success:
            print("[AudioControl] Switched to VB-Cable Input")
        else:
            print("[AudioControl] Failed to switch to VB-Cable")

        return success

    def _extract_short_device_name(self, full_name: str) -> str:
        """
        从PyAudio返回的完整设备名称中提取短名称用于nircmd
        PyAudio会截断设备名称（约31字符），nircmd需要能匹配的名称
        """
        if not full_name:
            return full_name

        # 对于中文扬声器，提取"扬声器"部分
        if "扬声器" in full_name:
            return "扬声器"

        # 对于Realtek设备，使用"Speakers"（Windows默认名称）
        if "realtek" in full_name.lower():
            return "Speakers"

        # 对于耳机
        if "耳机" in full_name:
            return "耳机"
        if "headphones" in full_name.lower():
            return "Headphones"

        # 其他情况，尝试提取括号前的部分
        if "(" in full_name:
            short_name = full_name.split("(")[0].strip()
            if short_name:
                return short_name

        return full_name

    def save_speaker_device(self, device_name: str) -> None:
        """
        保存TTS输出使用的扬声器设备名称
        在Stop时将用于恢复系统默认音频输出
        """
        if device_name:
            self.saved_speaker_device = device_name
            print(f"[AudioControl] Saved speaker device: {device_name}")

    def get_speaker_device_name(self, device_index: Optional[int]) -> Optional[str]:
        """
        根据设备索引获取设备名称
        如果device_index为None，则自动检测真实扬声器
        """
        try:
            import pyaudio
            pa = pyaudio.PyAudio()

            if device_index is not None:
                # 使用指定的设备索引
                info = pa.get_device_info_by_index(device_index)
                device_name = info.get("name", "")
                pa.terminate()
                return device_name
            else:
                # 自动检测真实扬声器（与livetranslate_client.py逻辑一致）
                speaker_keywords = ("Speakers", "Headphones", "Realtek", "耳机", "扬声器")
                virtual_keywords = ("cable", "virtual", "vb-audio")

                for i in range(pa.get_device_count()):
                    info = pa.get_device_info_by_index(i)
                    if int(info.get('maxOutputChannels', 0)) > 0:
                        name = info.get('name', '')
                        name_lower = name.lower()

                        # 跳过虚拟音频线缆
                        if any(vk in name_lower for vk in virtual_keywords):
                            continue

                        # 选择真实扬声器/耳机
                        if any(sk.lower() in name_lower for sk in speaker_keywords):
                            pa.terminate()
                            print(f"[AudioControl] Auto-detected real speaker: {name}")
                            return name

                pa.terminate()
                return None
        except Exception as e:
            print(f"[AudioControl] Error getting device name: {e}")
            return None

    def restore_default_device(self) -> bool:
        """
        恢复默认音频设备（扬声器）
        优先使用保存的TTS设备，否则尝试常见扬声器名称
        """
        if self.platform != "Windows":
            print("[AudioControl] Device restore only supported on Windows")
            return False

        # 首先尝试恢复到保存的TTS设备
        if self.saved_speaker_device:
            # 提取短名称用于nircmd（PyAudio返回的名称被截断，nircmd可能无法匹配）
            short_name = self._extract_short_device_name(self.saved_speaker_device)
            print(f"[AudioControl] Restoring to saved device: {self.saved_speaker_device}")
            print(f"[AudioControl] Using short name for nircmd: {short_name}")

            if self._run_nircmd("setdefaultsounddevice", short_name, "1"):
                print(f"[AudioControl] Successfully restored to {short_name}")
                self.saved_speaker_device = None  # 清除保存的设备
                return True
            else:
                print(f"[AudioControl] Failed to restore to saved device, trying alternatives...")

        # 回退：尝试常见的扬声器设备名称
        speaker_names = [
            "Speakers",
            "扬声器",
            "Realtek",
            "Headphones",
            "耳机"
        ]

        for name in speaker_names:
            if self._run_nircmd("setdefaultsounddevice", name, "1"):
                print(f"[AudioControl] Restored to {name}")
                self.saved_speaker_device = None  # 清除保存的设备
                return True

        print("[AudioControl] Could not restore default audio device")
        return False

    def get_audio_devices(self) -> list:
        """
        获取音频设备列表
        注意: 这个功能需要pyaudio, 在web环境下可能需要调整
        """
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            devices = []

            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                devices.append({
                    "index": i,
                    "name": info.get("name", ""),
                    "max_input_channels": info.get("maxInputChannels", 0),
                    "max_output_channels": info.get("maxOutputChannels", 0),
                    "default_sample_rate": info.get("defaultSampleRate", 0)
                })

            pa.terminate()
            return devices
        except Exception as e:
            print(f"[AudioControl] Error getting audio devices: {e}")
            return []


# 全局音频控制器实例
audio_controller = AudioController()

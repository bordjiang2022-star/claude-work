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

    def restore_default_device(self) -> bool:
        """恢复默认音频设备（扬声器）"""
        if self.platform != "Windows":
            print("[AudioControl] Device restore only supported on Windows")
            return False

        # 尝试常见的扬声器设备名称
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

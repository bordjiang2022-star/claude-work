# main.py — 运行入口（Windows 11 + VB-CABLE）
# 运行前在 PowerShell 设置环境变量后重启终端/IDE：
#   setx DASHSCOPE_API_KEY "sk-xxxxxxxx"

import os
import asyncio
import websockets
import pyaudio

from livetranslate_client import LiveTranslateClient


def print_banner():
    try:
        print(f"websockets version: {websockets.__version__}")
        print(f"websockets file   : {websockets.__file__}")
    except Exception:
        pass
    print("=" * 60)
    print("  基于通义千问 qwen3-livetranslate-flash-realtime")
    print("=" * 60)
    print()


def pick_cable_output_index(keywords=("CABLE Output", "VB-Audio", "Virtual Cable")) -> int | None:
    pa = pyaudio.PyAudio()
    try:
        found = None
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if int(info.get("maxInputChannels", 0)) > 0:
                name = info.get("name", "")
                if "cable" in name.lower() and "output" in name.lower():
                    found = i
                    break
                if any(k.lower() in name.lower() for k in keywords):
                    found = i
        if found is not None:
            print(f"[PickIn ] {found} {pa.get_device_info_by_index(found).get('name')}")
        else:
            print("[PickIn ] 未找到 CABLE Output，请检查虚拟线是否安装/启用")
        return found
    finally:
        pa.terminate()


def pick_speaker_index(keywords=("Speakers", "Headphones", "Realtek", "耳机", "扬声器")) -> int | None:
    """
    选择一个“真实扬声器/耳机”用于播放 TTS，避免把TTS回灌到虚拟线。
    """
    pa = pyaudio.PyAudio()
    try:
        cand = None
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if int(info.get("maxOutputChannels", 0)) > 0:
                name = info.get("name", "")
                if "cable" in name.lower():
                    continue  # 避免把输出设成虚拟线
                if any(k.lower() in name.lower() for k in keywords):
                    cand = i
                    print(f"[PickOut] {i} {name}")
                    break
        if cand is None:
            print("[PickOut] 未找到明显的实体扬声器，TTS 将走系统默认输出设备")
        return cand
    finally:
        pa.terminate()


def get_user_config():
    # 模式
    mode = input("请选择模式:\n1. 语音+文本 [默认] | 2. 仅文本\n请输入选项 (直接回车选择语音+文本): ").strip()
    audio_enabled = (mode != "2")

    # 目标语言
    langs = {
        "1": ("en", "英语"), "2": ("zh", "中文"), "3": ("ru", "俄语"),
        "4": ("fr", "法语"), "5": ("de", "德语"), "6": ("pt", "葡萄牙语"),
        "7": ("es", "西班牙语"), "8": ("it", "意大利语"), "9": ("ko", "韩语"),
        "10": ("ja", "日语"), "11": ("yue", "粤语"),
    }
    ch = input(
        "\n请选择翻译目标语言 (音频+文本 模式):\n"
        "1. 英语 | 2. 中文 | 3. 俄语 | 4. 法语 | 5. 德语 | "
        "6. 葡萄牙语 | 7. 西班牙语 | 8. 意大利语 | 9. 韩语 | 10. 日语 | 11. 粤语\n"
        "请输入选项 (默认取第一个): ").strip()
    target_language = langs.get(ch, langs["1"])[0]

    voice = None
    if audio_enabled:
        v = input(
            "\n请选择语音合成声音:\n"
            "1. Cherry (女声) [默认] | 2. Nofish (男声) | 3. 晴儿 Sunny | 4. 阿珍 Jada | "
            "5. 晓东 Dylan | 6. 李彼得 Peter | 7. 程川 Eric | 8. 阿清 Kiki (粤语)\n"
            "请输入选项 (直接回车选择Cherry): ").strip()
        voice_map = {
            "": "Cherry", "1": "Cherry", "2": "Nofish", "3": "晴儿 Sunny",
            "4": "阿珍 Jada", "5": "晓东 Dylan", "6": "李彼得 Peter",
            "7": "程川 Eric", "8": "阿清 Kiki",
        }
        voice = voice_map.get(v, "Cherry")

    print("\n配置完成:")
    print(f"  - 目标语言: {target_language}")
    print(f"  - 合成声音: {voice if audio_enabled else '（仅文本）'}")
    print()
    return audio_enabled, target_language, voice


async def main():
    print_banner()

    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        print("[ERROR] 请设置环境变量 DASHSCOPE_API_KEY")
        print("  PowerShell:  setx DASHSCOPE_API_KEY \"your_api_key_here\"")
        return

    audio_enabled, target_language, voice = get_user_config()

    # 选择设备
    in_idx = pick_cable_output_index()
    out_idx = pick_speaker_index()

    if in_idx is None:
        print("[FATAL] 未找到 CABLE Output，无法继续。")
        return

    client = LiveTranslateClient(
        api_key=api_key,
        target_language=target_language,
        voice=voice,
        audio_enabled=audio_enabled,
        input_device_index=in_idx,       # 采集 CABLE Output
        output_device_index=out_idx,     # 播放真实扬声器，避免回路
        # 如需微调可传：vad_rms_threshold=1200, vad_silence_ms=350, max_utter_ms=7000,
        #               pre_roll_ms=200, end_silence_ms=250
    )

    def on_text(t: str):
        print(t, end="", flush=True)

    try:
        print("正在连接到翻译服务...")
        await client.connect()
        client.start_audio_player()
        print("\n" + "-" * 60)
        print("连接成功！请对着麦克风说话。")
        print("程序将实时翻译您的语音并播放结果。按 Ctrl+C 退出。")
        print("-" * 60 + "\n")

        tasks = [
            asyncio.create_task(client.handle_server_messages(on_text_received=on_text)),
            asyncio.create_task(client.start_microphone_streaming()),
        ]
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n[CTRL+C] 用户中断。")
    except Exception as e:
        print(f"\n发生严重错误: {e}\n")
    finally:
        print("\n正在清理资源...")
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

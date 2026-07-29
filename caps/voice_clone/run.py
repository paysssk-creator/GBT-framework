# 开发者：自由的风
"""voice_clone/run.py — 语音克隆"""
import sys, json, os, subprocess, base64, wave
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE_DIR = Path.home() / ".gbt" / "voices"
VOICE_DIR.mkdir(parents=True, exist_ok=True)

def do_clone(params):
    text = params.get("text", params.get("speak", "你好，我是GBT小土豆"))
    voice_sample = params.get("sample", params.get("voice", ""))
    output = params.get("output", "")
    if not output:
        output = str(VOICE_DIR / "cloned_output.wav")

    # 尝试Coqui TTS
    try:
        import TTS
        from TTS.api import TTS as CoquiTTS
        tts = CoquiTTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
        tts.tts_to_file(text=text, file_path=output,
                        speaker_wav=voice_sample if voice_sample else None,
                        language="zh" if any('\u4e00' <= c <= '\u9fff' for c in text) else "en")
        return {"ok": True, "cap": "voice_clone", "domain": "媒体域",
                "engine": "Coqui XTTSv2", "text": text[:100], "output": output,
                "size": Path(output).stat().st_size if Path(output).exists() else 0}
    except ImportError:
        pass
    except Exception as e:
        pass

    # 降级: Edge TTS (Windows)
    if sys.platform == "win32":
        try:
            import edge_tts
            import asyncio
            async def _edge():
                communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
                await communicate.save(output)
            asyncio.run(_edge())
            return {"ok": True, "cap": "voice_clone", "engine": "Edge TTS", "output": output}
        except ImportError:
            pass

    return {"ok": False, "error": "语音引擎未安装。pip install TTS edge-tts",
            "note": "Coqui TTS支持语音克隆, Edge TTS支持高质量中文合成"}

def do_speak(params):
    text = params.get("text", "GBT小土豆在线")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        return {"ok": True, "cap": "voice_clone", "action": "speak", "engine": "pyttsx3(离线)"}
    except ImportError:
        return {"ok": False, "error": "pyttsx3未安装"}

HANDLERS = {"clone": do_clone, "speak": do_speak}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "clone"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = HANDLERS.get(action, lambda p: {"ok": False})(params)
    print(json.dumps(r, ensure_ascii=False, default=str))

# 开发者：自由的风
"""audio_capture/run.py — 麦克风录音·环境声音采集
=================================================
桌面域 ready — 录音+保存WAV,静默后台采集环境声音和对话。
"""
import sys, json, os, time, threading, wave
from pathlib import Path
from datetime import datetime

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = Path.home() / ".gbt" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
_recording = {"active": False, "thread": None, "file": None}

def do_record(params):
    duration = params.get("duration", 10)
    try:
        import pyaudio
        import numpy as np
        CHUNK, RATE, CHANNELS = 1024, 44100, 1
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        frames = []
        for _ in range(0, int(RATE/CHUNK*duration)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        stream.stop_stream(); stream.close(); p.terminate()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fpath = str(AUDIO_DIR / f"rec_{ts}.wav")
        with wave.open(fpath, 'wb') as wf:
            wf.setnchannels(CHANNELS); wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(RATE); wf.writeframes(b''.join(frames))
        return {"ok": True, "cap": "audio_capture", "action": "record", "domain": "桌面域",
                "file": fpath, "duration_sec": duration, "size_bytes": os.path.getsize(fpath)}
    except ImportError:
        return {"ok": False, "error": "pyaudio未安装(pip install pyaudio)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_stream(params):
    duration = params.get("duration", 60)
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        frames = []
        start = time.time()
        while time.time() - start < duration:
            frames.append(stream.read(1024, exception_on_overflow=False))
        stream.stop_stream(); stream.close(); p.terminate()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fpath = str(AUDIO_DIR / f"stream_{ts}.wav")
        with wave.open(fpath, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100); wf.writeframes(b''.join(frames))
        return {"ok": True, "cap": "audio_capture", "action": "stream", "file": fpath, "duration": duration}
    except ImportError:
        return {"ok": False, "error": "pyaudio未安装"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

HANDLERS = {"record": do_record, "stream": do_stream}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "record"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))

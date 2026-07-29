# 开发者：自由的风
"""语音播报 — Kokoro-82M + edge-tts + pyttsx3 三层TTS"""
import sys, json, subprocess


def _do_speak_pyttsx3(params):
    """第三层回退: Windows内置TTS引擎"""
    text = params.get('text', '你好，GBT就绪')
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        return {"ok": True, "text": text, "method": "pyttsx3"}
    except ImportError:
        return {"ok": False, "error": "pyttsx3 未安装。pip install pyttsx3"}
    except Exception as e:
        return {"ok": False, "error": f"pyttsx3 失败: {e}"}


def _do_speak_edge_tts(params):
    """第二层: edge-tts Azure自然语音合成"""
    text = params.get('text', '你好，GBT就绪')
    voice = params.get('voice', 'xiaoxiao')

    voice_map = {
        'xiaoxiao': ('zh-CN-XiaoxiaoNeural', ' Xiaoxiao(御姐)'),
        'xiaoyi':   ('zh-CN-XiaoyiNeural',   ' Xiaoyi(甜美)'),
        'yunyang':  ('zh-CN-YunyangNeural',  ' Yunyang(专业)'),
        'yunxi':    ('zh-CN-YunxiNeural',    ' Yunxi(男声)'),
        'female':   ('zh-CN-XiaoxiaoNeural', ' 御姐'),
        'male':     ('zh-CN-YunxiNeural',    ' Yunxi'),
    }
    voice_id, voice_name = voice_map.get(voice, voice_map['xiaoxiao'])

    try:
        import edge_tts, asyncio, os
        async def _spk():
            c = edge_tts.Communicate(text, voice_id, rate='-3%', pitch='+2Hz')
            await c.save('_tmp_voice.mp3')
        asyncio.run(_spk())
        subprocess.run(['cmd','/c','start','_tmp_voice.mp3'], shell=False)
        return {"ok": True, "text": text, "method": "edge_tts", "voice": voice_name}
    except ImportError:
        return {"ok": False, "error": "edge-tts 未安装。pip install edge-tts"}
    except Exception as e:
        return {"ok": False, "error": f"edge-tts 失败: {e}"}


def do_speak_kokoro(params):
    """Kokoro-82M SOTA开源TTS (MIT license, 82M params) → edge-tts 回退

    Kokoro-82M 是2026年排名第一的开源TTS模型:
    - MIT license, 82M参数, 24kHz采样率
    - 支持美式/英式英语、中文、日语、法语、韩语等
    - af_heart 为最佳美式女声预设
    """
    text = params.get('text', '你好，GBT就绪')
    voice = params.get('voice', 'af_heart')
    lang = params.get('lang', 'a')
    speed = params.get('speed', 1.0)

    try:
        from kokoro import KPipeline
        import soundfile as sf
        import numpy as np

        pipeline = KPipeline(lang_code=lang)
        generator = pipeline(text, voice=voice, speed=speed)

        audio_chunks = []
        for _, audio, _ in generator:
            if audio is not None and len(audio) > 0:
                audio_chunks.append(audio)

        if not audio_chunks:
            return {"ok": False, "error": "Kokoro produced no audio output"}

        full_audio = np.concatenate(audio_chunks)
        sf.write('_tmp_voice.wav', full_audio, 24000)
        subprocess.run(['cmd', '/c', 'start', '_tmp_voice.wav'], shell=False)
        return {"ok": True, "text": text, "method": "kokoro", "voice": voice,
                "model": "Kokoro-82M", "sample_rate": 24000}

    except ImportError:
        # kokoro 未安装 → 回退到 edge_tts
        result = _do_speak_edge_tts(params)
        if result.get('ok'):
            result['fallback_from'] = 'kokoro'
        return result

    except Exception as e:
        # kokoro 运行时错误 → 回退到 edge_tts
        result = _do_speak_edge_tts(params)
        if result.get('ok'):
            result['fallback_from'] = 'kokoro'
            result['kokoro_error'] = str(e)
            return result
        return {"ok": False, "error": f"Kokoro 失败({e}), edge-tts 也不可用"}


def _check_kokoro():
    """检测 Kokoro-82M 是否可用"""
    try:
        import kokoro
        version = getattr(kokoro, '__version__', 'unknown')
        return {"available": True, "version": version, "license": "MIT",
                "params": "82M", "sample_rate": 24000,
                "description": "SOTA open-source neural TTS"}
    except ImportError:
        return {"available": False, "reason": "pip install kokoro"}


def _check_edge_tts():
    """检测 edge-tts 是否可用"""
    try:
        import edge_tts
        return {"available": True, "description": "Microsoft Azure neural voices"}
    except ImportError:
        return {"available": False, "reason": "pip install edge-tts"}


def _check_pyttsx3():
    """检测 pyttsx3 是否可用"""
    try:
        import pyttsx3
        return {"available": True, "platform": sys.platform,
                "description": "Windows native SAPI5 TTS"}
    except ImportError:
        return {"available": False, "reason": "pip install pyttsx3"}


def do_list_engines(params):
    """列出所有可用TTS引擎及其状态"""
    kokoro_status = _check_kokoro()
    edge_status = _check_edge_tts()
    pyttsx3_status = _check_pyttsx3()

    chain = []
    if kokoro_status.get('available'):
        chain.append('kokoro')
    if edge_status.get('available'):
        chain.append('edge_tts')
    if pyttsx3_status.get('available'):
        chain.append('pyttsx3')

    return {
        "ok": True,
        "engines": {
            "kokoro": kokoro_status,
            "edge_tts": edge_status,
            "pyttsx3": pyttsx3_status,
        },
        "chain": chain,
        "kokoro_voices": [
            "af_heart", "af_bella", "af_nicole", "af_sarah", "af_sky",
            "am_adam", "am_michael",
            "bf_emma", "bf_isabella", "bm_george", "bm_lewis",
        ],
        "edge_voices": ["xiaoxiao", "xiaoyi", "yunyang", "yunxi", "female", "male"],
    }


def do_speak(params):
    """3-tier TTS链: kokoro → edge_tts → pyttsx3"""
    # 第一层: Kokoro-82M (SOTA开源, MIT license)
    result = do_speak_kokoro(params)
    if result.get('ok'):
        return result

    # 第二层: edge-tts (Microsoft Azure 自然语音)
    result = _do_speak_edge_tts(params)
    if result.get('ok'):
        return result

    # 第三层: Windows内置 pyttsx3 (SAPI5)
    return _do_speak_pyttsx3(params)


handlers = {
    'speak': do_speak,
    'speak_kokoro': do_speak_kokoro,
    'list_engines': do_list_engines,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "speak"
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except Exception:
            params = {}
    h = handlers.get(action,
        lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(handlers.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))

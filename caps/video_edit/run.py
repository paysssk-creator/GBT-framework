# 开发者：自由的风
"""video_edit/run.py — 视频编辑(转录/打包/时间线/渲染/调色/Manim)
=============================
媒体域能力模块 — ready
"""
import sys, json, os, subprocess, shutil, re
from pathlib import Path

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDLERS = {}

# ── helpers ──────────────────────────────────────────────

def _check_binary(name: str) -> bool:
    """Check if a binary is available on PATH."""
    return shutil.which(name) is not None

def _run_ffmpeg(args, timeout=300):
    """Run ffmpeg with args, return structured result."""
    if not _check_binary("ffmpeg"):
        return {"ok": False, "error": "ffmpeg 未安装。请安装: choco install ffmpeg / apt install ffmpeg"}
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return {
            "ok": r.returncode == 0,
            "returncode": r.returncode,
            "stderr": r.stderr.strip()[:1000] if r.returncode != 0 else ""
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"ffmpeg 超时({timeout}s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

# ── handlers ─────────────────────────────────────────────

def do_edit(params):
    """编辑视频 — 裁剪/拼接/变速/截图"""
    action = params.get("sub_action", params.get("op", "trim"))
    inputs = params.get("inputs", params.get("files", []))
    output = params.get("output", params.get("out", "output.mp4"))

    if not inputs:
        return {"ok": False, "error": "缺少 inputs/files 参数", "cap": "video_edit", "action": "edit"}

    if not _check_binary("ffmpeg"):
        return {"ok": False, "error": "ffmpeg 未安装。请安装: choco install ffmpeg / apt install ffmpeg",
                "cap": "video_edit", "action": "edit"}

    args = []

    # ── 裁剪: trim start duration ──
    if action == "trim":
        start = params.get("start", params.get("ss", "0"))
        duration = params.get("duration", params.get("t", None))
        end = params.get("end", params.get("to", None))
        args += ["-ss", str(start)]
        if len(inputs) >= 1:
            args += ["-i", str(inputs[0])]
        if duration:
            args += ["-t", str(duration)]
        elif end:
            args += ["-to", str(end)]
        # copy codecs for speed unless re-encode requested
        if params.get("reencode"):
            args += ["-c:v", params.get("codec", "libx264"), "-preset", "fast"]
        else:
            args += ["-c", "copy"]
        args += ["-avoid_negative_ts", "make_zero", str(output)]

    # ── 拼接: concat file list ──
    elif action == "concat":
        # Write concat list for filter method first
        # Simpler: use concat demuxer via temp file
        concat_list_path = params.get("concat_list", None)
        if concat_list_path and os.path.exists(concat_list_path):
            args += ["-f", "concat", "-safe", "0", "-i", str(concat_list_path), "-c", "copy", str(output)]
        else:
            # Build concat filter from inputs
            filter_parts = []
            for i, f in enumerate(inputs):
                args += ["-i", str(f)]
                filter_parts.append(f"[{i}:v:0][{i}:a:0]")
            filter_str = "".join(filter_parts) + f"concat=n={len(inputs)}:v=1:a=1[outv][outa]"
            args += ["-filter_complex", filter_str, "-map", "[outv]", "-map", "[outa]", str(output)]

    # ── 变速: speed factor ──
    elif action == "speed":
        speed = float(params.get("speed", 1.0))
        if len(inputs) >= 1:
            args += ["-i", str(inputs[0])]
        # setpts for video, atempo for audio
        v_pts = 1.0 / speed
        a_tempo = speed
        # atempo must be in [0.5, 2.0]; chain if needed
        atempo_filters = []
        remaining = a_tempo
        while remaining > 2.0:
            atempo_filters.append("atempo=2.0")
            remaining /= 2.0
        while remaining < 0.5:
            atempo_filters.append("atempo=0.5")
            remaining /= 0.5
        atempo_filters.append(f"atempo={remaining:.6f}")
        atempo_str = ",".join(atempo_filters)
        filter_str = f"[0:v]setpts={v_pts:.6f}*PTS[v];[0:a]{atempo_str}[a]"
        args += ["-filter_complex", filter_str, "-map", "[v]", "-map", "[a]", str(output)]

    # ── 截图: extract frame ──
    elif action == "screenshot":
        at_time = params.get("at", params.get("ss", "0"))
        if len(inputs) >= 1:
            args += ["-ss", str(at_time), "-i", str(inputs[0])]
        out_ext = os.path.splitext(output)[1].lower()
        if out_ext not in (".png", ".jpg", ".jpeg", ".bmp"):
            output = output.rsplit(".", 1)[0] + ".png" if "." in output else output + ".png"
        args += ["-frames:v", "1", str(output)]

    else:
        return {"ok": False, "error": f"未知子操作: {action}", "cap": "video_edit", "action": "edit",
                "supported": ["trim", "concat", "speed", "screenshot"]}

    result = _run_ffmpeg(args)
    result["cap"] = "video_edit"
    result["action"] = "edit"
    result["sub_action"] = action
    if result["ok"]:
        result["output"] = output
        result["note"] = f"GBT邻域视觉: 媒体域·video_edit·edit·{action}"
    return result


def do_transcribe(params):
    """转录 — whisper 语音转文字"""
    audio_path = params.get("audio", params.get("input", params.get("file", "")))
    language = params.get("language", params.get("lang", "zh"))
    model = params.get("model", "base")
    output = params.get("output", None)

    if not audio_path or not os.path.exists(audio_path):
        return {"ok": False, "error": f"音频文件不存在: {audio_path}",
                "cap": "video_edit", "action": "transcribe"}

    # Try whisper CLI first
    if _check_binary("whisper"):
        args = ["whisper", audio_path, "--model", model, "--language", language]
        if output:
            args += ["--output_dir", str(Path(output).parent), "--output_format", "json"]
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=600)
            if r.returncode == 0:
                import glob
                # whisper outputs to same dir as input by default; find the json/txt result
                base = os.path.splitext(audio_path)[0]
                result_files = []
                for ext in [".json", ".txt", ".srt", ".vtt"]:
                    for f in [base + ext, base + "." + model + ext]:
                        if os.path.exists(f):
                            result_files.append(f)
                text = ""
                txt_path = base + ".txt"
                if os.path.exists(txt_path):
                    text = Path(txt_path).read_text(encoding="utf-8", errors="replace")[:5000]
                return {"ok": True, "cap": "video_edit", "action": "transcribe",
                        "text": text, "result_files": result_files,
                        "note": f"GBT邻域视觉: 媒体域·video_edit·transcribe (whisper {model})"}
            else:
                return {"ok": False, "error": r.stderr.strip()[:500],
                        "cap": "video_edit", "action": "transcribe"}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "whisper 转录超时(600s)",
                    "cap": "video_edit", "action": "transcribe"}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200],
                    "cap": "video_edit", "action": "transcribe"}

    # Try Python whisper module
    try:
        import whisper as _whisper_mod
    except ImportError:
        pass
    else:
        try:
            m = _whisper_mod.load_model(model)
            result = m.transcribe(audio_path, language=language)
            text = result.get("text", "")[:5000]
            segments = [{"start": s["start"], "end": s["end"], "text": s["text"]}
                        for s in result.get("segments", [])]
            return {"ok": True, "cap": "video_edit", "action": "transcribe",
                    "text": text, "segments": segments,
                    "note": f"GBT邻域视觉: 媒体域·video_edit·transcribe (whisper-py {model})"}
        except Exception as e:
            return {"ok": False, "error": f"whisper-py 转录失败: {str(e)[:200]}",
                    "cap": "video_edit", "action": "transcribe"}

    # Whisper not installed — return instructive error
    return {"ok": False, "cap": "video_edit", "action": "transcribe",
            "error": "whisper 未安装。安装方式:\n"
                     "  pip install openai-whisper\n"
                     "  或 pip install whisper (OpenAI CLI)",
            "install_hint": "pip install openai-whisper",
            "note": "GBT邻域视觉: 媒体域·video_edit·transcribe (需要安装whisper)"}


def do_render(params):
    """渲染 — 视频合成/导出"""
    inputs = params.get("inputs", params.get("files", params.get("sources", [])))
    output = params.get("output", params.get("out", "rendered.mp4"))
    preset = params.get("preset", "medium")
    codec = params.get("codec", params.get("vcodec", "libx264"))
    crf = params.get("crf", params.get("quality", 23))
    width = params.get("width", None)
    height = params.get("height", None)
    fps = params.get("fps", None)
    bitrate = params.get("bitrate", None)
    audio_codec = params.get("acodec", params.get("audio_codec", "aac"))
    audio_bitrate = params.get("audio_bitrate", "128k")
    filter_complex = params.get("filter_complex", params.get("vf", None))

    if not _check_binary("ffmpeg"):
        return {"ok": False, "error": "ffmpeg 未安装。请安装: choco install ffmpeg / apt install ffmpeg",
                "cap": "video_edit", "action": "render"}

    args = []
    for src in inputs:
        args += ["-i", str(src)]

    # video codec
    args += ["-c:v", codec, "-preset", preset, "-crf", str(crf)]

    # resolution
    if width and height:
        args += ["-s", f"{width}x{height}"]
    elif width:
        args += ["-vf", f"scale={width}:-1"]
    elif height:
        args += ["-vf", f"scale=-1:{height}"]

    # fps
    if fps:
        args += ["-r", str(fps)]

    # bitrate
    if bitrate:
        args += ["-b:v", str(bitrate)]

    # filter complex
    if filter_complex:
        args += ["-filter_complex", str(filter_complex)]

    # audio
    args += ["-c:a", audio_codec, "-b:a", str(audio_bitrate)]

    # muxing options
    args += ["-movflags", "+faststart"]

    args += [str(output)]

    result = _run_ffmpeg(args, timeout=params.get("timeout", 600))
    result["cap"] = "video_edit"
    result["action"] = "render"
    if result["ok"]:
        result["output"] = output
        result["note"] = "GBT邻域视觉: 媒体域·video_edit·render"
    return result


def do_timeline(params):
    """时间线编辑 — 生成时间线/剪辑序列JSON"""
    clips = params.get("clips", params.get("segments", []))
    total_duration = params.get("duration", params.get("total_duration", 0))
    fps = params.get("fps", 30)
    output_path = params.get("output", params.get("out", None))

    # If no clips given, build a placeholder timeline
    if not clips:
        if total_duration > 0:
            clips = [{
                "id": 1, "start": 0, "end": total_duration,
                "label": "全段", "type": "raw"
            }]
        else:
            return {"ok": False, "error": "缺少 clips 或 duration 参数",
                    "cap": "video_edit", "action": "timeline"}

    timeline = {
        "fps": fps,
        "total_duration": total_duration or max((c.get("end", 0) for c in clips), default=0),
        "track_count": params.get("tracks", 1),
        "clips": [],
        "transitions": params.get("transitions", []),
        "markers": params.get("markers", [])
    }

    for i, clip in enumerate(clips):
        entry = {
            "id": clip.get("id", i + 1),
            "track": clip.get("track", 0),
            "start": clip.get("start", 0),
            "end": clip.get("end", clip.get("start", 0) + clip.get("duration", 0)),
            "duration": clip.get("duration", clip.get("end", 0) - clip.get("start", 0)),
            "source": clip.get("source", clip.get("file", "")),
            "label": clip.get("label", f"片段{i+1}"),
            "type": clip.get("type", "video"),
            "muted": clip.get("muted", False),
            "speed": clip.get("speed", 1.0),
            "effects": clip.get("effects", []),
            "frame_start": clip.get("frame_start", int(clip.get("start", 0) * fps)),
            "frame_end": clip.get("frame_end", int(clip.get("end", 0) * fps))
        }
        entry["duration"] = entry["end"] - entry["start"]
        timeline["clips"].append(entry)

    # Update total from clips if not explicit
    if not timeline["total_duration"] and timeline["clips"]:
        timeline["total_duration"] = max(c["end"] for c in timeline["clips"])

    result = {
        "ok": True,
        "cap": "video_edit",
        "action": "timeline",
        "timeline": timeline,
        "clip_count": len(timeline["clips"]),
        "note": "GBT邻域视觉: 媒体域·video_edit·timeline"
    }

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
        result["saved_to"] = output_path

    return result


# ── registration ─────────────────────────────────────────

HANDLERS = {
    "edit": do_edit,
    "transcribe": do_transcribe,
    "render": do_render,
    "timeline": do_timeline,
}


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "default"
    params_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(params_str)
    except Exception:
        params = {}
    handler = HANDLERS.get(action)
    if handler:
        result = handler(params)
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        print(json.dumps({"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())}, ensure_ascii=False))

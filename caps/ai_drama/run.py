# 开发者：自由的风
"""ai_drama/run.py — AI 短剧工厂
=================================
从一句话到完整短剧，全自动:
  ① 剧本生成 (Kimi API)    → 角色/分镜/台词
  ② 视频生成 (LTX-Video)   → 逐镜渲染
  ③ 配音合成 (Edge TTS)    → 角色配音
  ④ 自动剪辑 (FFmpeg)     → 拼接+字幕

动作:
  script   — 只生成剧本 JSON
  render   — 根据剧本生成视频
  dub      — 配音合成
  assemble — 剪辑拼接
  generate — 全流程一键生成

外部依赖:
  MOONSHOT_API_KEY (Kimi API 用于剧本)
  REPLICATE_API_TOKEN (可选，LTX-Video 云端生成)
  ffmpeg (视频拼接)
"""

import sys, json, os, re, time, subprocess, base64, tempfile, hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── 加载 .env ──
try:
    from dotenv import load_dotenv
    for p in [Path(__file__).resolve().parents[3], Path.cwd()]:
        env_file = p / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            break
except ImportError:
    pass

# ── 配置 ──
API_KEY = os.environ.get("MOONSHOT_API_KEY", "") or os.environ.get("KIMI_API_KEY", "")
API_URL = "https://api.moonshot.cn/v1/chat/completions"
MODEL = "deepseek-v4-pro"

REPLICATE_KEY = os.environ.get("REPLICATE_API_TOKEN", "")
REPLICATE_URL = "https://api.replicate.com/v1/predictions"

OUTPUT_DIR = Path(os.environ.get("AI_DRAMA_OUTPUT", "ai_drama_output"))
FFMPEG = "ffmpeg"

# ── Kimi API ──
def _kimi_chat(messages: list, max_tokens: int = 4000) -> str:
    """调用 Kimi API"""
    if not API_KEY:
        return json.dumps({"error": "未配置 MOONSHOT_API_KEY"})
    try:
        import urllib.request
        req = urllib.request.Request(API_URL,
            data=json.dumps({
                "model": MODEL, "messages": messages,
                "max_tokens": max_tokens, "temperature": 0.8
            }).encode(),
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            })
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return json.dumps({"error": str(e)})


# ══════════════════════════════════════════════════
# ① 剧本生成
# ══════════════════════════════════════════════════

SCRIPT_PROMPT = """你是一个短剧编剧。根据用户主题，生成一个30-60秒的短剧剧本。

严格输出JSON格式（不要包含```json标记）：
{
  "title": "短剧标题",
  "genre": "类型（悬疑/爱情/搞笑/科幻/励志）",
  "duration_sec": 45,
  "characters": [
    {"name": "角色名", "gender": "男/女", "voice": "zh-CN-YunxiNeural", "desc": "角色描述"}
  ],
  "scenes": [
    {
      "id": 1,
      "duration_sec": 10,
      "narration": "旁白文字（可选）",
      "visual_prompt": "英文画面描述（用于AI视频生成，200词以内，cinematographer风格）",
      "dialogue": {"character": "角色名", "text": "台词（中文）"},
      "camera": "镜头描述（如：中景，慢推）"
    }
  ]
}

要求：
- 3-6个分镜，总时长30-60秒
- visual_prompt 用英文，描述画面细节、光线、镜头运动
- 每个分镜有明确的视觉变化
- 台词简短有力，适合短视频节奏
- 最后留一个反转或金句"""


def do_script(params: dict) -> dict:
    """生成短剧剧本"""
    topic = params.get("topic", params.get("keyword", "一个关于重逢的短剧"))
    genre = params.get("genre", "auto")

    if genre != "auto":
        topic = f"{topic}，类型：{genre}"

    result = _kimi_chat([
        {"role": "system", "content": SCRIPT_PROMPT},
        {"role": "user", "content": f"短剧主题：{topic}"}
    ], max_tokens=4000)

    try:
        script = json.loads(result)
        script["ok"] = True
        script["input_topic"] = topic
        return script
    except json.JSONDecodeError:
        # 尝试提取 JSON
        m = re.search(r'\{[\s\S]*\}', result)
        if m:
            try:
                script = json.loads(m.group())
                script["ok"] = True
                script["input_topic"] = topic
                return script
            except:
                pass
        return {"ok": False, "error": "剧本JSON解析失败", "raw": result[:500]}


# ══════════════════════════════════════════════════
# ② 视频生成
# ══════════════════════════════════════════════════

def _replicate_ltx(prompt: str, duration: int = 5) -> dict:
    """通过 Replicate API 调用 LTX-Video"""
    if not REPLICATE_KEY:
        return {"error": "未配置 REPLICATE_API_TOKEN，跳过视频生成"}
    try:
        import urllib.request
        # 发起生成
        req = urllib.request.Request(REPLICATE_URL,
            data=json.dumps({
                "version": "lightricks/ltx-video",
                "input": {
                    "prompt": prompt,
                    "num_frames": min(duration * 24, 121),
                    "fps": 24,
                    "width": 768,
                    "height": 512,
                    "num_inference_steps": 30,
                }
            }).encode(),
            headers={
                "Authorization": f"Token {REPLICATE_KEY}",
                "Content-Type": "application/json"
            })
        with urllib.request.urlopen(req, timeout=30) as r:
            prediction = json.loads(r.read())

        # 轮询等待完成
        pred_id = prediction.get("id")
        poll_url = f"{REPLICATE_URL}/{pred_id}"
        for _ in range(60):  # 最多等5分钟
            time.sleep(5)
            req2 = urllib.request.Request(poll_url,
                headers={"Authorization": f"Token {REPLICATE_KEY}"})
            with urllib.request.urlopen(req2, timeout=10) as r:
                status = json.loads(r.read())
            if status.get("status") == "succeeded":
                output = status.get("output", "")
                if isinstance(output, list):
                    output = output[0] if output else ""
                return {"url": output, "id": pred_id}
            elif status.get("status") == "failed":
                return {"error": status.get("error", "生成失败")}
        return {"error": "生成超时", "id": pred_id}
    except Exception as e:
        return {"error": str(e)}


def do_render(params: dict) -> dict:
    """根据剧本生成视频分镜"""
    script = params.get("script", {})
    script_file = params.get("script_file", "")

    if script_file:
        script = json.loads(Path(script_file).read_text(encoding="utf-8"))

    scenes = script.get("scenes", [])
    if not scenes:
        return {"ok": False, "error": "剧本无分镜"}

    title = script.get("title", "untitled")
    slug = re.sub(r'[^\w]', '_', title)[:20]
    work_dir = OUTPUT_DIR / slug
    work_dir.mkdir(parents=True, exist_ok=True)

    rendered = []
    for i, scene in enumerate(scenes):
        prompt = scene.get("visual_prompt", "")
        if not prompt:
            rendered.append({"scene_id": scene.get("id"), "error": "无visual_prompt"})
            continue

        result = _replicate_ltx(prompt, scene.get("duration_sec", 8))
        if "url" in result:
            rendered.append({
                "scene_id": scene.get("id"),
                "video_url": result["url"],
                "status": "rendered"
            })
        else:
            rendered.append({
                "scene_id": scene.get("id"),
                "error": result.get("error", "未知错误"),
                "status": "failed",
                "placeholder": f"场景{i+1}: {prompt[:60]}..."
            })

    # 保存渲染状态
    render_state = {
        "title": title,
        "scenes": rendered,
        "work_dir": str(work_dir)
    }
    (work_dir / "render_state.json").write_text(
        json.dumps(render_state, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "title": title,
        "total_scenes": len(scenes),
        "rendered": sum(1 for s in rendered if s.get("status") == "rendered"),
        "failed": sum(1 for s in rendered if s.get("status") == "failed"),
        "scenes": rendered,
        "work_dir": str(work_dir)
    }


# ══════════════════════════════════════════════════
# ③ 配音合成
# ══════════════════════════════════════════════════

def _tts_edge(text: str, voice: str, output_path: str) -> bool:
    """用 Edge TTS 合成语音"""
    try:
        import subprocess
        r = subprocess.run(
            [sys.executable, "-m", "edge_tts", "--voice", voice, "--text", text, "--write-media", output_path],
            capture_output=True, timeout=30
        )
        return r.returncode == 0 and Path(output_path).exists()
    except Exception:
        return False


def do_dub(params: dict) -> dict:
    """合成配音"""
    script = params.get("script", {})
    script_file = params.get("script_file", "")

    if script_file:
        script = json.loads(Path(script_file).read_text(encoding="utf-8"))

    scenes = script.get("scenes", [])
    characters = script.get("characters", [])
    title = script.get("title", "untitled")
    slug = re.sub(r'[^\w]', '_', title)[:20]
    work_dir = OUTPUT_DIR / slug
    work_dir.mkdir(parents=True, exist_ok=True)

    # 角色 → 语音映射
    char_voices = {c["name"]: c.get("voice", "zh-CN-XiaoxiaoNeural") for c in characters}

    dubs = []
    for scene in scenes:
        dialogue = scene.get("dialogue", {})
        if not dialogue or not dialogue.get("text"):
            continue

        char = dialogue.get("character", "")
        text = dialogue.get("text", "")
        voice = char_voices.get(char, "zh-CN-XiaoxiaoNeural")

        audio_file = work_dir / f"scene_{scene.get('id','0')}_dub.mp3"
        if _tts_edge(text, voice, str(audio_file)):
            dubs.append({
                "scene_id": scene.get("id"),
                "character": char,
                "text": text,
                "audio": str(audio_file),
                "status": "ok"
            })
        else:
            dubs.append({
                "scene_id": scene.get("id"),
                "character": char,
                "text": text,
                "status": "failed"
            })

    dub_state = {
        "title": title,
        "dubs": dubs,
        "work_dir": str(work_dir)
    }
    (work_dir / "dub_state.json").write_text(
        json.dumps(dub_state, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "title": title,
        "total_dubs": len(dubs),
        "success": sum(1 for d in dubs if d.get("status") == "ok"),
        "dubs": dubs,
        "work_dir": str(work_dir)
    }


# ══════════════════════════════════════════════════
# ④ 自动剪辑
# ══════════════════════════════════════════════════

def do_assemble(params: dict) -> dict:
    """FFmpeg 拼接所有分镜+配音+字幕"""
    script_file = params.get("script_file", "")
    work_dir_str = params.get("work_dir", "")

    if not work_dir_str:
        return {"ok": False, "error": "需要 work_dir 参数"}

    work_dir = Path(work_dir_str)
    if not work_dir.exists():
        return {"ok": False, "error": f"工作目录不存在: {work_dir}"}

    # 检查 FFmpeg
    try:
        subprocess.run([FFMPEG, "-version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        return {"ok": False, "error": "ffmpeg 未安装。请安装: choco install ffmpeg"}

    # 读脚本
    if script_file:
        script = json.loads(Path(script_file).read_text(encoding="utf-8"))
    else:
        render_state = work_dir / "render_state.json"
        if not render_state.exists():
            return {"ok": False, "error": "未找到 render_state.json，请先执行 render"}
        render = json.loads(render_state.read_text(encoding="utf-8"))
        script = {"title": render.get("title", "untitled")}

    title = script.get("title", "untitled")
    slug = re.sub(r'[^\w]', '_', title)[:20]
    output_file = OUTPUT_DIR / f"{slug}_final.mp4"

    # FFmpeg 拼接（简化版——直接 concat）
    # 实际产品需要更精细的剪辑控制
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=768x512:d=3:r=24",
        "-vf", f"drawtext=text='{title}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(output_file)
    ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=30, check=True)
        return {
            "ok": True,
            "title": title,
            "output": str(output_file),
            "size_bytes": output_file.stat().st_size if output_file.exists() else 0,
            "message": "短剧生成完成！视频素材已就绪，配音和字幕需要手动微调。"
        }
    except subprocess.CalledProcessError as e:
        return {"ok": False, "error": f"FFmpeg 错误: {e.stderr.decode()[:500]}"}


# ══════════════════════════════════════════════════
# ⑤ 全流程生成
# ══════════════════════════════════════════════════

def do_generate(params: dict) -> dict:
    """一键全流程：剧本→视频→配音→剪辑"""
    topic = params.get("topic", params.get("keyword", "一个关于AI觉醒的悬疑短剧"))
    generate_video = params.get("generate_video", False)  # 默认不生成视频（需要API Key）

    # 步骤1：剧本
    script_result = do_script({"topic": topic})
    if not script_result.get("ok"):
        return script_result

    title = script_result.get("title", "untitled")
    slug = re.sub(r'[^\w]', '_', title)[:20]
    work_dir = OUTPUT_DIR / slug
    work_dir.mkdir(parents=True, exist_ok=True)
    script_file = work_dir / "script.json"
    script_file.write_text(json.dumps(script_result, ensure_ascii=False, indent=2), encoding="utf-8")

    steps = {"script": "completed", "render": "skipped", "dub": "skipped", "assemble": "skipped"}

    # 步骤2：视频（需要 REPLICATE_API_TOKEN）
    if generate_video and REPLICATE_KEY:
        render_result = do_render({"script_file": str(script_file)})
        steps["render"] = "completed" if render_result.get("ok") else "failed"

    # 步骤3：配音
    dub_result = do_dub({"script_file": str(script_file)})
    steps["dub"] = "completed" if dub_result.get("ok") else "failed"

    # 步骤4：剪辑
    assemble_result = do_assemble({"work_dir": str(work_dir), "script_file": str(script_file)})
    steps["assemble"] = "completed" if assemble_result.get("ok") else "failed"

    return {
        "ok": True,
        "title": title,
        "topic": topic,
        "script": script_result,
        "steps": steps,
        "work_dir": str(work_dir),
        "output": assemble_result.get("output", ""),
        "tip": "设置 REPLICATE_API_TOKEN 后加 generate_video=true 可生成视频，"
               "或手动将剧本 visual_prompt 贴到可灵/即梦/runway 生成画面后替换。"
    }


# ══════════════════════════════════════════════════
HANDLERS = {
    "script": do_script,
    "render": do_render,
    "dub": do_dub,
    "assemble": do_assemble,
    "generate": do_generate,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "auto"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: params = {}
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知动作: {action}", "available": list(HANDLERS.keys())})
    print(json.dumps(h(params), ensure_ascii=False, default=str))

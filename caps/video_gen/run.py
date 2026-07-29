# 开发者：自由的风
"""video_gen/run.py — AI视频生成(Replicate LTX-Video)
=====================================================
媒体域 core — 一句话生成视频。支持8种风格模式。
"""
import sys, json, os, urllib.request, urllib.error, time

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPLICATE_KEY = os.environ.get("REPLICATE_API_TOKEN", "")

VIDEO_MODES = {
    "cinematic": {"negative_prompt": "blurry, low quality, cartoon", "guidance_scale": 7.0},
    "anime": {"negative_prompt": "realistic, photographic", "guidance_scale": 8.0},
    "realistic": {"negative_prompt": "cartoon, anime, blurry", "guidance_scale": 6.0},
    "artistic": {"negative_prompt": "boring, plain", "guidance_scale": 8.5},
    "scifi": {"negative_prompt": "medieval, fantasy", "guidance_scale": 7.5},
    "nature": {"negative_prompt": "urban, indoor, artificial", "guidance_scale": 6.5},
    "abstract": {"negative_prompt": "realistic, photographic", "guidance_scale": 9.0},
    "documentary": {"negative_prompt": "fiction, fantasy, cartoon", "guidance_scale": 6.0},
}

def _call_replicate(prompt, mode="cinematic", duration=3):
    if not REPLICATE_KEY:
        return None, "REPLICATE_API_TOKEN未设置"
    mode_config = VIDEO_MODES.get(mode, VIDEO_MODES["cinematic"])
    body = json.dumps({
        "version": "ltx-video",
        "input": {
            "prompt": prompt,
            "negative_prompt": mode_config["negative_prompt"],
            "guidance_scale": mode_config["guidance_scale"],
            "num_frames": min(duration * 24, 121),
            "fps": 24,
            "width": 768, "height": 512,
        }
    }).encode()
    try:
        req = urllib.request.Request("https://api.replicate.com/v1/predictions", data=body,
            headers={"Authorization": f"Bearer {REPLICATE_KEY}", "Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        return resp, None
    except Exception as e:
        return None, str(e)[:200]

def do_generate(params):
    prompt = params.get("prompt", params.get("text", ""))
    if not prompt:
        return {"ok": False, "error": "缺少prompt"}
    mode = params.get("mode", "cinematic")
    duration = params.get("duration", 5)

    prediction, err = _call_replicate(prompt, mode, duration)
    if err:
        return {"ok": False, "error": err,
                "available_modes": list(VIDEO_MODES.keys())}

    return {
        "ok": True,
        "cap": "video_gen",
        "action": "generate",
        "domain": "媒体域",
        "prompt": prompt[:200],
        "mode": mode,
        "duration_sec": duration,
        "prediction_id": prediction.get("id", ""),
        "status": prediction.get("status", "processing"),
        "poll_url": prediction.get("urls", {}).get("get", ""),
        "note": "视频生成中，使用prediction_id查询进度",
    }

def do_modes(params):
    """列出8种风格模式"""
    return {"ok": True, "cap": "video_gen", "action": "modes",
            "modes": {name: cfg["negative_prompt"] for name, cfg in VIDEO_MODES.items()},
            "total": len(VIDEO_MODES)}

VIDEO_MODES["hunyuan_realistic"] = {"negative_prompt": "blurry, low quality, cartoon, anime", "guidance_scale": 6.5}
VIDEO_MODES["hunyuan_fast"] = {"negative_prompt": "blurry, distorted", "guidance_scale": 5.0}

def do_hunyuan_local(params):
    """HunyuanVideo本地生成 — SOTA开源视频模型 (13B, Apache 2.0)
    需要: pip install diffusers transformers accelerate torch
    显存: 建议24GB+ VRAM
    """
    prompt = params.get("prompt", params.get("text", ""))
    if not prompt:
        return {"ok": False, "error": "缺少prompt"}
    duration = params.get("duration", 5)
    mode = params.get("mode", "hunyuan_realistic")
    cfg = VIDEO_MODES.get(mode, VIDEO_MODES["hunyuan_realistic"])
    
    # 检查本地依赖
    try:
        import torch
        if not torch.cuda.is_available():
            return {"ok": False, "error": "HunyuanVideo需要CUDA GPU",
                    "fallback": "使用 generate 动作 (Replicate云端)", "suggestion": "pip install diffusers transformers accelerate torch"}
    except ImportError:
        return {"ok": False, "error": "PyTorch未安装",
                "install": "pip install diffusers transformers accelerate torch", "fallback": "使用 generate 动作"}
    
    # 生成完整本地运行脚本
    script = f'''# HunyuanVideo本地生成脚本 (Apache 2.0)
from diffusers import HunyuanVideoPipeline
import torch

pipe = HunyuanVideoPipeline.from_pretrained(
    "hunyuanvideo-community/HunyuanVideo",
    torch_dtype=torch.bfloat16
)
pipe.enable_model_cpu_offload()
pipe.vae.enable_tiling()

output = pipe(
    prompt="{prompt}",
    negative_prompt="{cfg['negative_prompt']}",
    num_frames={min(duration*24, 121)},
    fps=24,
    width=768, height=512,
    guidance_scale={cfg['guidance_scale']},
    num_inference_steps=30,
).frames[0]

from pathlib import Path
out = Path.home() / ".gbt" / "videos" / "hunyuan_output.mp4"
out.parent.mkdir(parents=True, exist_ok=True)
import imageio; imageio.mimsave(str(out), output, fps=24)
print(f"✅ 视频已保存: {{out}}")
'''
    return {"ok": True, "cap": "video_gen", "action": "hunyuan_local",
            "engine": "HunyuanVideo 13B (Apache 2.0)", "mode": mode,
            "script": script, "estimated_vram": "24GB",
            "note": "SOTA 2026开源视频模型, 本地运行无需API key",
            "engines": {"replicate_cloud": "LTX-Video (默认)", "hunyuan_local": "HunyuanVideo 13B (本地)", "both": "双引擎自动回退"}}

HANDLERS = {"generate": do_generate, "modes": do_modes, "hunyuan_local": do_hunyuan_local}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "modes"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    handler = HANDLERS.get(action)
    result = handler(params) if handler else {"ok": False, "error": f"未知:{action}"}
    print(json.dumps(result, ensure_ascii=False, default=str))

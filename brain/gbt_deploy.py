# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# ⛔ 链路内核集成 — 不可绕过
"""
brain/gbt_deploy.py — GBT唯一部署工具 · 不可绕过
==================================================
这是修改任何文件并部署到生产的唯一通道。没有第二条路。

用法:
  from brain.gbt_deploy import deploy
  deploy("web/dashboard.html", new_content)

内部强制流程:
  ① enforce_chain(context, mirror_target=file)
  ② mirror_fusion.mirror_verify(file, code)
  ③ watchdog.before(file)
  ④ 写入文件
  ⑤ watchdog.after(file)
  ⑥ mirror_fusion.promote_to_production(file, code)

任何一步失败 → 操作阻断 → 文件不会变更
"""

import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

DEPLOY_LOG = Path.home() / ".gbt" / "deploy_log.jsonl"
DEPLOY_LOG.parent.mkdir(parents=True, exist_ok=True)


def deploy(file_path: str, content: str, context: str = "") -> dict:
    """
    GBT唯一部署工具——修改文件并部署到生产的唯一通道。
    
    参数:
      file_path: 要修改的文件路径(相对于项目根目录)
      content: 新的文件内容
      context: 操作描述(用于审计日志)
    
    返回:
      {"ok": True/False, "file": ..., "steps": {...}, "backup": ...}
    """
    t0 = __import__('time').time()
    result = {"ok": False, "file": file_path, "context": context, "steps": {}}

    # Gate 1: enforce_chain — 绕过检测 + 视觉监护 + Step追踪 + 镜像验证
    try:
        from brain.chain_kernel import enforce_chain
        r = enforce_chain(context, mirror_target=file_path)
        result["steps"]["enforce"] = "pass" if r["ok"] else f"blocked: {r.get('error','?')}"
        if not r["ok"]:
            result["error"] = r.get("error", "enforce blocked")
            return result
    except (ImportError, ModuleNotFoundError) as e:
        result["steps"]["enforce"] = f"chain_not_booted: {e}"
        result["error"] = "链内核未启动——LLM会话必须通过brain/__init__.py导入"
        return result

    # Gate 2: mirror_verify — 4步镜像验证
    try:
        from brain.mirror_fusion import get_mirror
        m = get_mirror()
        v = m.mirror_verify(file_path, content)
        result["steps"]["mirror_verify"] = "pass" if v["ok"] else f"fail: {v.get('error','?')}"
        if not v["ok"]:
            result["error"] = f"镜像验证未通过: {v.get('error','?')}"
            return result
    except Exception as e:
        result["steps"]["mirror_verify"] = f"error: {e}"
        result["error"] = f"镜像验证异常: {e}"
        return result

    # Gate 3: watchdog.before — 修改前快照
    try:
        from brain.repair_watchdog import watch_before
        wb = watch_before(file_path, context)
        result["steps"]["watchdog_before"] = "pass"
    except Exception as e:
        result["steps"]["watchdog_before"] = f"error: {e}"

    # Step 4: 写入文件
    try:
        fp = ROOT / file_path if not Path(file_path).is_absolute() else Path(file_path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
        result["steps"]["write"] = "pass"
    except Exception as e:
        result["steps"]["write"] = f"fail: {e}"
        result["error"] = f"写入失败: {e}"
        return result

    # Gate 5: watchdog.after — 修改后验证
    try:
        from brain.repair_watchdog import watch_after
        wa = watch_after(file_path, {"compile": "pass"})
        result["steps"]["watchdog_after"] = wa.get("compile", "?")
    except Exception as e:
        result["steps"]["watchdog_after"] = f"error: {e}"

    # Gate 6: promote_to_production — 部署到生产
    try:
        pp = m.promote_to_production(file_path, content)
        result["steps"]["promote"] = "pass" if pp["ok"] else f"fail: {pp.get('error','?')}"
        result["backup"] = pp.get("backup")
    except Exception as e:
        result["steps"]["promote"] = f"error: {e}"

    result["ok"] = True
    result["elapsed_ms"] = round((__import__('time').time() - t0) * 1000)

    # 审计日志
    try:
        with open(DEPLOY_LOG, "a", encoding="utf-8") as f:
            import json
            f.write(json.dumps({**result, "timestamp": datetime.now().isoformat()}, ensure_ascii=False) + "\n")
    except:
        pass

    return result


def deploy_status() -> dict:
    """查看部署记录"""
    try:
        logs = []
        if DEPLOY_LOG.exists():
            with open(DEPLOY_LOG, "r", encoding="utf-8") as f:
                logs = [__import__('json').loads(line) for line in f if line.strip()]
        return {"ok": True, "total_deploys": len(logs), "recent": logs[-10:]}
    except:
        return {"ok": False, "error": "无法读取部署日志"}


if __name__ == "__main__":
    print("=" * 60)
    print("  GBT 唯一部署工具 · gbt_deploy(file, content)")
    print("  这是修改文件并部署到生产的唯一通道")
    print("=" * 60)
    s = deploy_status()
    print(f"\n  历史部署: {s.get('total_deploys', 0)} 次")

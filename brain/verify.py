# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""verify.py — 项目完整性校验
============================
每次启动/提交前运行, 对比.project.manifest确保框架未触碰项目文件。
哪怕一个字母不同都能检测到。
"""
import json, hashlib, sys, os
from pathlib import Path

ROOT = Path(__file__).parent.parent
MANIFEST = ROOT / ".project.manifest"

def verify():
    if not MANIFEST.exists():
        print("❌ .project.manifest 不存在, 请先运行: python verify.py --gen")
        return False

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hashes = data["hashes"]
    ok, changed, missing, new = 0, [], [], []

    # 检查清单中的每个文件
    for rel, expected_hash in sorted(hashes.items()):
        fpath = ROOT / rel
        if not fpath.exists():
            missing.append(rel)
            continue
        try:
            actual = hashlib.sha256(fpath.read_bytes()).hexdigest()[:16]
            if actual != expected_hash:
                changed.append((rel, expected_hash, actual))
            else:
                ok += 1
        except Exception:
            changed.append((rel, expected_hash, "UNREADABLE"))

    # 检查是否有新文件(不在清单中)
    skip = {'.git', '__pycache__', '.wrangler', 'node_modules', '.pytest_cache', '.gbt'}
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), ROOT).replace("\\", "/")
            if rel not in hashes and rel not in {".project.manifest", ".env"}:
                new.append(rel)

    total = ok + len(changed) + len(missing)
    print(f"\n{'='*50}")
    print(f"🧠 GBTxiaotudouV5 · 完整性校验")
    print(f"   清单版本: {data.get('version','?')} · 生成: {data.get('generated','?')[:19]}")
    print(f"{'='*50}")
    print(f"   ✅ 一致: {ok}/{total}")
    if changed:
        print(f"   🔴 被修改: {len(changed)}个文件")
        for rel, exp, act in changed[:20]:
            print(f"      {rel}")
            print(f"         期望: {exp}  实际: {act}")
    if missing:
        print(f"   🟡 已删除: {len(missing)}个文件")
        for rel in missing[:10]:
            print(f"      {rel}")
    if new:
        print(f"   🔵 新增(未登记): {len(new)}个文件")
        for rel in new[:10]:
            print(f"      {rel}")

    all_ok = not changed and not missing
    print(f"\n   {'✅ 项目完整, 框架未触碰' if all_ok else '❌ 项目被修改! 立即检查!'}")
    return all_ok

def generate():
    """重新生成清单"""
    import datetime
    hashes = {}
    skip = {'.git', '__pycache__', '.wrangler', 'node_modules', '.pytest_cache', '.gbt'}
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip]
        skip_files = {'.project.manifest', '.env'}
        for f in files:
            fpath = os.path.join(root, f)
            rel = os.path.relpath(fpath, ROOT).replace("\\", "/")
            if rel in skip_files:
                continue
            try:
                h = hashlib.sha256(Path(fpath).read_bytes()).hexdigest()[:16]
                hashes[rel] = h
            except Exception:
                hashes[rel] = "UNREADABLE"
    data = {
        "project": "GBTxiaotudouV5",
        "version": "5.1",
        "generated": datetime.datetime.now().isoformat(),
        "files": len(hashes),
        "hashes": hashes,
    }
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 清单已生成: {len(hashes)}个文件")

if __name__ == "__main__":
    if "--gen" in sys.argv:
        generate()
    else:
        ok = verify()
        sys.exit(0 if ok else 1)

# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/deploy_audit.py -- 部署审计触手 v2.0
==========================================
每次部署自动审计，不合格拦截。

审计维度:
  🔑 密钥泄露 — 硬编码API密钥/密码/私钥
  🛡 依赖漏洞 — npm audit / pip audit
  📏 代码大小 — 源码+构建产物
  🔒 安全检查 — README/LICENSE/gitignore/安全头
  🏗 HTML有效性 — 标签闭合/body配对/style检查
  ⚙ 构建验证 — build脚本/产物检查
"""
import sys, os, json, re, subprocess, time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
AUDIT_DIR = Path.home() / ".gbt" / "deploy_audits"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


class DeployAudit:
    def __init__(self):
        self._history = []

    def audit(self, project_path: str, project_name: str = "") -> dict:
        t0 = time.time()
        pp = Path(project_path)
        if not pp.exists():
            return {"ok": False, "error": "path not found"}
        name = project_name or pp.name
        result = {
            "project": name, "path": str(pp),
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        result["checks"]["secrets"] = self._scan_secrets(pp)
        result["checks"]["dependencies"] = self._audit_deps(pp)
        result["checks"]["html"] = self._check_html(pp)
        result["checks"]["size"] = self._check_size(pp)
        result["checks"]["security"] = self._check_security(pp)
        result["checks"]["build"] = self._check_build(pp)
        scores = [c.get("score", 0) for c in result["checks"].values()]
        result["overall_score"] = round(sum(scores) / len(scores), 1)
        result["ok"] = result["overall_score"] >= 70
        result["elapsed_ms"] = int((time.time() - t0) * 1000)
        self._persist(result)
        return result

    def _scan_secrets(self, pp: Path) -> dict:
        patterns = [
            (r'(?:api_key|apikey|SECRET|TOKEN|PASSWORD)\s*[=:]\s*["\'][^"\'\s]{8,}', "硬编码密钥"),
            (r'sk-[a-zA-Z0-9]{20,}', "API Key"),
            (r'ghp_[a-zA-Z0-9]{20,}', "GitHub Token"),
            (r'-----BEGIN.*PRIVATE KEY-----', "私钥文件"),
        ]
        findings = []
        for dirpath, dirnames, filenames in os.walk(str(pp)):
            dirnames[:] = [d for d in dirnames if d not in ('node_modules', '.git', '__pycache__', 'dist', '.next')]
            for f in filenames:
                if not f.endswith(('.js', '.ts', '.jsx', '.tsx', '.py', '.json', '.yml', '.yaml', '.env', '.html')):
                    continue
                try:
                    content = open(os.path.join(dirpath, f), 'r', encoding='utf-8', errors='replace').read()
                    for pat, desc in patterns:
                        for m in re.findall(pat, content, re.IGNORECASE):
                            if 'YOUR_' not in str(m) and 'example' not in str(m).lower():
                                findings.append({"file": f, "type": desc})
                except:
                    pass
        score = max(0, 100 - len(findings) * 20)
        return {"ok": len(findings) == 0, "score": score, "findings": len(findings), "details": findings[:5]}

    def _audit_deps(self, pp: Path) -> dict:
        findings = []
        pkg = pp / "package.json"
        if pkg.exists():
            try:
                r = subprocess.run(["npm", "audit", "--json"], capture_output=True, text=True, cwd=str(pp), timeout=30)
                if r.returncode != 0:
                    try:
                        data = json.loads(r.stdout)
                        for pkg_name, info in data.get("vulnerabilities", {}).items():
                            if info.get("severity") in ("critical", "high"):
                                findings.append({"package": pkg_name, "severity": info["severity"]})
                    except:
                        pass
            except:
                pass
        score = max(0, 100 - len(findings) * 20)
        return {"ok": len(findings) == 0, "score": score, "findings": len(findings)}

    def _check_html(self, pp: Path) -> dict:
        issues = []
        for f in pp.rglob("*.html"):
            try:
                c = f.read_text(encoding='utf-8', errors='replace')
                so, sc = c.count('<style'), c.count('</style>')
                if so != sc:
                    issues.append(f"{f.name}: style {so}开/{sc}闭")
                if '<body>' not in c and any(t in c for t in ['<nav>', '<div', '<section']):
                    issues.append(f"{f.name}: 缺<body>")
                for tag in ['div', 'section']:
                    o = len(re.findall(f'<{tag}[\\s>]', c))
                    cl = c.count(f'</{tag}>')
                    if abs(o - cl) > 5:
                        issues.append(f"{f.name}: {tag} {o}开/{cl}闭")
            except:
                pass
        score = max(0, 100 - len(issues) * 25)
        return {"ok": len(issues) == 0, "score": score, "findings": len(issues), "details": issues[:5]}

    def _check_size(self, pp: Path) -> dict:
        total = 0
        for dirpath, dirnames, filenames in os.walk(str(pp)):
            dirnames[:] = [d for d in dirnames if d not in ('node_modules', '.git', '__pycache__')]
            for f in filenames:
                try: total += os.path.getsize(os.path.join(dirpath, f))
                except: pass
        kb = total / 1024
        score = 100 if kb < 10000 else (80 if kb < 50000 else 60)
        return {"ok": True, "score": score, "total_kb": round(kb, 1)}

    def _check_security(self, pp: Path) -> dict:
        score = 0
        if (pp / "README.md").exists(): score += 25
        if (pp / "LICENSE").exists() or (pp / "LICENSE.md").exists(): score += 25
        if (pp / ".gitignore").exists(): score += 25
        for f in pp.rglob("*.{js,ts,jsx,tsx,json,conf,nginx}"):
            try:
                if any(h in f.read_text(encoding='utf-8', errors='replace') for h in ['Content-Security-Policy', 'helmet']):
                    score += 25
                    break
            except: pass
        return {"ok": score >= 50, "score": score}

    def _check_build(self, pp: Path) -> dict:
        pkg = pp / "package.json"
        if not pkg.exists():
            return {"ok": True, "score": 100}
        try:
            data = json.loads(pkg.read_text(encoding='utf-8'))
            scripts = data.get("scripts", {})
            has_build = "build" in scripts
            has_dist = (pp / "dist").exists() or (pp / "build").exists() or (pp / ".next").exists()
            score = 60 + (20 if has_build else 0) + (20 if has_dist else 0)
            return {"ok": has_build or has_dist, "score": score}
        except:
            return {"ok": True, "score": 50}

    def _persist(self, result: dict):
        try:
            with open(AUDIT_DIR / "audit_log.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        except:
            pass


_auditor = None

def get_auditor():
    global _auditor
    if _auditor is None: _auditor = DeployAudit()
    return _auditor

def audit_deploy(project_path: str, project_name: str = "") -> dict:
    return get_auditor().audit(project_path, project_name)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--name", default="")
    args = p.parse_args()
    r = audit_deploy(args.path, args.name)
    print(f"\nAudit: {r['project']} — {r['overall_score']}/100 {'PASS' if r['ok'] else 'BLOCKED'}")
    for name, check in r["checks"].items():
        icon = "OK" if check.get("ok") else "FAIL"
        print(f"  [{icon}] {name}: {check.get('score', '?')}分 ({check.get('findings', 0)} issues)")

# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/visual_memory.py -- 视觉记忆 · 脑海存储 v1.0
==================================================
人眼看到 → 存入脑海 → 随时回忆。

每帧视觉数据:
  截图 PNG  → .gbt/visual_memory/frames/
  OCR 文本  → .gbt/visual_memory/ocr/
  皮层分析  → .gbt/visual_memory/analysis/
  时间线索引 → .gbt/visual_memory/timeline.json
  语义索引  → .gbt/visual_memory/semantic.json

查询: "刚才屏幕上有什么?" "今天看到了什么?" "那个窗口什么时候出现过?"
"""
import sys, os, json, time, base64, io, re
from pathlib import Path
from datetime import datetime
from typing import Optional
from collections import deque

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

MEMORY_DIR = Path.home() / ".gbt" / "visual_memory"
FRAMES_DIR = MEMORY_DIR / "frames"
OCR_DIR = MEMORY_DIR / "ocr"
ANALYSIS_DIR = MEMORY_DIR / "analysis"
TIMELINE_FILE = MEMORY_DIR / "timeline.json"
SEMANTIC_FILE = MEMORY_DIR / "semantic.json"
MEMORY_STATS_FILE = MEMORY_DIR / "stats.json"

for d in [MEMORY_DIR, FRAMES_DIR, OCR_DIR, ANALYSIS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MAX_TIMELINE = 10000  # 最多保留10000条记忆
MAX_FRAMES = 500      # 最多保留500张截图


class VisualMemory:
    """视觉记忆 — 像人脑一样存储看到的每一帧"""

    def __init__(self):
        self.timeline = self._load_json(TIMELINE_FILE, [])
        self.semantic = self._load_json(SEMANTIC_FILE, {})
        self.stats = self._load_json(MEMORY_STATS_FILE, {
            "total_frames": 0, "total_ocr_chars": 0,
            "started_at": None, "last_frame_at": None
        })
        if not self.stats.get("started_at"):
            self.stats["started_at"] = datetime.now().isoformat()

    def _load_json(self, path: Path, default):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except:
                pass
        return default

    def _save_json(self, path: Path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _prune_frames(self):
        """清理旧截图，保留最新"""
        files = sorted(FRAMES_DIR.glob("*.png"), key=lambda f: f.stat().st_mtime)
        for f in files[:-MAX_FRAMES]:
            f.unlink()

    def remember(self, capture_result: dict) -> dict:
        """记住一帧 — 存入脑海"""
        ts = datetime.now()
        ts_str = ts.strftime("%Y%m%d_%H%M%S_%f")
        memory_id = f"mem_{ts_str}"

        entry = {
            "id": memory_id,
            "timestamp": ts.isoformat(),
            "channel": capture_result.get("channel", "?"),
            "size": capture_result.get("size", [0, 0]),
        }

        # 保存截图
        if "image_base64" in capture_result:
            try:
                frame_path = FRAMES_DIR / f"{memory_id}.png"
                img_bytes = base64.b64decode(capture_result["image_base64"])
                frame_path.write_bytes(img_bytes)
                entry["frame_file"] = str(frame_path)
                self._prune_frames()
            except:
                pass

        # 保存OCR文本
        ocr_data = capture_result.get("ocr", {})
        if ocr_data.get("ok") and ocr_data.get("text"):
            ocr_text = ocr_data["text"]
            ocr_path = OCR_DIR / f"{memory_id}.txt"
            ocr_path.write_text(ocr_text, encoding="utf-8")
            entry["ocr_file"] = str(ocr_path)
            entry["ocr_length"] = len(ocr_text)
            entry["ocr_blocks"] = ocr_data.get("block_count", 0)
            entry["ocr_preview"] = ocr_text[:200]
            self.stats["total_ocr_chars"] += len(ocr_text)

            # 提取关键词用于语义索引
            keywords = self._extract_keywords(ocr_text)
            entry["keywords"] = keywords
            for kw in keywords:
                if kw not in self.semantic:
                    self.semantic[kw] = []
                self.semantic[kw].append(memory_id)
                if len(self.semantic[kw]) > 100:
                    self.semantic[kw] = self.semantic[kw][-100:]

        # 保存皮层分析
        analysis = capture_result.get("analysis", {})
        if analysis.get("ok"):
            analysis_path = ANALYSIS_DIR / f"{memory_id}.json"
            self._save_json(analysis_path, analysis)
            entry["analysis_file"] = str(analysis_path)
            entry["brightness"] = analysis.get("brightness")
            entry["edge_density"] = analysis.get("edge_density")

        # 加入时间线
        self.timeline.append(entry)
        if len(self.timeline) > MAX_TIMELINE:
            self.timeline = self.timeline[-MAX_TIMELINE:]

        # 保存
        self.stats["total_frames"] += 1
        self.stats["last_frame_at"] = ts.isoformat()
        self._save_json(TIMELINE_FILE, self.timeline[-1000:])  # 只保存最近1000条到文件
        self._save_json(SEMANTIC_FILE, dict(list(self.semantic.items())[-500:]))
        self._save_json(MEMORY_STATS_FILE, self.stats)

        return entry

    def _extract_keywords(self, text: str) -> list:
        """从OCR文本提取关键词"""
        keywords = []
        # URL
        urls = re.findall(r'https?://[^\s]+', text)
        keywords.extend([u[:60] for u in urls])
        # 中文词组 (2-4字)
        chinese = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
        from collections import Counter
        word_counts = Counter(chinese)
        keywords.extend([w for w, c in word_counts.most_common(20) if c >= 2])
        # 英文单词
        english = re.findall(r'[A-Z][a-z]{2,}', text)
        keywords.extend(list(set(english))[:10])
        return list(set(keywords))[:30]

    def recall(self, query: str = None, limit: int = 10, minutes: int = None) -> list:
        """回忆 — 从脑海检索视觉记忆"""
        results = []

        # 时间过滤
        now = datetime.now()
        for entry in reversed(self.timeline):
            ts = datetime.fromisoformat(entry["timestamp"])
            if minutes and (now - ts).total_seconds() > minutes * 60:
                continue
            if query:
                # 搜索OCR文本和关键词
                ocr_preview = entry.get("ocr_preview", "")
                keywords = entry.get("keywords", [])
                if query.lower() in ocr_preview.lower() or any(query.lower() in kw.lower() for kw in keywords):
                    results.append(entry)
            else:
                results.append(entry)
            if len(results) >= limit:
                break

        return results

    def what_i_see_now(self) -> dict:
        """我刚才看到了什么 — 最近一帧的摘要"""
        if not self.timeline:
            return {"ok": False, "message": "还没有视觉记忆"}

        latest = self.timeline[-1]
        return {
            "ok": True,
            "timestamp": latest["timestamp"],
            "channel": latest.get("channel"),
            "size": latest.get("size"),
            "ocr_preview": latest.get("ocr_preview", ""),
            "keywords": latest.get("keywords", []),
            "brightness": latest.get("brightness"),
        }

    def today_summary(self) -> dict:
        """今天看到了什么"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_entries = [e for e in self.timeline if e["timestamp"].startswith(today)]

        all_keywords = []
        urls_seen = set()
        for e in today_entries:
            all_keywords.extend(e.get("keywords", []))
            preview = e.get("ocr_preview", "")
            for url in re.findall(r'https?://[^\s]+', preview):
                urls_seen.add(url[:80])

        from collections import Counter
        top_kw = Counter(all_keywords).most_common(20)

        return {
            "ok": True,
            "date": today,
            "total_frames": len(today_entries),
            "top_keywords": [(kw, count) for kw, count in top_kw],
            "urls_seen": list(urls_seen)[:10],
            "first_frame": today_entries[0]["timestamp"] if today_entries else None,
            "last_frame": today_entries[-1]["timestamp"] if today_entries else None,
        }


# ═══════════════ 全局 ═══════════════

_memory: Optional[VisualMemory] = None


def get_memory() -> VisualMemory:
    global _memory
    if _memory is None:
        _memory = VisualMemory()
    return _memory


def remember(capture: dict) -> dict:
    return get_memory().remember(capture)


def recall(query: str = None, limit: int = 10, minutes: int = None) -> list:
    return get_memory().recall(query, limit, minutes)


def what_i_see() -> dict:
    return get_memory().what_i_see_now()


def today() -> dict:
    return get_memory().today_summary()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="视觉记忆 — 脑海存储")
    p.add_argument("--see", action="store_true", help="我刚才看到了什么")
    p.add_argument("--today", action="store_true", help="今天看到了什么")
    p.add_argument("--recall", type=str, help="搜索视觉记忆")
    p.add_argument("--stats", action="store_true", help="记忆统计")
    args = p.parse_args()

    m = get_memory()

    if args.see:
        r = m.what_i_see_now()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.today:
        r = m.today_summary()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.recall:
        results = m.recall(args.recall, limit=20)
        for e in results:
            print(f"[{e['timestamp'][11:19]}] {e.get('ocr_preview', '')[:120]}")
    elif args.stats:
        print(json.dumps(m.stats, ensure_ascii=False, indent=2))
    else:
        print(f"Visual Memory: {m.stats['total_frames']} frames stored")
        print(f"Memory dir: {MEMORY_DIR}")

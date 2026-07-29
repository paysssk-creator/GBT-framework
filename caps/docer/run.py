# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
import sys, json, os, re
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser

# ─── 1. PDF 合并 ───
def do_pdf_merge(params: dict) -> dict:
    from PyPDF2 import PdfMerger
    inputs = params.get("inputs", [])
    output = params.get("output", "")
    result = {"ok": True, "action": "pdf_merge"}
    try:
        if not inputs or not isinstance(inputs, list) or len(inputs) < 2:
            return {"ok": False, "error": "至少需要2个PDF文件路径", "action": "pdf_merge"}
        if not output:
            output = str(Path(inputs[0]).with_stem(Path(inputs[0]).stem + "_merged"))
        merger = PdfMerger()
        merged_count = 0
        total_pages = 0
        for p in inputs:
            pp = Path(p)
            if not pp.exists():
                return {"ok": False, "error": f"文件不存在: {p}", "action": "pdf_merge"}
            merger.append(str(pp))
            merged_count += 1
        merger.write(output)
        merger.close()
        result["result"] = f"已合并 {merged_count} 个PDF"
        result["output"] = output
    except Exception as e:
        result["ok"] = False
        result["error"] = f"PDF合并失败: {str(e)}"
    return result


# ─── 2. PDF 拆分 ───
def do_pdf_split(params: dict) -> dict:
    from PyPDF2 import PdfReader, PdfWriter
    input_path = params.get("input", "")
    output_dir = params.get("output_dir", "")
    ranges_str = params.get("ranges", "")
    result = {"ok": True, "action": "pdf_split"}
    try:
        if not input_path or not Path(input_path).exists():
            return {"ok": False, "error": f"文件不存在: {input_path}", "action": "pdf_split"}
        if not output_dir:
            output_dir = str(Path(input_path).with_suffix("")) + "_split"
        os.makedirs(output_dir, exist_ok=True)
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        # 解析页码范围: "1-3,5,7-9"
        pages_to_extract = set()
        if ranges_str:
            for part in ranges_str.split(","):
                part = part.strip()
                if "-" in part:
                    a, b = part.split("-", 1)
                    for pg in range(int(a) - 1, int(b)):
                        if 0 <= pg < total_pages:
                            pages_to_extract.add(pg)
                else:
                    pg = int(part) - 1
                    if 0 <= pg < total_pages:
                        pages_to_extract.add(pg)
        else:
            pages_to_extract = set(range(total_pages))
        pages_sorted = sorted(pages_to_extract)
        if not pages_sorted:
            return {"ok": False, "error": "页码范围为空或超出PDF页数", "action": "pdf_split"}
        # 将连续页码分组
        groups = []
        group_start = pages_sorted[0]
        group_end = pages_sorted[0]
        for i in range(1, len(pages_sorted)):
            if pages_sorted[i] == group_end + 1:
                group_end = pages_sorted[i]
            else:
                groups.append((group_start, group_end))
                group_start = pages_sorted[i]
                group_end = pages_sorted[i]
        groups.append((group_start, group_end))
        stem = Path(input_path).stem
        outputs = []
        for idx, (gs, ge) in enumerate(groups, 1):
            writer = PdfWriter()
            for pg in range(gs, ge + 1):
                writer.add_page(reader.pages[pg])
            out_name = f"{stem}_p{gs+1}-{ge+1}.pdf" if gs != ge else f"{stem}_p{gs+1}.pdf"
            out_path = os.path.join(output_dir, out_name)
            writer.write(out_path)
            writer.close()
            outputs.append(out_name)
        result["result"] = f"已拆分出 {len(outputs)} 个PDF文件"
        result["output_dir"] = output_dir
        result["files"] = outputs
    except Exception as e:
        result["ok"] = False
        result["error"] = f"PDF拆分失败: {str(e)}"
    return result


# ─── 3. PDF 信息 ───
def do_pdf_info(params: dict) -> dict:
    from PyPDF2 import PdfReader
    input_path = params.get("input", "")
    result = {"ok": True, "action": "pdf_info"}
    try:
        if not input_path or not Path(input_path).exists():
            return {"ok": False, "error": f"文件不存在: {input_path}", "action": "pdf_info"}
        p = Path(input_path)
        reader = PdfReader(input_path)
        file_size = p.stat().st_size
        info = {
            "filename": p.name,
            "file_size": file_size,
            "file_size_human": _format_bytes(file_size),
            "pages": len(reader.pages),
            "is_encrypted": reader.is_encrypted,
        }
        # 元数据
        meta = reader.metadata
        if meta:
            info["metadata"] = {}
            for key in ("/Title", "/Author", "/Subject", "/Creator", "/Producer"):
                val = meta.get(key, "")
                if val:
                    info["metadata"][key.lstrip("/")] = str(val)
        # 每页尺寸 (前5页汇总)
        page_sizes = []
        for i, page in enumerate(reader.pages[:5]):
            mb = page.mediabox
            if mb:
                w = float(mb.width)
                h = float(mb.height)
                page_sizes.append({"page": i + 1, "width_pt": w, "height_pt": h,
                                   "size_mm": f"{w*0.3528:.0f}x{h*0.3528:.0f}"})
        if page_sizes:
            info["page_sizes"] = page_sizes
        result["info"] = info
        result["result"] = f"{info['pages']}页, {info['file_size_human']}"
    except Exception as e:
        result["ok"] = False
        result["error"] = f"PDF信息读取失败: {str(e)}"
    return result


def _format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} TB"


# ─── 4. Markdown → HTML ───
def do_md2html(params: dict) -> dict:
    import markdown
    text = params.get("text", "")
    file_path = params.get("file", "")
    result = {"ok": True, "action": "md2html"}
    try:
        if file_path:
            p = Path(file_path)
            if not p.exists():
                return {"ok": False, "error": f"文件不存在: {file_path}", "action": "md2html"}
            text = p.read_text(encoding="utf-8", errors="replace")
        if not text:
            return {"ok": False, "error": "请提供 Markdown 文本或文件路径", "action": "md2html"}
        html = markdown.markdown(
            text,
            extensions=["extra", "codehilite", "tables", "fenced_code", "toc"]
        )
        result["result"] = html
        result["source_len"] = len(text)
        result["output_len"] = len(html)
    except Exception as e:
        result["ok"] = False
        result["error"] = f"Markdown→HTML 转换失败: {str(e)}"
    return result


# ─── 5. HTML → Markdown ───
def do_html2md(params: dict) -> dict:
    text = params.get("text", "")
    file_path = params.get("file", "")
    result = {"ok": True, "action": "html2md"}
    try:
        if file_path:
            p = Path(file_path)
            if not p.exists():
                return {"ok": False, "error": f"文件不存在: {file_path}", "action": "html2md"}
            text = p.read_text(encoding="utf-8", errors="replace")
        if not text:
            return {"ok": False, "error": "请提供 HTML 文本或文件路径", "action": "html2md"}
        md = _html_to_markdown(text)
        result["result"] = md.strip()
        result["source_len"] = len(text)
        result["output_len"] = len(md)
    except Exception as e:
        result["ok"] = False
        result["error"] = f"HTML→Markdown 转换失败: {str(e)}"
    return result


class _HTML2MDConverter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out = []
        self._skip_content = set()
        self._list_stack = []
        self._indent = ""
        self._table_mode = False
        self._tr_cells = []
        self._in_tr = False
        self._in_cell = False
        self._cell_tag = ""
        self._link_href = ""
        self._link_text = []
        self._img_src = ""
        self._img_alt = ""
        self._pre_text = []
        self._in_pre = False
        self._heading_level = 0
        self._in_blockquote = False

    def _flush_inline(self):
        pass

    def _text(self, s: str):
        if not self._skip_content:
            self.out.append(s)

    def handle_starttag(self, tag: str, attrs: list):
        a = dict(attrs)
        tag = tag.lower()
        if tag in ("script", "style", "head", "noscript"):
            self._skip_content.add(tag)
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._heading_level = int(tag[1])
            self.out.append("\n" + "#" * self._heading_level + " ")
        elif tag == "p":
            self.out.append("\n\n")
        elif tag == "br":
            self.out.append("\n")
        elif tag == "hr":
            self.out.append("\n\n---\n\n")
        elif tag == "b" or tag == "strong":
            self.out.append("**")
        elif tag == "i" or tag == "em":
            self.out.append("*")
        elif tag == "code" and not self._in_pre:
            self.out.append("`")
        elif tag == "pre":
            self._in_pre = True
            self.out.append("\n\n```\n")
        elif tag == "blockquote":
            self._in_blockquote = True
            self.out.append("\n> ")
        elif tag == "ul":
            self._list_stack.append("-")
            self.out.append("\n")
        elif tag == "ol":
            self._list_stack.append("1.")
            self.out.append("\n")
        elif tag == "li":
            if self._list_stack:
                self.out.append("\n" + self._indent + self._list_stack[-1] + " ")
            self._indent += "  "
        elif tag == "a":
            self._link_href = a.get("href", "")
            self._link_text = []
        elif tag == "img":
            src = a.get("src", "")
            alt = a.get("alt", "")
            self.out.append(f"![{alt}]({src})")
        elif tag == "table":
            self._table_mode = True
            self._tr_cells = []
            self.out.append("\n\n")
        elif tag == "tr":
            self._in_tr = True
            self._tr_cells = []
        elif tag in ("td", "th"):
            self._in_cell = True
            self._cell_tag = tag

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag in self._skip_content:
            self._skip_content.discard(tag)
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.out.append("\n\n")
            self._heading_level = 0
        elif tag == "p":
            self.out.append("\n\n")
        elif tag == "b" or tag == "strong":
            self.out.append("**")
        elif tag == "i" or tag == "em":
            self.out.append("*")
        elif tag == "code" and not self._in_pre:
            self.out.append("`")
        elif tag == "pre":
            self._in_pre = False
            self.out.append("\n```\n")
        elif tag == "blockquote":
            self._in_blockquote = False
            self.out.append("\n")
        elif tag in ("ul", "ol"):
            self._list_stack.pop()
            self.out.append("\n")
        elif tag == "li":
            self._indent = self._indent[:-2]
        elif tag == "a":
            text = "".join(self._link_text)
            if self._link_href:
                self.out.append(f"[{text}]({self._link_href})")
            else:
                self.out.append(text)
            self._link_href = ""
            self._link_text = []
        elif tag == "table":
            self._table_mode = False
        elif tag == "tr":
            self._in_tr = False
            cells_md = "| " + " | ".join(self._tr_cells) + " |"
            self.out.append(cells_md + "\n")
            if len(self._tr_cells) > 0:
                sep = "| " + " | ".join(["---"] * len(self._tr_cells)) + " |"
                self.out.append(sep + "\n")
        elif tag in ("td", "th"):
            self._in_cell = False

    def handle_data(self, data: str):
        if self._skip_content:
            return
        if self._in_pre:
            self.out.append(data)
            return
        if self._in_cell:
            cleaned = re.sub(r"\s+", " ", data)
            self.out.append(cleaned)
        if self._link_text is not None and self._link_href:
            self._link_text.append(data)
        else:
            cleaned = re.sub(r"\s+", " ", data)
            self.out.append(cleaned)


def _html_to_markdown(html: str) -> str:
    parser = _HTML2MDConverter()
    parser.feed(html)
    parser.close()
    raw = "".join(parser.out)
    # 压缩多余空行
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw


# ─── 6. 文本统计 ───
def do_txt_stats(params: dict) -> dict:
    input_path = params.get("input", "")
    text = params.get("text", "")
    top_n = params.get("top_n", 20)
    result = {"ok": True, "action": "txt_stats"}
    try:
        if input_path:
            p = Path(input_path)
            if not p.exists():
                return {"ok": False, "error": f"文件不存在: {input_path}", "action": "txt_stats"}
            text = p.read_text(encoding="utf-8", errors="replace")
        if not text:
            return {"ok": False, "error": "请提供文本或文件路径", "action": "txt_stats"}
        lines = text.splitlines()
        line_count = len(lines)
        non_empty_lines = sum(1 for L in lines if L.strip())
        char_count = len(text)
        char_no_space = len(text.replace(" ", "").replace("\n", "").replace("\t", "").replace("\r", ""))
        # 中文字符数
        cn_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        # 英文单词数
        words = re.findall(r"[a-zA-Z]+", text)
        word_count = len(words)
        # 词频
        words_lower = [w.lower() for w in words if len(w) > 1]
        word_freq = Counter(words_lower).most_common(top_n)
        # 中文字频
        cn_freq = Counter(re.findall(r"[\u4e00-\u9fff]", text)).most_common(top_n)
        stats = {
            "lines": line_count,
            "non_empty_lines": non_empty_lines,
            "characters": char_count,
            "characters_no_space": char_no_space,
            "chinese_chars": cn_chars,
            "english_words": word_count,
        }
        if word_freq:
            stats["word_frequency"] = [{"word": w, "count": c} for w, c in word_freq]
        if cn_freq:
            stats["chinese_char_frequency"] = [{"char": ch, "count": c} for ch, c in cn_freq]
        result["stats"] = stats
        result["result"] = f"{line_count}行, {word_count}词, {cn_chars}中文字, {char_count}字符"
    except Exception as e:
        result["ok"] = False
        result["error"] = f"文本统计失败: {str(e)}"
    return result


# ─── Handler 注册 ───
handlers = {
    "pdf_merge":  do_pdf_merge,
    "pdf_split":  do_pdf_split,
    "pdf_info":   do_pdf_info,
    "md2html":    do_md2html,
    "html2md":    do_html2md,
    "txt_stats":  do_txt_stats,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else ""
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except Exception:
            pass
    handler = handlers.get(action)
    if handler:
        result = handler(params)
    else:
        result = {
            "ok": False,
            "error": f"未知操作: {action}",
            "available": list(handlers.keys()),
        }
    print(json.dumps(result, ensure_ascii=False, default=str))

# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/logging_pipeline.py — 统一日志管道 v2.0
==============================================
邻域接入: tracer(span追踪) + log_analyzer(模式分析)
替代所有散落的 basicConfig() 调用。

用法:
  from brain.logging_pipeline import get_logger
  L = get_logger(__name__)
  L.info("...")
  L.error("...", extra={"span_id": "...", "cap": "..."})
"""
import logging, logging.handlers, sys, uuid
from pathlib import Path
from datetime import datetime, timezone


class _SafeFormatter(logging.Formatter):
    """防御性格式化器 — 补齐缺失的 span_id，不依赖 filter 运行时序"""
    def format(self, record):
        if not hasattr(record, "span_id"):
            record.span_id = "-"
        return super().format(record)



LOG_DIR = Path.home() / ".gbt" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_pipeline_initialized = False
_trace_enabled = True

# ═══════════════════════════════════════════════
# 统一日志配置 — 整个进程只调用一次
# ═══════════════════════════════════════════════

def init_logging(level=logging.INFO):
    """初始化全局日志管道。替换所有 basicConfig()"""
    global _pipeline_initialized
    if _pipeline_initialized:
        return
    _pipeline_initialized = True

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    # 格式: [时间] [级别] [span] [模块] 消息 — SafeFormatter 防御补齐 span_id
    fmt = _SafeFormatter(
        "[%(asctime)s] [%(levelname)-5s] [%(span_id)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 主日志 — 轮转 (10MB × 5)
    main = logging.handlers.RotatingFileHandler(
        LOG_DIR / "gbt.log", maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
    )
    main.setFormatter(fmt)
    main.setLevel(logging.DEBUG)
    root.addHandler(main)

    # 错误日志 — 单独文件 (5MB × 3)
    err = logging.handlers.RotatingFileHandler(
        LOG_DIR / "errors.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"
    )
    err.setFormatter(fmt)
    err.setLevel(logging.WARNING)
    root.addHandler(err)

    # 控制台
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(fmt)
    console.setLevel(logging.WARNING)
    root.addHandler(console)

    # 挂载 span filter 到根 logger，确保首次日志不报 KeyError
    root.addFilter(_span_filter)

    root.info("[LoggingPipeline] 统一日志管道启动 · tracer=%s · log_analyzer=ready", "on" if _trace_enabled else "off")


# ═══════════════════════════════════════════════
# Span追踪 — 每个操作注入 trace_id
# ═══════════════════════════════════════════════

class TraceContext:
    """线程本地 span 上下文"""
    def __init__(self):
        self.trace_id: str = ""
        self.span_id: str = ""

_trace_ctx = TraceContext()

def start_trace(operation="unknown"):
    """开始一个追踪 span。返回 trace_id"""
    _trace_ctx.trace_id = uuid.uuid4().hex[:12]
    _trace_ctx.span_id = uuid.uuid4().hex[:8]
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from caps.tracer.run import do_start_trace
        do_start_trace({
            "trace_id": _trace_ctx.trace_id,
            "span_id": _trace_ctx.span_id,
            "operation": operation
        })
    except Exception:
        pass
    return _trace_ctx.trace_id

def end_trace(ok=True, error=None):
    """结束当前追踪 span"""
    tid = _trace_ctx.trace_id
    sid = _trace_ctx.span_id
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from caps.tracer.run import do_end_trace
        do_end_trace({
            "trace_id": tid,
            "span_id": sid,
            "ok": ok,
            "error": error
        })
    except Exception:
        pass
    _trace_ctx.trace_id = ""
    _trace_ctx.span_id = ""
    return tid


# ═══════════════════════════════════════════════
# Logger工厂 — 自动注入 span_id
# ═══════════════════════════════════════════════

class _SpanFilter(logging.Filter):
    def filter(self, record):
        record.span_id = _trace_ctx.span_id or "-"
        return True

_span_filter = _SpanFilter()

def get_logger(name):
    """获取带 span 追踪的 logger"""
    L = logging.getLogger(name)
    if _span_filter not in L.filters:
        L.addFilter(_span_filter)
    return L


# ═══════════════════════════════════════════════
# 快速函数
# ═══════════════════════════════════════════════

def trace_operation(operation, fn, *args, **kwargs):
    """一行包裹: tracer span + 自动记录"""
    start_trace(operation)
    L = get_logger("exec")
    L.info("开始: %s", operation)
    try:
        result = fn(*args, **kwargs)
        ok = result.get("ok", True) if isinstance(result, dict) else True
        end_trace(ok=ok)
        L.info("完成: %s ok=%s", operation, ok)
        return result
    except Exception as e:
        end_trace(ok=False, error=str(e)[:200])
        L.error("失败: %s — %s", operation, str(e)[:200])
        raise

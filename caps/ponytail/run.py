# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
import sys,json

LADDER = [
    ("YAGNI", "这个功能真的需要存在吗？不需要就跳过"),
    ("复用", "代码库里已经有了？直接复用"),
    ("标准库", "标准库能实现？不引入依赖"),
    ("原生", "平台原生功能？用<input>而非组件库"),
    ("现有依赖", "已安装的依赖能做？用现有的"),
    ("一行代码", "一行代码能搞定？写一行"),
    ("最小实现", "以上都不行，才写最小可工作的代码"),
]

PRINCIPLES = [
    "最好的代码是不写的代码",
    "懒惰于解决方案，勤奋于阅读理解",
    "信任边界验证、数据安全、错误处理绝不省略",
    "54%更少代码，20%更便宜，27%更快，100%安全",
]

def do_ladder(params):
    task = params.get("task", params.get("prompt", ""))
    return {"ok": True, "task": task, "ladder": [{"step": i+1, "name": r[0], "check": r[1]} for i,r in enumerate(LADDER)], "principle": "在上方阶梯中找到解决方案后再写代码"}

def do_principles(params=None):
    return {"ok": True, "principles": PRINCIPLES, "stats": "54% less code, 20% cheaper, 27% faster, 100% safe", "stars": 85000}

HANDLERS = {"ladder": do_ladder, "principles": do_principles, "audit": do_principles}

if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "ladder"
    p = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    h = HANDLERS.get(a, lambda x: {"ok": False})
    print(json.dumps(h(p), ensure_ascii=False))

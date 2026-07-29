# GBT cap: miniapp — 微信小程序一键生成部署
import sys, json, os, shutil
from pathlib import Path
from datetime import datetime

CAP_DIR = Path(__file__).parent
TEMPLATES_DIR = CAP_DIR / "templates"

TEMPLATES = {
    "ecommerce": {
        "name": "电商小程序",
        "desc": "轮播图+商品网格+购物车+会员中心，适合零售/服装/生鲜",
        "pages": ["首页","商品详情","购物车","会员中心"],
        "features": ["商品搜索","分类导航","购物车角标","价格对比"],
    },
    "article": {
        "name": "文章小程序",
        "desc": "文章列表+详情+分类，适合自媒体/博客/新闻",
        "pages": ["首页(文章流)","文章详情"],
        "features": ["文章列表","分类筛选","阅读历史"],
    },
    "card": {
        "name": "名片小程序",
        "desc": "个人/企业电子名片，适合商务/销售/服务",
        "pages": ["名片首页"],
        "features": ["一键拨号","微信咨询","地图导航","图片展示"],
    },
    "food": {
        "name": "点餐小程序",
        "desc": "菜单浏览+购物车+下单，适合餐饮/外卖/咖啡",
        "pages": ["菜单首页","下单","订单"],
        "features": ["菜品分类","规格选择","购物车","订单追踪"],
    },
}

def do_list(params: dict = None) -> dict:
    """列出所有可用模板"""
    return {
        "ok": True,
        "templates": [
            {"id": k, "name": v["name"], "desc": v["desc"], "pages": v["pages"]}
            for k, v in TEMPLATES.items()
        ]
    }

def do_info(params: dict) -> dict:
    """查看模板详情"""
    tmpl = params.get("template", "ecommerce")
    if tmpl not in TEMPLATES:
        return {"ok": False, "error": f"未知模板: {tmpl}", "available": list(TEMPLATES.keys())}
    t = TEMPLATES[tmpl]
    tmpl_dir = TEMPLATES_DIR / tmpl
    files = []
    if tmpl_dir.exists():
        for f in tmpl_dir.rglob("*"):
            if f.is_file():
                files.append(str(f.relative_to(tmpl_dir)))
    return {"ok": True, "template": tmpl, **t, "files": sorted(files), "path": str(tmpl_dir)}

def do_create(params: dict) -> dict:
    """脚手架新小程序项目"""
    name = params.get("name", "my-miniapp")
    target = Path(params.get("path", str(Path.home() / "Desktop"))) / name
    tmpl = params.get("template", "ecommerce")

    if tmpl not in TEMPLATES:
        return {"ok": False, "error": f"未知模板: {tmpl}", "available": list(TEMPLATES.keys())}

    src = TEMPLATES_DIR / tmpl
    if not src.exists():
        return {"ok": False, "error": f"模板目录不存在: {src}"}

    if target.exists():
        return {"ok": False, "error": f"目标已存在: {target}"}

    # 复制模板
    shutil.copytree(src, target)

    # 替换项目变量
    for f in target.rglob("*"):
        if f.is_file() and f.suffix in (".json", ".js", ".wxml", ".wxss", ".md"):
            content = f.read_text(encoding="utf-8", errors="replace")
            content = content.replace("{{PROJECT_NAME}}", name)
            content = content.replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))
            f.write_text(content, encoding="utf-8")

    return {
        "ok": True,
        "name": name,
        "template": tmpl,
        "path": str(target),
        "pages": TEMPLATES[tmpl]["pages"],
        "next": f"用微信开发者工具打开 {target}，点击「上传」即可发布",
    }

def do_deploy(params: dict) -> dict:
    """生成部署指南"""
    path = params.get("path", "")
    return {
        "ok": True,
        "steps": [
            "1. 下载微信开发者工具: https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html",
            "2. 打开微信开发者工具 → 导入项目 → 选择目录",
            f"   项目目录: {path or '<你的项目路径>'}",
            "3. 填写 AppID (在 mp.weixin.qq.com 注册获取)",
            "4. 开发工具中点击「上传」→ 填写版本号 → 上传",
            "5. 登录 mp.weixin.qq.com → 版本管理 → 提交审核",
            "6. 审核通过后点击「发布」",
        ],
        "cli_command": f'打开微信开发者工具后，也可用 CLI: cli open --project "{path or "/path/to/project"}"',
    }

handlers = {
    "run":    do_create,
    "create": do_create,
    "list":   do_list,
    "info":   do_info,
    "deploy": do_deploy,
}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "list"
    raw = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(raw)
    except Exception:
        params = {"instruction": raw}
    h = handlers.get(action, lambda p: {"ok": False, "error": f"未知:{action}", "available": list(handlers.keys())})
    print(json.dumps(h(params), ensure_ascii=False, indent=2))

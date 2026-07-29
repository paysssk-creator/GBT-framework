# GBTxiaotudouV5 架构边界

## 🧠 AI 框架 (可复用·不绑项目)

```
brain/          — 大脑引擎: nexus神经网络·推理·记忆·进化
caps/           — 190个能力模块: 感知·攻击·创作·金融·安全
gbt.py          — 统一CLI入口: chat/daemon/scan/boot
gbt_tui.py      — Kimi API对话终端
AGENTS.md       — AI行为规范+3D设计规范
CONSTITUTION.md — 执行铁律
pipeline.md     — 认知管线
gates.md        — 门禁系统
.omp/           — OMP扩展(健康扫描·桌面操控)
requirements.txt
pyproject.toml
```

## 📦 项目层 (GBT平台·可替换)

```
web/            — 前端页面·3D引擎·SDK
integrations/   — 支付·中继·Cloudflare·Telegram·交易
deploy/         — 部署脚本·隧道·趋势扫描
tools/          — 辅助工具
tests/          — 测试文件
.env            — 环境配置(API密钥等)
```

## 规则
- 框架层不引用项目层 (brain/ 不 import web/)
- 项目层可引用框架层 (web/ 可调用 caps/)
- 换个项目 = 换 web/ + integrations/ + .env
- 框架可独立打包部署到任何宿主

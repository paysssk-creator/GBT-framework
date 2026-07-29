# ⛔ 不可修改 · 不可删除 · 不可绕过
# GBT v5.0 统一执行路径 · 唯一通道
#
# 这是GBT框架的唯一执行路径。没有第二条路。
# 任何绕过、跳过、逾越此路径的操作 = 大脑根本性失效。
#
# 此文件在chain_kernel Phase 1 (宪法校验) 中被验证完整性。
# 被篡改 → 全链锁定 → 不可继续执行。

═══════════════════════════════════════════════════════════════
  GBT v5.0 · 统一执行路径 · ONE PATH ONLY
═══════════════════════════════════════════════════════════════

任何操作(读/写/改/部署/提交)必须经过以下唯一通道:

┌─────────────────────────────────────────────────────────────┐
│  STEP -2: 链内核启动 (auto_boot)                            │
│    13阶段全链验证 → 任何阻断 = 不可继续                       │
│    └→ Phase 12: 镜像空间就绪                                 │
├─────────────────────────────────────────────────────────────┤
│  每次操作前: enforce() 四重门禁                               │
│    Gate 1: 绕过检测 (30+关键词, 逾越链路等)                    │
│    Gate 2: vision_checkpoint (自动视觉监护)                   │
│    Gate 3: step_tracker (禁止跳步)                           │
│    Gate 4: mirror_verify (文件修改必须过镜像)                  │
├─────────────────────────────────────────────────────────────┤
│  修改任何文件:                                               │
│    ① mirror_fusion.mirror_verify(file)     ← 镜像验证        │
│    ② watchdog.before(file)                 ← 修改前快照       │
│    ③ 执行修改                               ← 在镜像空间改     │
│    ④ watchdog.after(file)                  ← 编译验证+快照    │
│    ⑤ mirror_fusion.promote_to_production() ← 部署到生产      │
├─────────────────────────────────────────────────────────────┤
│  部署到生产:                                                 │
│    必须通过 promote_to_production()                          │
│    禁止: 直接 git push                                     │
│    禁止: 直接 npx wrangler deploy                           │
│    禁止: 直接写入生产文件                                    │
└─────────────────────────────────────────────────────────────┘

唯一出入口 — deploy()：

  修改任何文件 → 必须调用 deploy(file, content, context)
    deploy() 是唯一门。write/edit/bash/cp 直接改文件 = 违法 = 被阻断。

  内部自动执行:
    enforce() → mirror_verify() → watchdog.before()
    → 写入 → watchdog.after() → promote_to_production()

禁止路径 (任何匹配 → enforce()阻断):
  ❌ 直接 git commit/push           → 必须走 promote_to_production()
  ❌ 直接 write/edit 生产文件        → 必须走 mirror_fusion
  ❌ 直接 npx/cfx/curl 部署          → 必须走 promote_to_production()
  ❌ 跳过 enforce()                  → 操作被拒绝
  ❌ 跳过 mirror_verify()            → 文件修改被拒绝
  ❌ 跳过 watchdog                   → 没有视觉验证 = 盲操作

唯一正确路径:
  enforce() → mirror_verify() → watchdog → 修改 → promote_to_production()

此路径不可缩短、不可跳过、不可绕过、不可逾越。
═══════════════════════════════════════════════════════════════

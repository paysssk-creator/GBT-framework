# GBTxiaotudouV5 · 全量修复记录

> **日期**: 2026-07-27  
> **审计**: OMP 原生控制包 + 深度排查 + 部署上线  
> **结果**: 零错报, 一致性 208/208, 192/192 cross-ref

---

## 一、启动修复 (3 项)

### 1. Daemon 启动卡死
- **文件**: `caps/devourer/run.py`
- **根因**: `scan_platforms()` 串行 16 个 LLM API 调用, 总耗时 ~3 分钟
- **修复**: `ThreadPoolExecutor(max_workers=8)` 真正并发, `per_source_timeout=45s`
- **效果**: 180s → 28s

### 2. 邻域断连 5 处
- **文件**: `brain/nexus.py`
- **根因**: `scan()` 只查 `caps/`, `integrations/payment/` 下 5 个支付 cap 未被发现
- **修复**: 新增 `_EXTRA_CAP_DIRS = [PAYMENT_DIR]` 多路径扫描
- **效果**: 190/190 cross-ref 全匹配

### 3. 缺口误报
- **文件**: `caps/devourer/run.py`
- **根因**: `analyze_gaps()` 关键词匹配漏 `content_publisher`/`translator`（"translate" 非 "translator" 子串）
- **修复**: 加入 `_suggest_cap_name()` 精确匹配
- **效果**: 4 gaps → 0 gaps（另创建 simulation_env, compliance_checker）

---

## 二、运行时 Bug 修复 (8 项)

| # | 文件 | 问题 | 修复 |
|---|---|---|---|
| 1 | `caps/darknet_scanner/run.py` | `urllib.request.quote` AttributeError | → `urllib.parse.quote` |
| 2 | `caps/rag_knowledge/run.py` | CLI `h(pr)` 传空, `params` 被丢弃 | → `h(params)` |
| 3 | `integrations/payment/cryptapi_pay/run.py` | subprocess 路径 `_payment/revenue_split` 不存在 | 去掉多余 `_payment/` |
| 4 | `brain/remote_body.py` | `RemoteEyes.find()` 类型检查错误, 永远无法 `found=True` | `isinstance(r, dict)` + `r.get("x"/"y")` |
| 5 | `caps/proxy_network/run.py` | stdin 读取 → subprocess 调用挂死 | 优先 argv, 回退 stdin |
| 6 | `caps/root_cause_debugger/run.py` | 3 函数未注册 HANDLERS | 加入 `auto_debug/hypothesis/fix_attempt` |
| 7 | `caps/state_space/run.py` | 3 函数未注册 HANDLERS | 加入 `detect_loop/escape_loop/explore_branch` |
| 8 | `caps/docer/run.py` | table 渲染 cell 文本从不收集 | `pass` → 实际追加文本 |

---

## 三、Cap 一致性 (208/208)

- **79 caps** 缺 `auto_exec` 字段 → 批量补全
- **88 caps** capability.json 与 run.py HANDLERS 不匹配 → 自动对齐脚本
- **`_2captcha`** 无 HANDLERS → 新增 5 个 handler
- **`rag_knowledge`** `HANDLERS = H` 别名 → 内联 dict
- **`check_cap_consistency.py`** 增强: 多 HANDLERS 声明取最后, 空 dict 回退 import
- **最终**: `passed: true`, 0 mismatch, 0 missing, 0 parse error

---

## 四、新 Cap (2 个)

| Cap | 功能 | 邻域 |
|-----|------|------|
| `simulation_env` | OpenAI Gym + RL 训练环境 | 特殊域 |
| `compliance_checker` | GDPR/SOC2/ISO27001 合规检查 + 代码扫描 | 特殊域 |

已在 `nexus.py` NEIGHBORHOODS + INTENT_ROUTES 注册。

---

## 五、部署: OMP 原生控制包

- **包位置**: `web/downloads/gbt-omp-control-pack.zip` (4.6KB)
- **内容**: `install.bat` (Win) + `install.sh` (Mac/Linux) + `README.md`
- **下载页**: `gbtxiaotudou.com/downloads.html`
- **部署**: Cloudflare Pages → main + production 双分支
- **审计**: ZIP CRC ✅ / 内容完整性 ✅ / CDN 200 ✅

---

## 六、验证状态

```
Nexus Deep Scan:   🟢 全连接完好 (0 issues)
Cap Consistency:   ✅ passed (208/208)
Cap Import:        192/192 OK
Gap Analysis:      0 gaps
Brain Modules:     12/12 import OK
Daemon Startup:    全 ✅, 零 ❌⛔⚠️
```

# 8号当铺 部署标准流程 (SOP)

## 每次部署必须执行:

### ① 本地验证
```
python gbt.py scan          # 穿透扫描, 0错误才继续
python -c "验证HTML: style闭合/body标签/div匹配"
```

### ② 浏览器验证
```
打开浏览器 → 看页面渲染 → 检查:
  - nav/hero/content 是否正常显示
  - 项目卡片数量正确
  - 无 "Something went wrong" 等错误
  - 移动端响应式正常
```

### ③ 审计门禁
```
python -c "from brain.deploy_audit import audit_deploy; r=audit_deploy('web'); print(r['overall_score'])"
≥70分 → 放行
<70分 → 修复后重新来过
```

### ④ 提交推送
```
git add <files>
git commit -m "描述改动"
git push origin master:main
```

### ⑤ 等待Cloudflare自动部署 (1-2分钟)
```
不要手动 wrangler deploy
刷新 gbtxiaotudou.com 验证
如果1分钟后还是旧版 → 加 ?v=timestamp 参数绕过缓存
```

### ⑥ 生产复查
```
浏览器打开 gbtxiaotudou.com
检查所有功能正常
截图留证
```

## 禁止事项
- ❌ 改完直接推送不验证
- ❌ wrangler和git push同时用
- ❌ 部署完不复查
- ❌ 带语法错误提交
- ❌ 跳过审计门禁

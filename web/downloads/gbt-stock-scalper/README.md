# GBT A股AI快进快出操盘系统 v1.0

基于涨幅动量的A股短线AI交易系统。AI实时监控涨幅榜，判断动量持续性，快进快出赚取价差。

## 特性
- 🤖 AI驱动：DeepSeek实时分析涨幅动量
- ⚡ 快进快出：涨幅2-8%候选 → AI决策 → 市价买入
- 🛡️ 自动风控：止盈+3% / 止损-1.5%
- 📊 新浪行情：实时A股数据
- 💰 模拟交易：零风险练习

## 快速开始

### 1. 配置 API Key
```bash
python main.py config set deepseek_api_key=sk-your-key-here
```

### 2. 扫描市场
```bash
python main.py scan
```

### 3. 执行快进快出
```bash
python main.py scalp
```

## 策略参数

在 `config.json` 中调整：

```json
{
  "strategy": {
    "max_stocks": 5,       // 最多同时持有
    "max_amount": 100000,   // 最大投入金额
    "min_change": 2.0,      // 最小涨幅%
    "max_change": 8.0,      // 最大涨幅%(排除涨停)
    "take_profit": 3.0,     // 止盈%
    "stop_loss": -1.5       // 止损%
  }
}
```

## 免责声明
本系统仅供学习和模拟交易使用。A股投资有风险，实盘交易请自行承担风险。

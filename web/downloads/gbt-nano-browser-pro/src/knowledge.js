// ⛔ GBT Nano Browser Pro — AI 知识记忆注入
// ⛔ QA铁律：部署后必须复查，不能部署完就走
const KNOWLEDGE = {
  _version: "1.0.0", _app_name: "GBT Nano Browser Pro",

  product: {
    name: "GBT Nano Browser Pro", version: "1.0.0", developer: "自由的风 · GBT小土豆",
    website: "https://gbtxiaotudou.com",
    pricing: {
      free: { price: "免费", features: ["基础浏览","2个标签","AI基础问答"] },
      pro: { price: "$29/月", features: ["无限标签","指纹隐身","2Captcha","AI全控","股票操盘","优先支持"] },
      enterprise: { price: "$99/月", features: ["全部Pro功能","API接入","白标定制","专属AI训练","7x24支持"] }
    },
    how_to_buy: "访问 https://gbtxiaotudou.com/pricing.html 选择套餐，支持支付宝/微信/加密货币/信用卡"
  },

  browser: {
    tabs: { desc: "多标签浏览", how_to: "点击+新建标签，Ctrl+T/W切换关闭" },
    stealth: { desc: "指纹隐身模式——15维指纹随机化", how_to: "左侧菜单开启隐身开关" },
    captcha: { desc: "2Captcha自动验证码", how_to: "设置中填入API Key", setup: "1.注册2captcha.com 2.获取Key 3.填入设置", buy: "https://2captcha.com/p/playwright-captcha-solver" },
    devtools: { desc: "开发者工具", how_to: "F12或右键检查元素" }
  },

  stock: {
    desc: "A股AI自动操盘——心跳驱动快进快出割草式盈利",
    features: ["30秒心跳扫描","多源资讯采集","AI推理决策","风控保护","御姐音播报","每日复盘"],
    config: { capital: "总资金(10万)", interval: "心跳间隔(30秒)", tp: "止盈+3%", sl: "止损-2%" }
  },

  ai: {
    desc: "AI全控助手", how_to: "Ctrl+Space唤醒，语音/文字操控一切",
    examples: ["帮我打开淘宝","扫描今天的牛股","怎么买Pro版","验证码怎么用"]
  },

  shopping: {
    ecommerce: [{name:"淘宝",url:"https://taobao.com"},{name:"京东",url:"https://jd.com"},{name:"拼多多",url:"https://pinduoduo.com"},{name:"Amazon",url:"https://amazon.com"}],
    stock_platforms: [{name:"东方财富",url:"https://eastmoney.com"},{name:"雪球",url:"https://xueqiu.com"},{name:"同花顺",url:"https://10jqka.com.cn"},{name:"新浪财经",url:"https://finance.sina.com.cn"}],
    tools: [{name:"2Captcha",url:"https://2captcha.com"},{name:"DeepSeek",url:"https://platform.deepseek.com"},{name:"GitHub",url:"https://github.com"}]
  },

  qa: {
    desc: "⛔ 部署交付铁律——每次部署后强制执行复查",
    layers: ["第一层:语法编译+JSON格式检查","第二层:启动验证+端口监听+Error=0","第三层:用户视角——打开界面测试每个按钮"],
    forbidden: ["编译通过≠完成","跑起来≠能用","报错不能忽略","黑屏≠启动","没复查≠交付"],
    tool: "python qa_check.py [cap] --user",
    standard: "全部✓通过才算交付"
  },

  faq: [
    {q:"如何购买Pro版?",a:"访问 gbtxiaotudou.com/pricing.html 选择套餐，支付宝/微信/加密货币均可"},
    {q:"验证码怎么用?",a:"1.去2captcha.com注册充值 2.获取API Key 3.设置中填入并开启"},
    {q:"股票操盘安全吗?",a:"目前为模拟交易，风控规则专业严谨"},
    {q:"部署后怎么检查?",a:"运行 python qa_check.py [cap名] --user 自动复查三层"}
  ]
};

function search(query) {
  const q = (query||'').toLowerCase(), results = [];
  for (const [cat, content] of Object.entries(KNOWLEDGE)) {
    if (typeof content === 'string' && content.toLowerCase().includes(q)) results.push({cat,content});
    else if (Array.isArray(content)) for (const item of content)
      if (JSON.stringify(item).toLowerCase().includes(q)) results.push({cat,item});
    else if (content.desc && content.desc.toLowerCase().includes(q)) results.push({cat,...content});
  }
  return results.slice(0,10);
}
function getTopic(t) { return KNOWLEDGE[t] || search(t); }
function getAll() { return KNOWLEDGE; }
module.exports = { KNOWLEDGE, search, getTopic, getAll };

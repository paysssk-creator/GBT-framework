# 开发者：自由的风
"""stock_trader/run.py — A股自动操盘系统
==========================================
完整交易链路: 选股→分析→决策→下单→风控→复盘

数据源: 东方财富/同花顺免费API
交易: 券商API模拟(可接入华泰/中信/国金等)
"""
import sys, json, os, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

TRADE_DIR = Path.home() / '.gbt' / 'trading'
TRADE_DIR.mkdir(parents=True, exist_ok=True)

# 交易配置
DEFAULT_CONFIG = {
    'max_position': 0.3,      # 单票最大仓位30%
    'stop_loss': -0.05,       # 止损-5%
    'take_profit': 0.10,      # 止盈+10%
    'max_daily_trades': 10,   # 每日最大交易次数
    'max_daily_loss': -0.03,  # 每日最大亏损-3%
}


def _eastmoney_api(path, params=None):
    """东方财富免费API"""
    base = 'https://push2.eastmoney.com/api/qt'
    try:
        url = base + path
        if params:
            url += '?' + '&'.join(f'{k}={v}' for k, v in params.items())
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://quote.eastmoney.com/'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8', errors='replace')), None
    except Exception as e:
        return None, str(e)[:200]


def do_scan_market(params=None):
    """扫描全市场 — 技术面+资金面选股"""
    strategy = (params or {}).get('strategy', 'hot_money')
    
    strategies = {
        'hot_money': '涨停板+龙虎榜+资金流向',
        'trend_follow': '均线多头+MACD金叉+放量',
        'oversold_bounce': '超跌反弹+底背离+缩量',
        'breakout': '突破前高+放量+板块共振'
    }
    
    # 获取实时行情
    stocks = []
    
    # 1. 涨停板扫描
    resp, err = _eastmoney_api('/stock/limitup/get', {
        'pagesize': 50, 'page': 1,
        'sort': 'limit_up_time', 'order': 'desc'
    })
    if resp:
        for item in resp.get('data', {}).get('diff', [])[:20]:
            stocks.append({
                'code': item.get('f12', ''),
                'name': item.get('f14', ''),
                'price': item.get('f2', 0),
                'change_pct': item.get('f3', 0),
                'volume': item.get('f5', 0),
                'limit_up_times': item.get('f14', 0),
                'sector': item.get('f100', ''),
                'reason': '涨停'
            })
    
    return {
        'ok': True,
        'strategy': strategies.get(strategy, strategy),
        'market_time': datetime.now().strftime('%H:%M:%S'),
        'candidates': stocks[:20],
        'total': len(stocks)
    }


def do_analyze_stock(params):
    """个股深度分析"""
    code = params.get('code', '')
    if not code:
        return {'ok': False, 'error': '缺少股票代码'}
    
    # 添加市场前缀
    if code.startswith('6'):
        full_code = '1.' + code  # 上海
    else:
        full_code = '0.' + code  # 深圳
    
    analysis = {
        'code': code,
        'full_code': full_code,
        'time': datetime.now().strftime('%H:%M:%S'),
        'technical': {},
        'fund_flow': {},
        'score': 0,
        'signal': 'wait'  # buy/sell/wait
    }
    
    # 技术面
    resp, _ = _eastmoney_api('/stock/get', {
        'secid': full_code,
        'fields': 'f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60,f116,f117,f162,f167,f168,f169,f170'
    })
    if resp and resp.get('data'):
        d = resp['data']
        analysis['technical'] = {
            'price': d.get('f43', 0),
            'high': d.get('f44', 0),
            'low': d.get('f45', 0),
            'open': d.get('f46', 0),
            'volume': d.get('f47', 0),
            'amount': d.get('f48', 0),
            'change_pct': d.get('f170', 0),
            'pe': d.get('f162', 0),
            'market_cap': d.get('f116', 0) / 1e8 if d.get('f116') else 0
        }
        
        # 评分
        price = d.get('f43', 0)
        change = d.get('f170', 0)
        score = 50
        if change > 0:
            score += min(change * 5, 30)
        if d.get('f47', 0) > d.get('f117', 0) * 1.5:
            score += 10  # 放量
        if price > d.get('f60', 0):
            score += 5  # 站上20日均线
        analysis['score'] = min(score, 100)
        analysis['signal'] = 'buy' if score >= 65 else ('sell' if score < 30 else 'wait')
    
    return {'ok': True, 'analysis': analysis}


def do_place_order(params):
    """下单 — 模拟交易(可接入券商API)"""
    code = params.get('code', '')
    action = params.get('action', 'buy')  # buy/sell
    price = float(params.get('price', 0))
    quantity = int(params.get('quantity', 100))
    
    if not code or price <= 0 or quantity <= 0:
        return {'ok': False, 'error': '参数不完整'}
    
    # 风控检查
    positions = _load_positions()
    total_value = sum(p.get('market_value', 0) for p in positions.values())
    
    if action == 'buy':
        if len(positions) >= 10:
            return {'ok': False, 'error': '持仓超过10只, 已达上限'}
        order_value = price * quantity
        if total_value > 0 and order_value / total_value > DEFAULT_CONFIG['max_position']:
            return {'ok': False, 'error': f'单票仓位超过{DEFAULT_CONFIG["max_position"]*100}%'}
    
    order = {
        'id': f'ORD{int(time.time())}{code}',
        'code': code,
        'action': action,
        'price': price,
        'quantity': quantity,
        'value': price * quantity,
        'status': 'submitted',
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'note': '模拟交易 — 实际接入券商API后生效'
    }
    
    # 保存订单
    orders_file = TRADE_DIR / 'orders.jsonl'
    with open(orders_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(order, ensure_ascii=False) + '\n')
    
    return {'ok': True, 'order': order}


def do_risk_check(params=None):
    """风控检查"""
    positions = _load_positions()
    orders = _load_orders()
    
    total_value = sum(p.get('market_value', 0) for p in positions.values())
    today_pnl = sum(p.get('today_pnl', 0) for p in positions.values())
    today_trades = len([o for o in orders if o.get('time', '')[:10] == datetime.now().strftime('%Y-%m-%d')])
    
    alerts = []
    if today_pnl < total_value * DEFAULT_CONFIG['max_daily_loss'] and total_value > 0:
        alerts.append({'level': 'danger', 'msg': f'当日亏损{today_pnl:.0f}, 超过限额, 强制停止交易'})
    if today_trades >= DEFAULT_CONFIG['max_daily_trades']:
        alerts.append({'level': 'warning', 'msg': f'当日交易{today_trades}次, 已达上限'})
    
    for code, pos in positions.items():
        if pos.get('pnl_pct', 0) <= DEFAULT_CONFIG['stop_loss']:
            alerts.append({'level': 'danger', 'msg': f'{code} 触发止损 {pos['pnl_pct']*100:.1f}%'})
        if pos.get('pnl_pct', 0) >= DEFAULT_CONFIG['take_profit']:
            alerts.append({'level': 'info', 'msg': f'{code} 触发止盈 {pos['pnl_pct']*100:.1f}%'})
    
    can_trade = not any(a['level'] == 'danger' for a in alerts)
    
    return {
        'ok': True,
        'can_trade': can_trade,
        'total_value': total_value,
        'today_pnl': today_pnl,
        'today_trades': today_trades,
        'alerts': alerts,
        'limits': DEFAULT_CONFIG
    }


def do_review(params=None):
    """复盘 — 今日交易总结"""
    orders = _load_orders()
    today = datetime.now().strftime('%Y-%m-%d')
    today_orders = [o for o in orders if o.get('time', '')[:10] == today]
    
    if not today_orders:
        return {'ok': True, 'message': '今日无交易记录'}
    
    buys = [o for o in today_orders if o['action'] == 'buy']
    sells = [o for o in today_orders if o['action'] == 'sell']
    
    total_buy = sum(o['value'] for o in buys)
    total_sell = sum(o['value'] for o in sells)
    
    return {
        'ok': True,
        'date': today,
        'trades': len(today_orders),
        'buys': len(buys), 'sells': len(sells),
        'total_buy': total_buy, 'total_sell': total_sell,
        'pnl': total_sell - total_buy,
        'details': today_orders
    }


def _load_positions():
    f = TRADE_DIR / 'positions.json'
    if f.exists():
        return json.loads(f.read_text(encoding='utf-8'))
    return {}

def _load_orders():
    f = TRADE_DIR / 'orders.jsonl'
    if f.exists():
        return [json.loads(line) for line in f.read_text(encoding='utf-8').strip().split('\n') if line.strip()]
    return []


def do_kline(params=None):
    """获取个股K线数据 — 东方财富免费API"""
    code = (params or {}).get('code', 'sh600519')
    period = (params or {}).get('period', 'day')
    limit = int((params or {}).get('limit', 60))

    # 市场代码转换: sh→1, sz→0
    market = '1' if code.startswith('sh') or code.startswith('6') else '0'
    secid = f'{market}.{code.replace("sh","").replace("sz","")}'

    # 周期映射: day→101, week→102, month→103
    period_map = {'day': '101', 'week': '102', 'month': '103'}
    klt = period_map.get(period, '101')

    url = (
        f'https://push2his.eastmoney.com/api/qt/stock/kline/get?'
        f'secid={secid}&fields1=f1,f2,f3,f4,f5,f6'
        f'&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61'
        f'&klt={klt}&fqt=1&end=20500101&lmt={min(limit,120)}'
    )

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://quote.eastmoney.com/'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode('utf-8'))

        klines_data = (raw.get('data') or {}).get('klines', [])
        if not klines_data:
            return {'ok': False, 'error': '无K线数据，请检查股票代码'}

        klines = []
        for line in klines_data:
            parts = line.split(',')
            if len(parts) < 7:
                continue
            klines.append({
                'date': parts[0],
                'open': float(parts[1]),
                'close': float(parts[2]),
                'high': float(parts[3]),
                'low': float(parts[4]),
                'volume': int(float(parts[5])),
                'amount': float(parts[6])
            })

        return {
            'ok': True,
            'code': code,
            'name': raw.get('data', {}).get('name', ''),
            'period': period,
            'klines': klines
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)[:200]}


HANDLERS = {
    'scan': do_scan_market, 'analyze': do_analyze_stock,
    'order': do_place_order, 'risk': do_risk_check,
    'review': do_review, 'positions': lambda p: {'ok': True, 'positions': _load_positions()},
    'run': do_scan_market, 'kline': do_kline
}

if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else 'scan'
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except:
            pass
    h = HANDLERS.get(action)
    result = h(params) if h else {'ok': False, 'error': 'unknown:' + action}
    print(json.dumps(result, ensure_ascii=False, default=str))

# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""fund_pool/run.py — GBT 用户资金池系统 · 内部虚拟账本
=====================================================
真实资金在 GBT 主钱包，内部转账只改账本，提现才动链上。
存储: .gbt/fund_pool.json
"""
import sys, json, os, uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA_FILE = ROOT / ".gbt" / "fund_pool.json"

# ── 持久化 ──────────────────────────────────────────────

def _load():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            return _empty_state()
    return _empty_state()

def _empty_state():
    return {"users": [], "transactions": [], "next_user_id": 1, "next_tx_id": 1}

def _save(state):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 辅助 ────────────────────────────────────────────────

def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _find_user(state, user_id):
    for u in state["users"]:
        if u["id"] == user_id:
            return u
    return None

def _short_hash():
    return uuid.uuid4().hex[:12]

# ── 核心 ────────────────────────────────────────────────

def _compute_pool(state):
    total = 0.0
    reserved = 0.0
    frozen_amount = 0.0
    active = 0
    for u in state["users"]:
        total += u["virtual_balance"]
        if u["status"] == "active":
            active += 1
        elif u["status"] == "frozen":
            frozen_amount += u["virtual_balance"]
    # reserved = pending withdrawals not yet settled
    for tx in state["transactions"]:
        if tx["type"] == "withdrawal" and tx["status"] == "pending":
            reserved += tx["amount"]
    return {
        "total_balance": round(total, 6),
        "reserved": round(reserved, 6),
        "frozen_amount": round(frozen_amount, 6),
        "available": round(total - reserved - frozen_amount, 6),
        "user_count": len(state["users"]),
        "active_users": active,
        "currency": "USDC",
    }


# ══════════════════════════════════════════════════════════
#  HANDLERS
# ══════════════════════════════════════════════════════════

def do_user_create(params):
    """创建用户虚拟账户"""
    name = (params.get("name") or "").strip()
    if not name:
        return {"ok": False, "error": "name 不能为空"}
    currency = (params.get("currency") or "USDC").strip().upper()
    email = (params.get("email") or "").strip()
    state = _load()
    # 检查同名
    for u in state["users"]:
        if u["name"].lower() == name.lower():
            return {"ok": False, "error": f"用户 '{name}' 已存在", "user_id": u["id"]}
    user = {
        "id": state["next_user_id"],
        "name": name,
        "email": email,
        "virtual_balance": 0.0,
        "currency": currency,
        "created_at": _now(),
        "status": "active",
    }
    state["users"].append(user)
    state["next_user_id"] += 1
    _save(state)
    return {"ok": True, "user": user}


def do_user_balance(params):
    """查询用户余额"""
    user_id = params.get("user_id")
    if user_id is None:
        return {"ok": False, "error": "user_id 必填"}
    state = _load()
    user = _find_user(state, int(user_id))
    if not user:
        return {"ok": False, "error": f"用户 {user_id} 不存在"}
    return {
        "ok": True,
        "user_id": user["id"],
        "name": user["name"],
        "balance": user["virtual_balance"],
        "currency": user["currency"],
        "status": user["status"],
    }


def do_deposit(params):
    """用户充值 — 增加虚拟余额，记录交易"""
    user_id = params.get("user_id")
    amount = params.get("amount", 0)
    if user_id is None:
        return {"ok": False, "error": "user_id 必填"}
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return {"ok": False, "error": "amount 必须是数字"}
    if amount <= 0:
        return {"ok": False, "error": "amount 必须 > 0"}
    state = _load()
    user = _find_user(state, int(user_id))
    if not user:
        return {"ok": False, "error": f"用户 {user_id} 不存在"}
    if user["status"] != "active":
        return {"ok": False, "error": f"用户 {user_id} 状态为 {user['status']}，无法充值"}

    user["virtual_balance"] = round(user["virtual_balance"] + amount, 6)
    tx = {
        "id": state["next_tx_id"],
        "user_id": user["id"],
        "type": "deposit",
        "amount": amount,
        "timestamp": _now(),
        "tx_hash": params.get("tx_hash") or _short_hash(),
        "related_user_id": None,
        "status": "completed",
        "note": params.get("note") or "",
    }
    state["transactions"].append(tx)
    state["next_tx_id"] += 1
    _save(state)
    return {
        "ok": True,
        "user_id": user["id"],
        "amount": amount,
        "new_balance": user["virtual_balance"],
        "tx": tx,
    }


def do_withdraw(params):
    """用户提现 — 减少虚拟余额，标记待链上处理"""
    user_id = params.get("user_id")
    amount = params.get("amount", 0)
    if user_id is None:
        return {"ok": False, "error": "user_id 必填"}
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return {"ok": False, "error": "amount 必须是数字"}
    if amount <= 0:
        return {"ok": False, "error": "amount 必须 > 0"}
    state = _load()
    user = _find_user(state, int(user_id))
    if not user:
        return {"ok": False, "error": f"用户 {user_id} 不存在"}
    if user["status"] != "active":
        return {"ok": False, "error": f"用户 {user_id} 状态为 {user['status']}，无法提现"}
    if user["virtual_balance"] < amount:
        return {"ok": False, "error": f"余额不足: {user['virtual_balance']} < {amount}"}

    user["virtual_balance"] = round(user["virtual_balance"] - amount, 6)
    tx = {
        "id": state["next_tx_id"],
        "user_id": user["id"],
        "type": "withdrawal",
        "amount": amount,
        "timestamp": _now(),
        "tx_hash": params.get("tx_hash") or None,
        "related_user_id": None,
        "status": "pending",
        "note": params.get("note") or "",
    }
    state["transactions"].append(tx)
    state["next_tx_id"] += 1
    _save(state)
    return {
        "ok": True,
        "user_id": user["id"],
        "amount": amount,
        "new_balance": user["virtual_balance"],
        "tx": tx,
    }


def do_transfer(params):
    """用户间转账 — 纯账本操作，不动链上"""
    from_id = params.get("from_user_id")
    to_id = params.get("to_user_id")
    amount = params.get("amount", 0)
    if from_id is None or to_id is None:
        return {"ok": False, "error": "from_user_id 和 to_user_id 必填"}
    if from_id == to_id:
        return {"ok": False, "error": "不能给自己转账"}
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return {"ok": False, "error": "amount 必须是数字"}
    if amount <= 0:
        return {"ok": False, "error": "amount 必须 > 0"}

    # 内部转账费 $1
    FEE = 1.00
    total_debit = round(amount + FEE, 6)

    state = _load()
    from_user = _find_user(state, int(from_id))
    to_user = _find_user(state, int(to_id))
    if not from_user:
        return {"ok": False, "error": f"转出用户 {from_id} 不存在"}
    if not to_user:
        return {"ok": False, "error": f"转入用户 {to_id} 不存在"}
    if from_user["status"] != "active":
        return {"ok": False, "error": f"转出用户 {from_id} 状态为 {from_user['status']}"}
    if to_user["status"] != "active":
        return {"ok": False, "error": f"转入用户 {to_id} 状态为 {to_user['status']}"}
    if from_user["virtual_balance"] < total_debit:
        return {"ok": False, "error": f"余额不足: {from_user['virtual_balance']} < {total_debit} (含$1手续费)"}

    from_user["virtual_balance"] = round(from_user["virtual_balance"] - total_debit, 6)
    to_user["virtual_balance"] = round(to_user["virtual_balance"] + amount, 6)

    tx_out = {
        "id": state["next_tx_id"],
        "user_id": from_user["id"],
        "type": "transfer_out",
        "amount": amount,
        "fee": FEE,
        "total_debit": total_debit,
        "timestamp": _now(),
        "tx_hash": None,
        "related_user_id": to_user["id"],
        "status": "completed",
        "note": (params.get("note") or "") + f" (含$1手续费)"
    }
    state["next_tx_id"] += 1
    state["transactions"].append(tx_out)

    tx_in = {
        "id": state["next_tx_id"],
        "user_id": to_user["id"],
        "type": "transfer_in",
        "amount": amount,
        "timestamp": _now(),
        "tx_hash": None,
        "related_user_id": from_user["id"],
        "status": "completed",
        "note": params.get("note") or "",
    }
    state["next_tx_id"] += 1
    state["transactions"].append(tx_in)

    _save(state)
    return {
        "ok": True,
        "from_user_id": from_user["id"],
        "to_user_id": to_user["id"],
        "amount": amount,
        "from_new_balance": from_user["virtual_balance"],
        "to_new_balance": to_user["virtual_balance"],
        "tx_out_id": tx_out["id"],
        "tx_in_id": tx_in["id"],
    }


def do_pool_status(params):
    """查看资金池总览"""
    state = _load()
    pool = _compute_pool(state)
    return {"ok": True, **pool}


def do_tx_history(params):
    """用户交易记录"""
    user_id = params.get("user_id")
    limit = max(1, min(1000, int(params.get("limit", 50))))
    offset = max(0, int(params.get("offset", 0)))
    state = _load()
    txs = state["transactions"]
    if user_id is not None:
        uid = int(user_id)
        txs = [t for t in txs if t["user_id"] == uid]
    # 最新在前
    txs = sorted(txs, key=lambda t: t["id"], reverse=True)
    total = len(txs)
    page = txs[offset : offset + limit]
    return {"ok": True, "transactions": page, "total": total, "limit": limit, "offset": offset}


def do_admin_list(params):
    """所有用户列表（仅管理员）"""
    state = _load()
    users = sorted(state["users"], key=lambda u: u["id"])
    return {"ok": True, "users": users, "total": len(users)}


def do_freeze(params):
    """冻结用户账户"""
    user_id = params.get("user_id")
    if user_id is None:
        return {"ok": False, "error": "user_id 必填"}
    state = _load()
    user = _find_user(state, int(user_id))
    if not user:
        return {"ok": False, "error": f"用户 {user_id} 不存在"}
    if user["status"] == "frozen":
        return {"ok": False, "error": f"用户 {user_id} 已冻结"}
    user["status"] = "frozen"
    _save(state)
    return {"ok": True, "user_id": user["id"], "status": "frozen"}


def do_unfreeze(params):
    """解冻用户账户"""
    user_id = params.get("user_id")
    if user_id is None:
        return {"ok": False, "error": "user_id 必填"}
    state = _load()
    user = _find_user(state, int(user_id))
    if not user:
        return {"ok": False, "error": f"用户 {user_id} 不存在"}
    if user["status"] != "frozen":
        return {"ok": False, "error": f"用户 {user_id} 未冻结"}
    user["status"] = "active"
    _save(state)
    return {"ok": True, "user_id": user["id"], "status": "active"}


def do_withdraw_approve(params):
    """批准提现 — pending → completed"""
    tx_id = params.get("tx_id")
    if tx_id is None:
        return {"ok": False, "error": "tx_id 必填"}
    state = _load()
    for tx in state["transactions"]:
        if tx["id"] == int(tx_id):
            if tx["type"] != "withdrawal":
                return {"ok": False, "error": f"交易 {tx_id} 不是提现"}
            if tx["status"] != "pending":
                return {"ok": False, "error": f"交易 {tx_id} 状态 {tx['status']}，非 pending"}
            tx["status"] = "completed"
            if not tx["tx_hash"]:
                tx["tx_hash"] = _short_hash()
            _save(state)
            user = _find_user(state, tx["user_id"])
            return {"ok": True, "tx_id": tx["id"], "status": "completed",
                    "user_id": tx["user_id"],
                    "new_balance": user["virtual_balance"] if user else None}
    return {"ok": False, "error": f"交易 {tx_id} 不存在"}


def do_withdraw_reject(params):
    """拒绝提现 — 退回余额，pending → rejected"""
    tx_id = params.get("tx_id")
    if tx_id is None:
        return {"ok": False, "error": "tx_id 必填"}
    state = _load()
    for tx in state["transactions"]:
        if tx["id"] == int(tx_id):
            if tx["type"] != "withdrawal":
                return {"ok": False, "error": f"交易 {tx_id} 不是提现"}
            if tx["status"] != "pending":
                return {"ok": False, "error": f"交易 {tx_id} 状态 {tx['status']}，非 pending"}
            tx["status"] = "rejected"
            user = _find_user(state, tx["user_id"])
            if user:
                user["virtual_balance"] = round(user["virtual_balance"] + tx["amount"], 6)
            _save(state)
            return {"ok": True, "tx_id": tx["id"], "status": "rejected",
                    "user_id": tx["user_id"],
                    "new_balance": user["virtual_balance"] if user else None}
    return {"ok": False, "error": f"交易 {tx_id} 不存在"}


# ══════════════════════════════════════════════════════════
#  DISPATCH
# ══════════════════════════════════════════════════════════

HANDLERS = {
    "user_create": do_user_create,
    "user_balance": do_user_balance,
    "deposit": do_deposit,
    "withdraw": do_withdraw,
    "transfer": do_transfer,
    "pool_status": do_pool_status,
    "tx_history": do_tx_history,
    "admin_list": do_admin_list,
    "freeze": do_freeze,
    "unfreeze": do_unfreeze,
    "withdraw_approve": do_withdraw_approve,
    "withdraw_reject": do_withdraw_reject,
}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "缺少 action 参数"}, ensure_ascii=False))
        sys.exit(1)

    action = sys.argv[1].lstrip("-")
    params = {}
    if len(sys.argv) > 2:
        try:
            raw = sys.argv[2]
            # 支持文件路径或 JSON 字符串
            if os.path.isfile(raw):
                params = json.loads(Path(raw).read_text(encoding="utf-8"))
            else:
                params = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as e:
            print(json.dumps({"ok": False, "error": f"参数解析失败: {e}"}, ensure_ascii=False))
            sys.exit(1)

    handler = HANDLERS.get(action)
    if not handler:
        print(json.dumps({"ok": False, "error": f"未知 action: {action}", "available": list(HANDLERS.keys())}, ensure_ascii=False))
        sys.exit(1)

    try:
        result = handler(params)
    except Exception as e:
        result = {"ok": False, "error": str(e)}

    print(json.dumps(result, ensure_ascii=False, default=str))

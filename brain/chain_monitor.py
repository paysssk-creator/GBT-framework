# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/chain_monitor.py — 区块链入账监控 (TRON USDT)
=====================================================
监控TP钱包USDT入账 → 识别Memo → 自动加虚拟余额
注意: 这是区块链(blockchain)入账监控，不是执行链(execution chain)监控。
"""
import sys, json, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

MONITOR_DIR = Path.home() / ".gbt" / "chain_monitor"
MONITOR_DIR.mkdir(parents=True, exist_ok=True)

AUTO_APPROVE_LIMIT = 1000
PENDING_FILE = MONITOR_DIR / "pending_withdrawals.json"

# Master TP Wallet
MASTER_WALLET = "TTML7MEQZh8iwqXZcrnrcRXF4ZL62Ln2B2"
TRON_API = "https://api.trongrid.io"

# Virtual user balances (in production this would be DB)
BALANCES_FILE = MONITOR_DIR / "balances.json"
TX_LOG = MONITOR_DIR / "transactions.jsonl"


class ChainMonitor:
    """链上监控 — 自动检测入账"""

    def __init__(self):
        from brain.chain_kernel import enforce_chain
        enforce_chain("chain_monitor.init")
        self.balances = self._load_balances()
        self.last_tx = self._load_last_tx()

    def _load_balances(self) -> dict:
        if BALANCES_FILE.exists():
            try: return json.loads(BALANCES_FILE.read_text(encoding="utf-8"))
            except: pass
        return {}

    def _save_balances(self):
        BALANCES_FILE.write_text(json.dumps(self.balances, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_last_tx(self) -> str:
        if TX_LOG.exists():
            lines = TX_LOG.read_text(encoding="utf-8").strip().split("\n")
            if lines:
                try: return json.loads(lines[-1]).get("txid", "")
                except: pass
        return ""

    def _api(self, path: str) -> dict:
        try:
            url = f"{TRON_API}{path}"
            req = urllib.request.Request(url, headers={"User-Agent": "GBT-ChainMonitor/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)[:200]}

    def check_deposits(self) -> dict:
        from brain.chain_kernel import enforce_chain
        enforce_chain("chain_monitor.check_deposits")
        """检查TP钱包新入账"""
        # Query TRC20 USDT transfers to master wallet
        path = f"/v1/accounts/{MASTER_WALLET}/transactions/trc20?limit=20"
        data = self._api(path)

        if "error" in data:
            return {"ok": False, "error": data["error"]}

        new_deposits = []
        tx_list = data.get("data", [])

        for tx in tx_list:
            txid = tx.get("transaction_id", "")
            if txid == self.last_tx:
                break

            # Parse TRC20 transfer
            token_info = tx.get("token_info", {})
            to_addr = tx.get("to", "")
            from_addr = tx.get("from", "")
            amount_raw = tx.get("value", "0")

            # Only count deposits TO master wallet (TRC20 USDT)
            if to_addr != MASTER_WALLET:
                continue

            try:
                amount = int(amount_raw) / 1_000_000  # USDT has 6 decimals
            except:
                amount = 0

            # Extract memo/user_id from transaction data
            memo = tx.get("raw_data", {}).get("data", "")
            if memo:
                try:
                    memo_decoded = bytes.fromhex(memo).decode("utf-8", errors="replace")
                except:
                    memo_decoded = memo

            deposit = {
                "txid": txid,
                "from": from_addr,
                "to": to_addr,
                "amount": round(amount, 2),
                "memo": memo_decoded[:50] if memo else "",
                "timestamp": datetime.now().isoformat(),
            }
            new_deposits.append(deposit)

            # Credit user
            user_id = self._resolve_user(from_addr, memo_decoded if memo else "")
            if user_id:
                self.balances[user_id] = self.balances.get(user_id, 0) + amount
                deposit["user_id"] = user_id
                deposit["credited"] = True

            # Log
            with open(TX_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(deposit, ensure_ascii=False) + "\n")

        if new_deposits:
            self.last_tx = new_deposits[0]["txid"]
            self._save_balances()

        return {
            "ok": True,
            "new_deposits": len(new_deposits),
            "deposits": new_deposits[:5],
            "total_balance": sum(self.balances.values()),
            "user_count": len(self.balances),
        }

    def _resolve_user(self, from_addr: str, memo: str) -> str:
        """根据memo或地址识别用户"""
        if memo and len(memo) >= 10:
            # Memo contains user ID hash
            for uid in self.balances:
                if uid[:10] in memo or memo[:10] in uid:
                    return uid
        # Map address to user (if known)
        return ""

    def get_balance(self, user_id: str) -> dict:
        return {
            "ok": True,
            "user_id": user_id,
            "balance": self.balances.get(user_id, 0),
            "currency": "USDT",
            "chain": "TRON (TRC20)",
            "master_wallet": MASTER_WALLET,
        }

    def get_virtual_card(self, user_id: str) -> dict:
        """用户虚拟卡信息"""
        addr = self._get_user_memo(user_id)
        return {
            "ok": True,
            "user_id": user_id,
            "card_number": f"GBT-{user_id[:8].upper()}",
            "balance": self.balances.get(user_id, 0),
            "currency": "USDT",
            "deposit_address": MASTER_WALLET,
            "deposit_memo": addr,
            "deposit_note": f"转账时Memo必须填: {addr}",
            "chain": "TRON (TRC20)",
            "status": "active",
        }

    def _get_user_memo(self, user_id: str) -> str:
        import hashlib
        return hashlib.sha256(f"gbt_user_{user_id}".encode()).hexdigest()[:20]


# Global

    def request_withdraw(self, user_id: str, amount: float, to_address: str) -> dict:
        from brain.chain_kernel import enforce_chain
        enforce_chain("chain_monitor.request_withdraw")
        balance = self.balances.get(user_id, 0)
        if amount > balance:
            return {"ok": False, "error": f"余额不足: {balance} USDT"}
        if amount <= 0:
            return {"ok": False, "error": "金额必须大于0"}

        self.balances[user_id] = balance - amount
        self._save_balances()

        import time as _time
        req = {
            "id": f"wd_{int(_time.time())}",
            "user_id": user_id,
            "amount": amount,
            "to_address": to_address,
            "status": "auto_approved" if amount < AUTO_APPROVE_LIMIT else "pending_confirm",
            "timestamp": datetime.now().isoformat(),
        }

        if req["status"] == "pending_confirm":
            pending = self._load_pending()
            pending.append(req)
            self._save_pending(pending)
            return {"ok": True, "status": "pending_confirm",
                    "message": f"大额提现 ${amount} 需人工确认", "amount": amount}

        return {"ok": True, "status": "auto_approved",
                "message": f"小额提现 ${amount} 已自动批准", "amount": amount}

    def _load_pending(self):
        if PENDING_FILE.exists():
            try: return json.loads(PENDING_FILE.read_text(encoding="utf-8"))
            except: pass
        return []

    def _save_pending(self, data):
        PENDING_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_pending(self) -> list:
        return self._load_pending()
_monitor = None

def get_monitor() -> ChainMonitor:
    global _monitor
    if _monitor is None: _monitor = ChainMonitor()
    return _monitor


if __name__ == "__main__":
    m = get_monitor()

    # Show virtual cards for demo users
    for uid in ["user_001", "user_002", "user_003"]:
        card = m.get_virtual_card(uid)
        print(f"\n💳 GBT虚拟卡")
        print(f"  卡号: {card['card_number']}")
        print(f"  余额: {card['balance']} {card['currency']}")
        print(f"  充值: {card['deposit_address']}")
        print(f"  Memo: {card['deposit_memo']}")

    print(f"\n🔍 扫描入账...")
    r = m.check_deposits()
    print(f"  新入账: {r.get('new_deposits', 0)}笔")
    print(f"  总余额: {r.get('total_balance', 0)} USDT")
    print(f"  用户数: {r.get('user_count', 0)}")

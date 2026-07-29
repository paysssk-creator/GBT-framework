# 开发者：自由的风
"""encryption_engine/run.py — 加密引擎"""
import sys, json, os, hashlib, base64, secrets
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac, padding
from cryptography.hazmat.backends import default_backend

SANDBOX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _derive_key(password, salt=None, length=32):
    if salt is None: salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000, dklen=length)
    return key, salt

def do_encrypt(params):
    data = params.get("data", params.get("text", ""))
    password = params.get("password", params.get("key"))
    if not password:
        return {"ok": False, "error": "缺少 password 参数 — 加密必须提供密钥"}
    if not data: return {"ok": False, "error": "缺少data"}
    try:
        key, salt = _derive_key(password)
        iv = secrets.token_bytes(16)
        padder = padding.PKCS7(128).padder()
        padded = padder.update(data.encode()) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded) + encryptor.finalize()
        result = base64.b64encode(salt + iv + encrypted).decode()
        h = hashlib.sha256(data.encode()).hexdigest()[:16]
        return {"ok": True, "cap": "encryption_engine", "domain": "安全域",
                "encrypted": result[:200] + "...[{}B]".format(len(result)),
                "algorithm": "AES-256-CBC", "original_hash": h, "size": len(result)}
    except ImportError:
        return {"ok": False, "error": "cryptography未安装"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_decrypt(params):
    encrypted_b64 = params.get("encrypted", params.get("data", ""))
    password = params.get("password", params.get("key"))
    if not password:
        return {"ok": False, "error": "缺少 password 参数 — 解密必须提供密钥"}
    if not encrypted_b64: return {"ok": False, "error": "缺少encrypted"}
    try:
        raw = base64.b64decode(encrypted_b64)
        salt, iv, ciphertext = raw[:16], raw[16:32], raw[32:]
        key, _ = _derive_key(password, salt)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded) + unpadder.finalize()
        return {"ok": True, "decrypted": plaintext.decode(), "size": len(plaintext)}
    except ImportError:
        return {"ok": False, "error": "cryptography未安装"}
    except Exception as e:
        return {"ok": False, "error": "解密失败(密钥错误或数据损坏): {}".format(str(e)[:100])}

def do_hash(params):
    data = params.get("data", "")
    algo = params.get("algo", "sha256")
    h = hashlib.new(algo, data.encode())
    return {"ok": True, "algorithm": algo, "hash": h.hexdigest()}

HANDLERS = {"encrypt": do_encrypt, "decrypt": do_decrypt, "hash": do_hash}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "encrypt"
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    r = HANDLERS.get(action, lambda p: {"ok": False})(params)
    print(json.dumps(r, ensure_ascii=False, default=str))

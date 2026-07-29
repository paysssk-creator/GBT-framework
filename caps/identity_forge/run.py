# 开发者：自由的风
"""identity_forge/run.py — 身份信息生成"""
import sys, json, random, string, hashlib
SANDBOX = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))

FIRST_NAMES = ["James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda","David","Elizabeth","William","Barbara","Richard","Susan","Joseph","Jessica","Thomas","Sarah","Charles","Karen"]
LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin"]
DOMAINS = ["gmail.com","outlook.com","proton.me","yahoo.com","mail.com","icloud.com","hotmail.com","live.com"]

def _gen_ssn(): return "{:03d}-{:02d}-{:04d}".format(random.randint(100,899), random.randint(1,99), random.randint(1,9999))
def _gen_dob(): return "{:04d}-{:02d}-{:02d}".format(random.randint(1950,2005), random.randint(1,12), random.randint(1,28))
def _gen_phone(): return "+1-{:03d}-{:03d}-{:04d}".format(random.randint(200,999), random.randint(200,999), random.randint(1000,9999))
def _gen_passport(): return "".join(random.choices(string.ascii_uppercase+string.digits, k=9))

def do_generate(params):
    count = params.get("count", 1)
    identities = []
    for _ in range(count):
        fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        email = "{}.{}{}@{}".format(fn.lower(), ln.lower(), random.randint(1,999), random.choice(DOMAINS))
        identities.append({
            "first_name": fn, "last_name": ln, "full_name": fn+" "+ln,
            "email": email, "phone": _gen_phone(), "dob": _gen_dob(),
            "ssn": _gen_ssn(), "passport": _gen_passport(),
            "username": (fn[0]+ln).lower()+str(random.randint(10,999)),
            "password": "".join(random.choices(string.ascii_letters+string.digits+"!@#$", k=16)),
        })
    return {"ok": True, "cap": "identity_forge", "domain": "特殊域",
            "generated": count, "identities": identities}

HANDLERS = {"generate": do_generate}
if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv)>1 else "generate"
    p = json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
    r = HANDLERS.get(a, lambda p:{"ok":False})(p)
    print(json.dumps(r, ensure_ascii=False, default=str))

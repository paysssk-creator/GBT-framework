# 开发者：自由的风
"""osint_master/run.py — 综合OSINT开源情报·四源聚合
侦察域 — 对标SpiderFoot/Maltego:搜索/dns/社交/泄露/邮箱五通道
互补工具: pentest_kali, subdomain_enum, port_scanner, darknet_scanner"""
import sys, json, os, re, ssl, socket, hashlib, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from pathlib import Path
SHODAN_API_KEY = os.environ.get("SHODAN_API_KEY", "")
HIBP_API_KEY = os.environ.get("HIBP_API_KEY", "")
COMPANION_TOOLS = {"pentest_kali":"Kali容器渗透","subdomain_enum":"子域名枚举",
    "port_scanner":"端口探测","darknet_scanner":"暗网监控",
    "dir_buster":"目录爆破","location_tracker":"IP定位"}

def _http_get(url, headers=None, timeout=12, json_out=True):
    if headers is None: headers = {"User-Agent": "GBT-OSINT/5.0"}
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=headers)
            ctx = ssl.create_default_context()
            resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body) if json_out else body
        except Exception:
            if attempt == 1: return None
            time.sleep(0.5)
    return None

# ═══ search: 多引擎情报搜索 (Google dorking + Shodan + crt.sh + Wayback) ═══

def _google_dork(query, dork_type="site"):
    dorks = {"site": f"site:{query}", "file": f"site:{query} filetype:pdf OR filetype:doc OR filetype:xlsx",
             "login": f"site:{query} inurl:login OR inurl:admin",
             "sensitive": f"site:{query} intitle:\"index of\" OR intext:\"password\""}
    q = dorks.get(dork_type, dorks["site"])
    try:
        body = _http_get(f"https://www.google.com/search?q={urllib.request.quote(q)}",
                         headers={"User-Agent":"Mozilla/5.0"}, json_out=False)
        if body:
            return [{"snippet": re.sub(r'<[^>]+>','',s).strip()[:300], "dork": dork_type}
                    for s in re.findall(r'<div[^>]*class="[^"]*BNeawe[^"]*"[^>]*>(.*?)</div>', body)[:10]
                    if len(re.sub(r'<[^>]+>','',s).strip()) > 10]
    except: pass
    return [{"dork_query": q, "note": "Google dorking不可达"}]

def _shodan_search(target):
    if not SHODAN_API_KEY: return [{"error": "SHODAN_API_KEY未配置"}]
    try:
        data = _http_get(f"https://api.shodan.io/shodan/host/search?key={SHODAN_API_KEY}"
                         f"&query={urllib.request.quote(target)}&minify=true", timeout=20)
        if data and "matches" in data:
            return [{"ip":m.get("ip_str",""),"port":m.get("port",0),"org":m.get("org",""),
                     "hostnames":m.get("hostnames",[])[:3],"os":m.get("os",""),
                     "banner":(m.get("data","")or"")[:200]} for m in data["matches"][:8]]
    except Exception as e: return [{"error": f"Shodan: {str(e)[:100]}"}]
    return []

def _crtsh_search(domain):
    try:
        data = _http_get(f"https://crt.sh/?q=%25.{domain}&output=json", timeout=20)
        if data:
            seen, results = set(), []
            for e in data[:50]:
                for n in e.get("name_value","").split("\n"):
                    n = n.strip().lstrip("*.")
                    if n and n not in seen:
                        seen.add(n)
                        results.append({"domain":n,"issuer":(e.get("issuer_name","")or"")[:100],
                                        "logged":e.get("entry_timestamp","")[:10]})
            return results
    except: pass
    return [{"note": "crt.sh不可达"}]

def _wayback_search(domain):
    try:
        data = _http_get(f"https://web.archive.org/cdx/search/cdx?url={domain}/*"
                         f"&output=json&fl=timestamp,original,statuscode&collapse=urlkey&limit=30", timeout=25)
        if data: return [{"ts":r[0],"url":r[1],"status":r[2]} for r in data[1:31]]
    except: pass
    return [{"note": "Wayback Machine不可达"}]

def do_search(params):
    target = (params.get("target") or params.get("query") or params.get("domain") or "").strip()
    if not target: return {"ok": False, "error": "缺少 target/query/domain"}
    dork_type = params.get("dork_type", "site")
    engines = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        fut = {ex.submit(f, target): n for f, n in
               [(_google_dork, "google"), (_shodan_search, "shodan"),
                (_crtsh_search, "crtsh"), (_wayback_search, "wayback")]}
        for f in as_completed(fut): engines[fut[f]] = f.result()
    return {"ok": True, "cap": "osint_master", "action": "search", "domain": "侦察域",
            "target": target, "timestamp": datetime.now().isoformat(),
            "engines": list(engines.keys()), "results": engines}

# ═══ dns: 完整DNS侦察 (A/AAAA/MX/NS/TXT/SOA/CNAME + AXFR) ═══

def _dns_resolve(domain, rtype, timeout=5):
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, rtype, lifetime=timeout)
        if rtype == "MX":
            return [{"pref":r.preference,"ex":str(r.exchange).rstrip(".")} for r in answers]
        if rtype == "SOA":
            r = answers[0]
            return {"mname":str(r.mname).rstrip("."),"rname":str(r.rname).rstrip("."),
                    "serial":r.serial,"refresh":r.refresh,"retry":r.retry,
                    "expire":r.expire,"minimum":r.minimum}
        return [str(r).rstrip(".") for r in answers]
    except Exception:
        try:  # socket降级
            af = socket.AF_INET if rtype == "A" else socket.AF_INET6
            return [a[4][0] for a in socket.getaddrinfo(domain, None, family=af) if a[4][0]][:5]
        except: return None

def _dns_axfr(domain, ns_list):
    if not ns_list or not isinstance(ns_list, list): return None
    for ns in ns_list[:3]:
        try:
            ns_ip = ns if re.match(r'^\d+\.\d+\.\d+\.\d+$', ns) else socket.getaddrinfo(ns,53)[0][4][0]
            import dns.query, dns.zone
            zone = dns.zone.from_xfr(dns.query.xfr(ns_ip, domain, timeout=8, lifetime=10))
            return [str(n) for n in sorted(zone.nodes.keys())[:50]]
        except: continue
    return None

def do_dns(params):
    target = (params.get("domain") or params.get("target") or "").strip().lower()
    target = target.replace("http://","").replace("https://","").rstrip("/")
    if not target or "." not in target: return {"ok": False, "error": "需要有效 domain"}
    records, ns = {}, []
    for rt in ["A","AAAA","MX","NS","TXT","SOA","CNAME"]:
        r = _dns_resolve(target, rt)
        records[rt] = r if r is not None else []
        if rt == "NS" and isinstance(r, list): ns = r
    axfr = _dns_axfr(target, ns)
    if axfr: records["AXFR"] = axfr
    whois_info = {}
    try:
        data = _http_get(f"https://rdap.verisign.com/domain/v1/{target}", timeout=10)
        if data:
            whois_info = {"ldh":data.get("ldhName",""), "status":data.get("status",[]),
                "entities":[{"role":e.get("roles",[""])[0], "name":
                    e.get("vcardArray",[[],[]])[-1][-1][-1] if len(e.get("vcardArray",[[],[]]))>1 else ""}
                    for e in data.get("entities",[])[:5]]}
    except: whois_info = {"note": "RDAP失败"}
    return {"ok": True, "cap": "osint_master", "action": "dns", "domain": "侦察域",
            "target": target, "timestamp": datetime.now().isoformat(),
            "records": records, "whois": whois_info, "axfr_attempted": bool(ns)}

# ═══ social: 社交媒体档案 (Twitter/X + GitHub + LinkedIn) ═══

def _social_twitter(username):
    try:
        body = _http_get(f"https://nitter.net/{username}/rss", json_out=False, timeout=10)
        if body and "<?xml" in body:
            posts = []
            for item in re.findall(r'<item>(.*?)</item>', body, re.DOTALL)[:5]:
                t = re.search(r'<title>(.*?)</title>', item)
                l = re.search(r'<link>(.*?)</link>', item)
                d = re.search(r'<pubDate>(.*?)</pubDate>', item)
                if t: posts.append({"title":t.group(1)[:200],
                    "link":l.group(1) if l else "", "date":d.group(1) if d else ""})
            return {"platform":"twitter/x","url":f"https://x.com/{username}","posts":posts}
    except: pass
    return {"platform":"twitter/x","url":f"https://x.com/{username}","note":"不可达或无活动"}

def _social_github(username):
    try:
        data = _http_get(f"https://api.github.com/users/{username}", timeout=10)
        if data and "login" in data:
            repos = _http_get(data.get("repos_url","")+"?per_page=10&sort=updated", timeout=10) or []
            return {"platform":"github","url":data.get("html_url",""),"name":data.get("name",""),
                    "bio":(data.get("bio","")or"")[:300],"company":data.get("company",""),
                    "location":data.get("location",""),"repos":data.get("public_repos",0),
                    "followers":data.get("followers",0),
                    "recent":[{"name":r.get("name",""),"desc":(r.get("description","")or"")[:200],
                               "lang":r.get("language",""),"stars":r.get("stargazers_count",0)}
                              for r in repos[:5]]}
    except: pass
    return {"platform":"github","url":f"https://github.com/{username}","note":"不可达"}

def _social_linkedin(username):
    try:
        body = _http_get(f"https://www.google.com/search?q=site%3Alinkedin.com%2Fin%2F+%22{username}%22",
                         headers={"User-Agent":"Mozilla/5.0"}, json_out=False, timeout=12)
        links = list(set(re.findall(r'https://[a-z]{2,3}\.linkedin\.com/in/[^"&\s<>]+', body or "")))[:5]
        return {"platform":"linkedin","profiles":[{"url":l} for l in links]} if links else \
               {"platform":"linkedin","note":"无公开匹配"}
    except: return {"platform":"linkedin","note":"不可达"}

def do_social(params):
    username = (params.get("username") or params.get("handle") or params.get("target") or "").strip()
    if not username: return {"ok": False, "error": "缺少 username/handle/target"}
    res = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        fut = {ex.submit(f, username): n for f, n in
               [(_social_twitter,"twitter"), (_social_github,"github"), (_social_linkedin,"linkedin")]}
        for f in as_completed(fut): res[fut[f]] = f.result()
    return {"ok": True, "cap": "osint_master", "action": "social", "domain": "侦察域",
            "username": username, "timestamp": datetime.now().isoformat(), "profiles": res}

# ═══ breach: HaveIBeenPwned v3 泄露库检查 ═══

def do_breach(params):
    email = (params.get("email") or params.get("target") or "").strip().lower()
    domain = params.get("domain", "").strip().lower()
    if not email and not domain: return {"ok": False, "error": "需要 email 或 domain"}
    if not HIBP_API_KEY:
        return {"ok": True, "cap": "osint_master", "action": "breach", "domain": "侦察域",
                "target": email or domain, "timestamp": datetime.now().isoformat(),
                "results": {"note": "HIBP_API_KEY未配置 — 设置环境变量启用"}, "hibp_ok": False}
    hdrs = {"hibp-api-key": HIBP_API_KEY, "User-Agent": "GBT-OSINT/5.0", "Accept": "application/json"}
    br = {}
    if email:
        try:
            data = _http_get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
                             f"?truncateResponse=false", headers=hdrs, timeout=15)
            if data:
                br["breaches"] = [{"name":b.get("Name",""),"title":b.get("Title",""),
                    "domain":b.get("Domain",""),"date":b.get("BreachDate",""),
                    "classes":b.get("DataClasses",[])[:10],"pwned":b.get("PwnCount",0),
                    "verified":b.get("IsVerified",False)} for b in data]
                br["count"] = len(br["breaches"])
            else: br["breaches"] = []; br["count"] = 0; br["note"] = "未在已知泄露中出现 ✓"
        except Exception as e: br["error"] = str(e)[:100]
        # k-anonymity 密码泄露
        try:
            h = hashlib.sha1(email.encode()).hexdigest().upper()
            body = _http_get(f"https://api.pwnedpasswords.com/range/{h[:5]}",
                             headers={"User-Agent":"GBT-OSINT"}, json_out=False, timeout=10)
            if body:
                for line in body.strip().split("\n"):
                    s, c = line.split(":")[:2]
                    if h[5:] == s: br["pass_pwned"] = True; br["pass_count"] = int(c); break
                else: br["pass_pwned"] = False
        except: br["pass_pwned"] = None
    if domain:
        try:
            data = _http_get(f"https://haveibeenpwned.com/api/v3/breaches?domain={domain}",
                             headers=hdrs, timeout=15)
            if data:
                br["domain_breaches"] = [{"name":b.get("Name",""),"title":b.get("Title",""),
                    "date":b.get("BreachDate",""),"pwned":b.get("PwnCount",0)} for b in data[:20]]
        except Exception as e: br["domain_error"] = str(e)[:100]
    return {"ok": True, "cap": "osint_master", "action": "breach", "domain": "侦察域",
            "target": email or domain, "timestamp": datetime.now().isoformat(),
            "results": br, "hibp_ok": True}

# ═══ email: 邮箱OSINT (pattern推断 + 验证 + SPF/DMARC追踪) ═══

def _email_patterns(domain):
    fmts = [f.replace("{d}", domain) for f in
            ["{first}.{last}@{d}","{first}{last}@{d}","{f}{last}@{d}",
             "{first}{l}@{d}","{first}_{last}@{d}","{last}.{first}@{d}"]]
    found = []
    try:
        body = _http_get(f"https://www.google.com/search?q=%22%40{domain}%22+email",
                         headers={"User-Agent":"Mozilla/5.0"}, json_out=False, timeout=12)
        if body: found = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@'+re.escape(domain), body)))[:10]
    except: pass
    return {"domain": domain, "templates": fmts, "found": found}

def _verify_email(email):
    domain = email.split("@")[-1]
    fmt_ok = bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))
    mx = False
    try:
        import dns.resolver; dns.resolver.resolve(domain, "MX", lifetime=4); mx = True
    except:
        try: socket.getaddrinfo(domain, 25); mx = True
        except: pass
    return {"email": email, "valid_format": fmt_ok, "domain": domain, "mx_exists": mx}

def _trace_email(email):
    domain = email.split("@")[-1]; res = {}
    try:
        for r in (_dns_resolve(domain, "TXT") or []):
            s = r if isinstance(r, str) else str(r)
            if "v=spf1" in s: res["spf"] = s; break
    except: pass
    try:
        for r in (_dns_resolve(f"_dmarc.{domain}", "TXT") or []):
            s = r if isinstance(r, str) else str(r)
            if "v=DMARC1" in s: res["dmarc"] = s; break
    except: pass
    return res

def do_email(params):
    email = (params.get("email") or params.get("target") or "").strip().lower()
    domain = (params.get("domain") or "").strip().lower()
    if email and "@" in email:
        domain = email.split("@")[-1]
        return {"ok": True, "cap": "osint_master", "action": "email", "domain": "侦察域",
                "email": email, "timestamp": datetime.now().isoformat(),
                "verify": _verify_email(email), "trace": _trace_email(email),
                "patterns": _email_patterns(domain)}
    if domain:
        return {"ok": True, "cap": "osint_master", "action": "email", "domain": "侦察域",
                "target_domain": domain, "timestamp": datetime.now().isoformat(),
                "patterns": _email_patterns(domain),
                "note": "提供 email 参数可进行完整验证和来源追踪"}
    return {"ok": False, "error": "需要 email 或 domain"}

# ═══ autonomous_recon: 五通道全自动侦察 ═══

def do_autonomous_recon(params):
    """全自动侦察 — 同时运行所有5个通道并聚合结果"""
    target = (params.get("target") or params.get("query") or params.get("domain") or "").strip()
    if not target:
        return {"ok": False, "error": "需要 target/query/domain"}
    channels = {
        "search": lambda: do_search({"target": target}),
        "dns": lambda: do_dns({"domain": target, "target": target}),
        "social": lambda: do_social({"username": target, "target": target}),
        "breach": lambda: do_breach({"email": target, "target": target}),
        "email": lambda: do_email({"email": target, "target": target}),
    }
    results = {}
    errors = []
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(fn): ch for ch, fn in channels.items()}
        for f in as_completed(futures):
            ch = futures[f]
            try:
                results[ch] = f.result(timeout=60)
            except Exception as e:
                errors.append({"channel": ch, "error": str(e)[:200]})
                results[ch] = {"error": str(e)[:200]}
    return {
        "ok": True,
        "cap": "osint_master",
        "action": "autonomous_recon",
        "domain": "侦察域",
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "channels_completed": list(results.keys()),
        "channels_failed": [e["channel"] for e in errors],
        "results": results,
        "errors": errors if errors else None,
    }

# ═══ scheduled_scan: 定期变更检测 ═══

_SCAN_DIR = Path.home() / ".gbt" / "osint_master" / "scans"
_SCAN_DIR.mkdir(parents=True, exist_ok=True)

def _scan_key(target):
    return hashlib.sha256(target.encode()).hexdigest()[:16]

def _diff_dicts(prev, curr, path=""):
    changes = []
    if isinstance(prev, dict) and isinstance(curr, dict):
        all_keys = set(prev.keys()) | set(curr.keys())
        for k in all_keys:
            p = f"{path}.{k}" if path else k
            pv = prev.get(k)
            cv = curr.get(k)
            if pv != cv:
                if isinstance(pv, (dict, list)) and isinstance(cv, (dict, list)):
                    changes.extend(_diff_dicts(pv, cv, p))
                else:
                    changes.append({"field": p, "old": str(pv)[:200], "new": str(cv)[:200]})
    elif isinstance(prev, list) and isinstance(curr, list):
        if len(prev) != len(curr):
            changes.append({"field": f"{path}.length", "old": len(prev), "new": len(curr)})
        for i in range(min(len(prev), len(curr))):
            if prev[i] != curr[i]:
                changes.extend(_diff_dicts(prev[i], curr[i], f"{path}[{i}]"))
    return changes

def do_scheduled_scan(params):
    """定期扫描 — 运行全通道侦察并对比上次结果"""
    target = (params.get("target") or params.get("query") or params.get("domain") or "").strip()
    if not target:
        return {"ok": False, "error": "需要 target/query/domain"}
    current = do_autonomous_recon(params)
    if not current.get("ok"):
        return current
    key = _scan_key(target)
    scan_file = _SCAN_DIR / f"{key}.json"
    prev_data = None
    if scan_file.exists():
        try:
            prev_data = json.loads(scan_file.read_text(encoding="utf-8"))
        except Exception:
            prev_data = None
    # 保存当前结果
    scan_file.write_text(json.dumps(current, ensure_ascii=False, default=str), encoding="utf-8")
    # 对比差异
    diffs = []
    if prev_data:
        for ch in current.get("results", {}):
            prev_ch = prev_data.get("results", {}).get(ch, {})
            curr_ch = current["results"].get(ch, {})
            ch_diffs = _diff_dicts(prev_ch, curr_ch, ch)
            if ch_diffs:
                diffs.append({"channel": ch, "changes": len(ch_diffs), "details": ch_diffs[:30]})
    return {
        "ok": True,
        "cap": "osint_master",
        "action": "scheduled_scan",
        "domain": "侦察域",
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "scan_key": key,
        "scan_file": str(scan_file),
        "is_first_scan": prev_data is None,
        "previous_scan_time": prev_data.get("timestamp") if prev_data else None,
        "total_changes": sum(d.get("changes", 0) for d in diffs),
        "diffs": diffs if diffs else None,
        "current_results": current.get("results"),
    }

# ═══ intel_fusion: 情报融合统一报告 ═══

def do_intel_fusion(params):
    """情报融合 — 合并所有通道发现到统一报告，发现跨通道关联"""
    target = (params.get("target") or params.get("query") or params.get("domain") or "").strip()
    if not target:
        return {"ok": False, "error": "需要 target/query/domain"}
    recon = do_autonomous_recon(params)
    if not recon.get("ok"):
        return recon
    results = recon.get("results", {})
    # 提取关键发现
    findings = []
    domains_found = set()
    ips_found = set()
    emails_found = set()
    usernames_found = set()
    # 从各通道提取实体
    if "search" in results:
        sr = results["search"]
        engines = sr.get("engines", {})
        for eng_name, eng_data in engines.items():
            for item in (eng_data if isinstance(eng_data, list) else [eng_data]):
                if isinstance(item, dict) and item.get("dork_query"):
                    findings.append({"source": "search", "type": "dork", "channel": eng_name, "value": item["dork_query"]})
    if "dns" in results:
        dr = results["dns"]
        records = dr.get("records", {})
        for rtype, vals in records.items():
            if isinstance(vals, list):
                for v in vals:
                    if isinstance(v, str):
                        if rtype in ("A", "AAAA"):
                            ips_found.add(v)
                        elif rtype in ("MX", "CNAME", "NS"):
                            domains_found.add(v.rstrip("."))
        whois = dr.get("whois", {})
        if whois and whois.get("ldh"):
            domains_found.add(whois["ldh"])
    if "social" in results:
        sr2 = results["social"]
        for profile in sr2.get("profiles", []):
            username = sr2.get("username", "")
            if username:
                usernames_found.add(username)
            findings.append({"source": "social", "type": "profile", "channel": profile.get("platform", ""), "value": profile.get("url", "")})
    if "breach" in results:
        br = results["breach"]
        br_data = br.get("results", {})
        for b in br_data.get("breaches", []):
            findings.append({"source": "breach", "type": "breach", "channel": b.get("name", ""), "value": b.get("title", ""), "date": b.get("date", "")})
        for b in br_data.get("domain_breaches", []):
            findings.append({"source": "breach", "type": "domain_breach", "channel": b.get("name", ""), "value": b.get("title", "")})
    if "email" in results:
        er = results["email"]
        if er.get("ok"):
            ep = er.get("patterns", {})
            for tpl in ep.get("found", []):
                if isinstance(tpl, str):
                    emails_found.add(tpl)
    # 融合摘要
    risk_level = "low"
    if len(findings) > 20:
        risk_level = "high"
    elif len(findings) > 10:
        risk_level = "medium"
    # 实体关联图
    entities = {
        "target": target,
        "domains": sorted(list(domains_found - {target}))[:30],
        "ips": sorted(list(ips_found))[:30],
        "emails": sorted(list(emails_found))[:30],
        "usernames": sorted(list(usernames_found))[:20],
    }
    return {
        "ok": True,
        "cap": "osint_master",
        "action": "intel_fusion",
        "domain": "侦察域",
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "risk_level": risk_level,
        "total_findings": len(findings),
        "findings": findings[:50],
        "entities": entities,
        "summary": f"OSINT融合报告: {len(findings)}条发现, 风险等级{risk_level}, "
                    f"{len(entities['domains'])}关联域/{len(entities['ips'])}关联IP/"
                    f"{len(entities['emails'])}邮箱/{len(entities['usernames'])}用户名",
    }

HANDLERS = {"search": do_search, "dns": do_dns, "social": do_social,
            "breach": do_breach, "email": do_email,
            "autonomous_recon": do_autonomous_recon,
            "scheduled_scan": do_scheduled_scan,
            "intel_fusion": do_intel_fusion}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "search"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except json.JSONDecodeError: params = {"target": sys.argv[2]}
    handler = HANDLERS.get(action)
    if not handler:
        result = {"ok": False, "error": f"未知动作: {action}",
                  "available": list(HANDLERS.keys()), "companions": COMPANION_TOOLS}
    else:
        result = handler(params)
        result["companions"] = COMPANION_TOOLS
    print(json.dumps(result, ensure_ascii=False, default=str))

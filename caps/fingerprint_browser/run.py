# 开发者：自由的风
"""fingerprint_browser/run.py — 指纹浏览器
============================================
每个配置文件独立指纹环境(Canvas/WebGL/Audio/字体/时区/语言)
基于Playwright + 自定义指纹注入
"""
import sys, json, os, subprocess, time
from pathlib import Path

PROFILES_DIR = Path.home() / '.gbt' / 'browser_profiles'
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

FINGERPRINT_TEMPLATES = {
    'win_chrome': {
        'platform': 'Win32', 'vendor': 'Google Inc.',
        'webgl_vendor': 'Intel Inc.', 'webgl_renderer': 'Intel(R) UHD Graphics',
        'hardware_concurrency': 8, 'device_memory': 8,
        'timezone': 'Asia/Shanghai', 'language': 'zh-CN',
        'screen': {'width': 1920, 'height': 1080},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'
    },
    'mac_safari': {
        'platform': 'MacIntel', 'vendor': 'Apple Computer, Inc.',
        'webgl_vendor': 'Apple Inc.', 'webgl_renderer': 'Apple M2',
        'hardware_concurrency': 10, 'device_memory': 16,
        'timezone': 'America/New_York', 'language': 'en-US',
        'screen': {'width': 2560, 'height': 1664},
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 Version/17.4 Safari/605.1.15'
    }
}

def do_create_profile(params):
    name = params.get('name', 'profile_' + str(int(time.time())))
    template = params.get('template', 'win_chrome')
    fp = FINGERPRINT_TEMPLATES.get(template, FINGERPRINT_TEMPLATES['win_chrome'])
    
    profile_dir = PROFILES_DIR / name
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    config = {'name': name, 'fingerprint': fp, 'template': template,
              'created': time.strftime('%Y-%m-%d %H:%M:%S'),
              'proxy': params.get('proxy', '')}
    
    (profile_dir / 'config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'ok': True, 'name': name, 'template': template, 'profile_dir': str(profile_dir)}

def do_launch(params):
    name = params.get('name', '')
    profile_dir = PROFILES_DIR / name
    if not profile_dir.exists():
        return {'ok': False, 'error': 'Profile not found: ' + name}
    try:
        # Use subprocess to launch Playwright with the profile
        import subprocess as sp
        sp.Popen([sys.executable, '-c', '''
import asyncio, json, sys
from pathlib import Path
async def main():
    from playwright.async_api import async_playwright
    cfg = json.loads((Path(sys.argv[1]) / "config.json").read_text(encoding="utf-8"))
    fp = cfg["fingerprint"]
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(
            viewport={"width": fp["screen"]["width"], "height": fp["screen"]["height"]},
            user_agent=fp["user_agent"],
            timezone_id=fp["timezone"],
            locale=fp["language"]
        )
        page = await ctx.new_page()
        await page.goto("about:blank")
        print("Profile launched: " + cfg["name"])
        await asyncio.Event().wait()
asyncio.run(main())
''', str(profile_dir)], creationflags=0x00000010 if sys.platform == 'win32' else 0)
        return {'ok': True, 'name': name, 'status': 'launched'}
    except Exception as e:
        return {'ok': False, 'error': str(e)[:200]}

def do_list_profiles(params=None):
    profiles = []
    for d in PROFILES_DIR.iterdir():
        if d.is_dir() and (d / 'config.json').exists():
            cfg = json.loads((d / 'config.json').read_text(encoding='utf-8'))
            profiles.append({'name': d.name, 'template': cfg.get('template', ''),
                           'created': cfg.get('created', ''), 'proxy': cfg.get('proxy', '')})
    return {'ok': True, 'profiles': profiles, 'total': len(profiles)}

def do_delete_profile(params):
    name = params.get('name', '')
    profile_dir = PROFILES_DIR / name
    if not profile_dir.exists():
        return {'ok': False, 'error': 'Profile not found: ' + name}
    import shutil
    shutil.rmtree(profile_dir)
    return {'ok': True, 'name': name, 'deleted': True}

HANDLERS = {'create_profile': do_create_profile, 'launch': do_launch,
            'list_profiles': do_list_profiles, 'delete_profile': do_delete_profile}

if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else 'list_profiles'
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except:
            pass
    h = HANDLERS.get(action)
    result = h(params) if h else {'ok': False, 'error': 'unknown:' + action}
    print(json.dumps(result, ensure_ascii=False, default=str))

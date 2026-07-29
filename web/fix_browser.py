import re
p = r'C:\Users\Administrator\Desktop\GBT_Pro_AI_v1\nano_browser\browser.py'
c = open(p, encoding='utf-8').read()
c = c.replace('async def quick_navigate(self, url):',
             'async def quick_navigate(self, url):\n        if url and not url.startswith("http") and not url.startswith("about:"): url = "http://localhost:8765/" + url')
open(p,'w',encoding='utf-8').write(c)
print('BROWSER FIXED')

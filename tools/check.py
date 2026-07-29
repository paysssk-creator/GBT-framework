import re
h = open('C:/Users/ADMIN/GBTxiaotudouV5/index.html', encoding='utf-8').read()
print(f'Size: {len(h)}B')
print(f'Hero count: {len(re.findall(r"<section class=[\"\\\\]*hero[\"\\\\]*", h))}')
print(f'Body close: {"OK" if "</body>" in h else "MISSING"}')
print(f'HTML end clean: {h.strip().endswith("</html>")}')
print(f'catScroll: {"OK" if "catScroll" in h else "MISSING"}')
print(f'cta-footer: {"OK" if "cta-footer" in h else "MISSING"}')
print(f'aiSession: {"OK" if "aiSession" in h else "MISSING"}')
print(f'ai-search: {"OK" if "ai-search" in h else "MISSING"}')
print(f'addQuickActions: {"OK" if "addQuickActions" in h else "MISSING"}')

# Show hero section HTML
hero_start = h.find('<section class="hero"')
hero_end = h.find('</section>', hero_start) + 10
print(f'\nHero HTML ({hero_start}-{hero_end}):')
print(h[hero_start:hero_end])

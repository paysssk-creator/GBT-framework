import os

h = open('C:/Users/ADMIN/GBTxiaotudouV5/web/index.html', encoding='utf-8').read()

# Replace old aiAsk
old = "async function aiAsk(){const q=document.getElementById('aiInput').value.trim();"
new = """let aiSession='sess_'+Date.now()+'_'+Math.random().toString(36).slice(2,8);
function addQuickActions(actions,msgs){if(!actions||!actions.length)return;const div=document.createElement('div');div.style.cssText='display:flex;flex-wrap:wrap;gap:4px;margin:4px 0;padding-left:4px';actions.forEach(function(a){const btn=document.createElement('button');btn.textContent=a;btn.style.cssText='padding:4px 10px;border-radius:12px;font-size:11px;border:1px solid var(--border);background:var(--bg3);color:var(--accent);cursor:pointer';btn.onclick=function(){document.getElementById('aiInput').value=a;aiAsk()};div.appendChild(btn)});msgs.appendChild(div)}
async function aiAsk(){const q=document.getElementById('aiInput').value.trim();"""

h = h.replace(old, new)

# Add session to fetch
old2 = "body:JSON.stringify({question:q})}"
new2 = "body:JSON.stringify({question:q,session:aiSession})}"
h = h.replace(old2, new2)

# Add quick actions display
old3 = "}catch(e){const last=msgs.querySelectorAll"
new3 = """if(d.quick_actions)addQuickActions(d.quick_actions,msgs);if(d.next_topics){const nDiv=document.createElement('div');nDiv.style.cssText='font-size:10px;color:var(--dim);margin:2px 0 8px 4px';nDiv.textContent='💡 '+d.next_topics.join(' · ');msgs.appendChild(nDiv)}}catch(e){const last=msgs.querySelectorAll"""
h = h.replace(old3, new3)

# Add page suggestion on load
suggest = """setTimeout(async function(){try{const r=await fetch(API+'/suggest',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({page:location.pathname})});const d=await r.json();if(d.ok&&d.suggestion){const msgs=document.getElementById('aiMsgs');msgs.innerHTML='<div style=\"text-align:left;margin:4px 0\"><span style=\"background:var(--bg2);padding:6px 12px;border-radius:12px;font-size:12px;color:var(--fg)\">'+d.suggestion+'</span></div>';if(d.actions)d.actions.forEach(function(a){const btn=document.createElement('button');btn.textContent=a;btn.style.cssText='margin:2px;padding:4px 10px;border-radius:12px;font-size:11px;border:1px solid var(--border);background:var(--bg3);color:var(--accent);cursor:pointer';btn.onclick=function(){document.getElementById('aiInput').value=a;aiAsk()};msgs.appendChild(btn)})}}catch(e){}},1500)"""
script_end = h.rfind('</script>')
h = h[:script_end] + suggest + '\n' + h[script_end:]

open('C:/Users/ADMIN/GBTxiaotudouV5/web/index.html', 'w', encoding='utf-8').write(h)
print(f'Fixed: {len(h)}B, session:{h.count("aiSession")}, actions:{h.count("addQuickActions")}, suggest:{h.count("suggest")}')

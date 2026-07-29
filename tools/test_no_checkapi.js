
const API='https://gbtxiaotudou.com/api';
const PROJ_API=API+'/projects';
const modal=document.createElement('div');modal.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.8);backdrop-filter:blur(8px);z-index:999;display:none;align-items:center;justify-content:center';
document.body.appendChild(modal);
document.getElementById('modalClose').onclick=()=>modal.style.display='none';
modal.onclick=e=>{if(e.target===modal)modal.style.display='none'};
document.getElementById('modalSubmit').onclick=async()=>{const url=document.getElementById('repoUrl').value.trim();const msg=document.getElementById('modalMsg');if(!url){msg.textContent='请输入GitHub仓库URL';msg.style.color='var(--red)';return}msg.textContent='⏳ AI评估中...';msg.style.color='var(--accent)';try{const r=await fetch(API+'/oauth/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({repo_url:url,repo_name:url.split('/').pop()})});const d=await r.json();if(d.ok){msg.innerHTML='✅ 提交成功!<br>AI评估价格: <b style=color:var(--green)>$'+d.suggested_price_per_hour+'/h</b>';msg.style.color='var(--green)';setTimeout(()=>modal.style.display='none',2000)}else{msg.textContent=d.error||'提交失败';msg.style.color='var(--red)'}}catch(e){msg.textContent='API未连接. 请启动服务器';msg.style.color='var(--red)'}};

// ═══ API Status ═══
const statusDot=document.createElement('span');statusDot.style.cssText='display:inline-block;width:6px;height:6px;border-radius:50%;margin-right:4px;background:var(--dim)';
const navBrand=document.querySelector('.nav-brand');if(navBrand)navBrand.appendChild(statusDot);

// ═══ Deploy + Payment Flow ═══
let pendingDeploy=null;
async function deployProject(n,p){
  const b=event.target; const orig=b.textContent;
  b.textContent='⏳';b.disabled=1;
  // ① Check API
  try{const r=await fetch(API+'/health');if(!r.ok)throw new Error()}catch(e){b.textContent='API离线';b.style.background='var(--red)';setTimeout(()=>{b.textContent=orig;b.style.background=''},2000);b.disabled=0;return}
  // ② Create payment
  try{const r=await fetch(API+'/payment/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({coin:'USDT',amount:parseFloat(p),order_id:'GBT-'+Date.now(),project:n})});const d=await r.json();
    if(d.ok){
      b.textContent='✅ 已部署';b.style.background='var(--green)';
      setTimeout(()=>{b.textContent=orig;b.style.background=''},3000)
    }else{b.textContent='重试';b.disabled=0}
  }catch(e){b.textContent='重试';b.disabled=0}}
document.querySelectorAll('.btn-deploy').forEach(b=>{const c=b.closest('.project-card');const n=c?.querySelector('.card-name')?.textContent?.split('·')[0]?.trim()||'';const p=c?.querySelector('.card-price')?.textContent?.replace(/[^0-9.]/g,'')||'0.5';b.onclick=()=>deployProject(n,p)});
  document.querySelectorAll('.btn-deploy').forEach(b=>{const c=b.closest('.project-card');const n=c?.querySelector('.card-name')?.textContent?.split('·')[0]?.trim()||'';const p=c?.querySelector('.card-price')?.textContent?.replace(/[^0-9.]/g,'')||'0.5';b.onclick=()=>deployProject(n,p)});
const obs=new IntersectionObserver((e)=>{e.forEach(x=>{if(x.isIntersecting){x.target.classList.add("visible");obs.unobserve(x.target)}})},{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>obs.observe(el));
const co=new IntersectionObserver((e)=>{e.forEach(x=>{if(x.isIntersecting){const el=x.target;const t=parseInt(el.textContent.replace(/[^0-9]/g,""));if(t>0){let c=0;const s=t/35;const iv=setInterval(()=>{c+=s;if(c>=t){el.textContent=el.textContent.replace(/[0-9]+/,t);clearInterval(iv)}else{el.textContent=el.textContent.replace(/[0-9]+/,Math.floor(c))}},22)}}co.unobserve(el)}})},{threshold:.5});
document.querySelectorAll('.stat-num').forEach(el=>co.observe(el));

setTimeout(function(){
  document.getElementById('notifBar').classList.add('show');
  setTimeout(function(){
    document.getElementById('notifBar').classList.remove('show')
  },5000)
},2000);
setInterval(function(){
  var msgs=['AI扫描完成: 13个热门项目已更新','新项目上线: AI Agent框架','支付系统正常: 60+币种可用','开发者已赚取: ,600+'];
  var m=msgs[Math.floor(Math.random()*msgs.length)];
  document.getElementById('notifMsg').textContent=m;
  document.getElementById('notifBar').classList.add('show');
  setTimeout(function(){document.getElementById('notifBar').classList.remove('show')},4000)
},30000);


(async function loadProjects(){
  try{
    const r = await fetch(API+'/projects');
    const d = await r.json();
    if(d.ok && d.projects){
      const grid = document.querySelector('.projects-grid');
      if(!grid) return;
      grid.innerHTML = d.projects.map(p => 
        '<div class="project-card reveal"><div class="card-header"><div class="card-logo" style="background:'+p.color+';color:#fff">'+p.icon.slice(0,2).toUpperCase()+'</div><div><div class="card-name">'+p.name+'</div><div class="card-stars">⭐ '+p.stars+'</div></div></div><div class="card-desc">AI评估·即租即用</div><div class="card-tags">'+p.tags.map(t=>'<span class="tag tag-o">'+t+'</span>').join('')+'</div><div class="card-footer"><div class="card-price">$'+p.price.toFixed(2)+'<span>/h</span></div><button class="btn-deploy" onclick="deployProject($'"'+p.id+'","'+p.price+'")">部署</button></div></div>'
      ).join('');
      // Rewire deploy buttons
      document.querySelectorAll('.btn-deploy').forEach(b=>{
        const c=b.closest('.project-card');
        const n=c?.querySelector('.card-name')?.textContent?.split('·')[0]?.trim()||'';
        const p=c?.querySelector('.card-price')?.textContent?.replace(/[^0-9.]/g,'')||'0.5';
        b.onclick=()=>deployProject(n,p)
      });
    }
  }catch(e){console.log('Projects API not available, using static')}
})();

function aiSearch(){const q=document.getElementById('aiSearch').value.trim();if(!q)return;window.location.hash='projects';const grid=document.querySelector('.projects-grid');if(grid){const cards=grid.querySelectorAll('.project-card');let found=0;cards.forEach(c=>{const t=c.textContent.toLowerCase();if(t.includes(q.toLowerCase())){c.style.display='';found++}else{c.style.display='none'}});if(!found){grid.innerHTML='<div style=text-align:center;padding:40px;color:var(--dim)><p>🔍 未找到 "'+q+'"</p><p style=font-size:13px>试试其他关键词,或提交你的项目</p></div>'}}}
let aiSession='sess_'+Date.now()+'_'+Math.random().toString(36).slice(2,8);
function addQuickActions(actions,msgs){if(!actions||!actions.length)return;const div=document.createElement('div');div.style.cssText='display:flex;flex-wrap:wrap;gap:4px;margin:4px 0;padding-left:4px';actions.forEach(function(a){const btn=document.createElement('button');btn.textContent=a;btn.style.cssText='padding:4px 10px;border-radius:12px;font-size:11px;border:1px solid var(--border);background:var(--bg3);color:var(--accent);cursor:pointer';btn.onclick=function(){document.getElementById('aiInput').value=a;aiAsk()};div.appendChild(btn)});msgs.appendChild(div)}
async function aiAsk(){const q=document.getElementById('aiInput').value.trim();if(!q)return;const msgs=document.getElementById('aiMsgs');msgs.innerHTML+='<div style=text-align:right;margin:4px 0><span style=background:var(--accent);color:#fff;padding:6px 12px;border-radius:12px;font-size:12px>'+q+'</span></div>';document.getElementById('aiInput').value='';msgs.innerHTML+='<div style=text-align:left;margin:4px 0><span style=background:var(--bg2);padding:6px 12px;border-radius:12px;font-size:12px;color:var(--dim)>⏳...</span></div>';msgs.scrollTop=msgs.scrollHeight;try{const r=await fetch(API+'/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,session:aiSession})});const d=await r.json();const last=msgs.querySelectorAll('span[style*=bg2]');if(last.length)last[last.length-1].textContent=d.answer||d.response||'收到!'if(d.quick_actions)addQuickActions(d.quick_actions,msgs);if(d.next_topics){const nDiv=document.createElement('div');nDiv.style.cssText='font-size:10px;color:var(--dim);margin:2px 0 8px 4px';nDiv.textContent='💡 '+d.next_topics.join(' · ');msgs.appendChild(nDiv)}}catch(e){const last=msgs.querySelectorAll('span[style*=bg2]');if(last.length)last[last.length-1].textContent='抱歉,AI服务暂不可用'}}

setTimeout(async function(){try{const r=await fetch(API+'/suggest',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({page:location.pathname})});const d=await r.json();if(d.ok&&d.suggestion){const msgs=document.getElementById('aiMsgs');msgs.innerHTML='<div style="text-align:left;margin:4px 0"><span style="background:var(--bg2);padding:6px 12px;border-radius:12px;font-size:12px;color:var(--fg)">'+d.suggestion+'</span></div>';if(d.actions)d.actions.forEach(function(a){const btn=document.createElement('button');btn.textContent=a;btn.style.cssText='margin:2px;padding:4px 10px;border-radius:12px;font-size:11px;border:1px solid var(--border);background:var(--bg3);color:var(--accent);cursor:pointer';btn.onclick=function(){document.getElementById('aiInput').value=a;aiAsk()};msgs.appendChild(btn)})}}catch(e){}},1500)

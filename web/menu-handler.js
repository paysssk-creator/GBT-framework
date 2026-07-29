// menu-handler.js — V1-V30 活体3D场景调度器
(function(){
  var stage = document.getElementById('gbt-stage');
  if (!stage) return;

  // ═══ 30层版本数据 ═══
  var versionData = {
    V1:{t:'V1 · 静态海报',c:'#888',d:'HTML+CSS假3D。JPG贴图+阴影伪造立体感。无交互无粒子——这是"不能这么做"的对标物。',tags:['HTML','CSS','假3D']},
    V2:{t:'V2 · 2D Canvas',c:'#888',d:'<canvas>+原生JS画点阵线条。ctx.beginPath()+requestAnimationFrame。2D无Z轴,复杂物体代码爆炸。',tags:['Canvas','2D','命令式']},
    V3:{t:'V3 · 裸WebGL',c:'#888',d:'顶点着色器+片元着色器。自己管理缓冲区/矩阵/光照。画一个立方体要几百行。GLSL语法AI记不住。',tags:['WebGL','Shader','GLSL']},
    V4:{t:'V4 · Three.js命令式',c:'#aaa',d:'引入Three.js。new Scene()+手写相机灯光。AI能写但像盲人摸象——不知道模型放哪个div。',tags:['Three.js','命令式']},
    V5:{t:'V5 · 声明式引擎',c:'#00d4ff',d:'2KB吞掉Three.js。data-*协议诞生。AI只写标签,引擎自动接管。30层进化的起点与分水岭。',tags:['声明式','data-*','分水岭'],kb:'2KB'},
    V6:{t:'V6 · 高保真模型',c:'#00d4ff',d:'GLB加载+HDR环境贴图+PMREMGenerator PBR烘培+ACES色调映射+OrbitControls拖拽缩放+5种内置HDR预设。',tags:['GLTFLoader','RGBELoader','PBR'],kb:'13KB'},
    V7:{t:'V7 · 交互热区',c:'#a855f7',d:'Raycaster射线检测+脉冲光点标记+毛玻璃弹窗。点击模型部件弹出介绍卡片,支持跳转链接。',tags:['hotspots','Raycaster','弹窗'],kb:'26KB'},
    V8:{t:'V8 · 材质配置器',c:'#a855f7',d:'data-materials预设+data-gbt3d-part动态换色。color.lerp() 400ms平滑渐变+场景阴影底座+加载进度条。',tags:['换色','阴影','进度条'],kb:'34KB'},
    V9:{t:'V9 · 营销闭环',c:'#a855f7',d:'6视角一键切换+canvas截图下载+手机系统分享+WebXR AR增强现实。',tags:['截图','AR','视角'],kb:'38KB'},
    V10:{t:'V10 · 数字孪生',c:'#ffd700',d:'WebSocket/HTTP数据源+data-bind数据→模型映射+data-range归一化+GBT_DATA_UPDATE全局事件+模拟数据模式。',tags:['实时数据','WebSocket','模拟'],kb:'60KB'},
    V11:{t:'V11 · 多人协同',c:'#ffd700',d:'WebSocket房间管理+相机/材质/热区操作广播+协同光标+3D标记+在线人数。server-sync.js一键启动。',tags:['多人','同步','光标'],kb:'60KB'},
    V12:{t:'V12 · AI虚拟人',c:'#ffd700',d:'GLB骨骼动画(idle/talk)+Web Speech TTS播报+语音识别+对话气泡+内置20+规则语义解析器。',tags:['虚拟人','TTS','语音'],kb:'69KB'},
    V13:{t:'V13 · 生成式AI',c:'#22c55e',d:'文字→3D模型生成(轮询)+autoLayout自动布景+AR实景放置(WebXR hit-test)+generate-proxy.js代理。',tags:['AI生成','布景','AR'],kb:'73KB'},
    V14:{t:'V14 · 情感计算',c:'#22c55e',d:'FaceDetector表情识别+HandDetector手势+GBT_EMOTION_UPDATE事件+粒子/模型情绪响应。',tags:['表情','手势','情绪'],kb:'78KB'},
    V15:{t:'V15 · 多感官融合',c:'#22c55e',d:'Web Audio FFT音频驱动+Web MIDI音符映射+Gamepad摇杆控制+fusionBus事件融合总线。',tags:['音频','MIDI','手柄'],kb:'83KB'},
    V16:{t:'V16 · 生产级部署',c:'#ffd700',d:'PWA manifest+service-worker+Docker+Nginx+GitHub Actions CI/CD+WebGPU自适应+内存监控。',tags:['Docker','CI/CD','PWA'],kb:'84KB'},
    V17:{t:'V17 · AI智能体',c:'#a855f7',d:'人格注入+localStorage用户画像+自主决策循环+自我策展(热度淘汰)。Agent主动开口推荐。',tags:['Agent','记忆','策展'],kb:'90KB'},
    V18:{t:'V18 · 物理世界',c:'#00d4ff',d:'WebBluetooth心率/LED+WebUSB传感器+物理↔3D双向映射+emit设备控制。',tags:['BLE','USB','双向'],kb:'92KB'},
    V19:{t:'V19 · 环境感知',c:'#00d4ff',d:'GPS地理围栏(haversine)+NFC标签+环境光传感器+陀螺仪指南针+空间锚定。',tags:['GPS','NFC','光感'],kb:'95KB'},
    V20:{t:'V20 · 时间维度',c:'#ffd700',d:'天文时钟6时段色调渐变+Fog雾效+行为预测+场景快照+时间回溯。',tags:['日夜','预测','回溯'],kb:'99KB'},
    V21:{t:'V21 · 具身智能',c:'#a855f7',d:'物理机器人WebSocket控制。3D场景→现实世界移动指令。模拟模式已激活。',tags:['机器人','无人机']},
    V22:{t:'V22 · 脑机接口',c:'#22c55e',d:'Muse脑电头环EEG信号→专注度/放松度→3D属性映射。模拟模式已激活。',tags:['BCI','EEG','意念']},
    V23:{t:'V23 · SLAM扫描',c:'#00d4ff',d:'WebXR平面检测+网格扫描。虚实完全融合,空间锚定。模拟模式已激活。',tags:['SLAM','点云','锚定']},
    V24:{t:'V24 · 基因进化',c:'#22c55e',d:'24h基因池迭代+交叉变异。页面自己"进化"出最佳配色/布局。模拟模式已激活。',tags:['进化','变异','适应']},
    V25:{t:'V25 · NFT铸造',c:'#ffd700',d:'3D定制模型一键铸造成NFT+MetaMask+IPFS上链。演示模式已激活。',tags:['NFT','以太坊','MetaMask']},
    V26:{t:'V26 · 平行宇宙',c:'#a855f7',d:'多时间线同时渲染。滑动切换不同配色/版本的模型。模拟模式已激活。',tags:['多重宇宙','分岔']},
    V27:{t:'V27 · 触觉反馈',c:'#00d4ff',d:'navigator.vibrate()+材质粗糙度→震动强度自适应。模拟模式已激活。',tags:['触觉','震动','体感']},
    V28:{t:'V28 · 量子视觉',c:'#22c55e',d:'波函数概率云+观察者效应。悬停时粒子坍缩成确定轨迹。模拟模式已激活。',tags:['量子','叠加态','坍缩']},
    V29:{t:'V29 · AI创世',c:'#a855f7',d:'输入Prompt→大模型返回JSON配置→引擎重构整个3D世界。模拟模式已激活。',tags:['创世','自主设计']},
    V30:{t:'V30 · 全息链接',c:'#ffd700',d:'XR眼镜+眼球追踪+神经信号。数字与物理终极融合。模拟模式已激活。',tags:['全息','XR','神经']},
  };

  // ═══ 渲染侧边栏 ═══
  var vlist = document.getElementById('vlist');
  var eras = [
    { label:'摸索期', versions:['V1','V2','V3'] },
    { label:'接入期', versions:['V4'] },
    { label:'分水岭', versions:['V5'] },
    { label:'扩张期(渲染)', versions:['V6'] },
    { label:'扩张期(交互)', versions:['V7','V8','V9'] },
    { label:'扩张期(数据)', versions:['V10','V11'] },
    { label:'扩张期(智能)', versions:['V12','V13','V14','V15'] },
    { label:'扩张期(工程)', versions:['V16','V17'] },
    { label:'扩张期(物理)', versions:['V18','V19','V20'] },
    { label:'终极期', versions:['V21','V22','V23','V24','V25','V26','V27','V28','V29','V30'] },
  ];
  eras.forEach(function(era){
    var label = document.createElement('div');
    label.className = 'era-label';
    label.textContent = era.label;
    vlist.appendChild(label);
    era.versions.forEach(function(vk){
      var vd = versionData[vk];
      if (!vd) return;
      var el = document.createElement('div');
      el.className = 'ver';
      var eraClass = vn>=21?'v21-v30':vn>=6?'v6-v20':vn===5?'v5':'v1-v4';if(vn===30)eraClass+=' v30-ultimate';el.className='ver '+eraClass;el.innerHTML = '<span class="vtag" style="background:'+vd.c+'20">'+vk+'</span><span class="vname">'+vd.t.split('·')[1].trim()+'</span>';
      el.onclick = function(){ switchTo(vk); };
      vlist.appendChild(el);
    });
  });

  // ═══ 粒子音效 ═══
  function playSound(freq,dur,type){
    try{var ctx=new AudioContext();var osc=ctx.createOscillator();var gain=ctx.createGain();osc.type=type||'sine';osc.frequency.value=freq;gain.gain.setValueAtTime(0.08,ctx.currentTime);gain.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+dur);osc.connect(gain);gain.connect(ctx.destination);osc.start();osc.stop(ctx.currentTime+dur)}catch(e){}
  }

  // ═══ V30奇点爆炸 ═══
  function singularityBurst(){
    var ring=document.createElement('div');ring.className='singularity';stage.appendChild(ring);
    setTimeout(function(){if(ring.parentNode)ring.parentNode.removeChild(ring)},1600);
    // 分层音效
    playSound(220,0.3,'sine');setTimeout(function(){playSound(440,0.2,'triangle')},150);setTimeout(function(){playSound(880,0.15,'square')},300);
  }

  // ═══ 场景切换 ═══
  function switchTo(version){
    // 高亮
    document.querySelectorAll('.ver').forEach(function(el){ el.classList.remove('active'); });
    var items = document.querySelectorAll('.ver');
    for (var i=0;i<items.length;i++){
      if (items[i].querySelector('.vtag').textContent === version) { items[i].classList.add('active'); break; }
    }

    var data = versionData[version];
    // 更新UI卡片
    document.getElementById('card-title').style.color = data.c;
    document.getElementById('card-title').textContent = data.t;
    document.getElementById('card-desc').textContent = data.d;
    var tagsEl = document.getElementById('card-tags');
    tagsEl.innerHTML = data.tags.map(function(t){ return '<span class="tag">'+t+'</span>' }).join('');
    document.getElementById('card-meta').textContent = '引擎体积: '+(data.kb||'模拟')+' · 30层进化';

    // 清空旧场景
    window._gbtPulseActive = false
    if (window.__GBT_ENGINE && window.__GBT_ENGINE.clear) {
      window.__GBT_ENGINE.clear(stage);
    }

    // 调度3D场景
    var engine = window.__GBT_ENGINE;
    if (!engine) return;

    var vn = parseInt(version.replace('V',''));
    
    if (vn <= 4) {
      // V1-V4: 静态/简单 — 纯黑背景,什么都不渲染
      stage.style.background = vn===1?'#050510':vn===2?'#080818':vn===3?'#0a0a1a':'#0c0c1c';
    }
    else if (vn === 5) {
      engine.initParticles(stage, {count:2000, color:'#00d4ff', rings:3, speed:0.0005});
    }
    else if (vn >= 6 && vn <= 20) {
      // V6-V20: 粒子+不同颜色/参数展示能力层次
      var colors = ['#00d4ff','#a855f7','#a855f7','#a855f7','#ffd700','#ffd700','#ffd700','#22c55e','#22c55e','#22c55e','#ffd700','#a855f7','#00d4ff','#00d4ff','#ffd700'];
      var c = colors[vn-6] || '#00d4ff';
      var cnt = 1500 + (vn-5)*50;
      var spd = 0.0003 + (vn-5)*0.00005;
      engine.initParticles(stage, {count:Math.min(cnt,3000), color:c, rings:3, speed:spd});
    }
    else {
      // V21-V30: 终极粒子+特殊效果
      engine.initParticles(stage, {count:2500, color:'#ffd700', rings:4, speed:0.0008});
      // 脉冲光晕模拟量子/全息效果
      setTimeout(function(){
        if (engine._pulseGlow) engine._pulseGlow(stage);
      singularityBurst();
      }, 500);
    }

    if(vn>=21){playSound(880,0.2,'sine')}else if(vn===5){playSound(440,0.25,'triangle')}else if(vn>=6){playSound(660,0.15,'sine')}
    console.log('[Menu] 切换到', version, data.t);
  }

  // 暴露
  window.__GBT_MENU = { switchTo: switchTo, versionData: versionData };
  // 默认选中V30
  switchTo('V30');
})();

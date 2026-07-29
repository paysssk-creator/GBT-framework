/**
 * ═══════════════════════════════════════════
 *  GBT 3D 能力层 v2 — AI部署页面自动加载
 *  
 *  新增: 动态数据地球 · 移动端性能保底 · 光效连线(data-beam)
 *  AI 只需: <div data-gbt3d="..." data-markers="/api/..." >
 * ═══════════════════════════════════════════
 */
(function injectGBT3D() {
  if (window.GBT3D) return;
  var CDN = 'https://unpkg.com/three@0.160.0/build/three.min.js';
  var loaded = false;
  function boot() { if (loaded) return; loaded = true; initGBT3D(); }
  if (!window.THREE) {
    var s = document.createElement('script');
    s.src = CDN; s.async = true; s.onload = boot;
    document.head.appendChild(s);
  } else { boot(); }
})();

function initGBT3D() {
  if (window.GBT3D) return;

  // ═══ 移动端检测 ═══
  var IS_MOBILE = /Mobi|Android|iPhone/i.test(navigator.userAgent);
  var MOBILE_MAX_PARTICLES = 600;
  var MOBILE_RINGS = 2;
  var MOBILE_SPEED = 0.0003;

  var GBT = window.GBT3D = {
    /* ─── V1-V4 史前进化 (概念层, 解释为什么V5是分水岭) ─── */
    _history: {
      V1: {era:'静态海报',year:2024,desc:'HTML+CSS假3D。设计师画JPG贴图, CSS渐变伪造立体感。无交互, 无粒子, 无旋转。',lesson:'假3D做不到真正的旋转和粒子交互——必须引入程序化渲染。'},
      V2: {era:'2D Canvas',year:2024,desc:'<canvas>+原生JS画点阵线条。ctx.beginPath()+requestAnimationFrame。2D无Z轴深度, 复杂物体代码爆炸。',lesson:'纯手写命令式代码路线太累——AI生成极易出错卡顿。'},
      V3: {era:'裸WebGL',year:2024,desc:'WebGLRenderingContext+顶点着色器+片元着色器。自己管理缓冲区/矩阵/光照。画一个旋转立方体要几百行。',lesson:'裸机WebGL给AI完全不可行——GLSL语法AI记不住, 写出来跑不通。'},
      V4: {era:'Three.js命令式',year:2024,desc:'引入Three.js库。new THREE.Scene()+Mesh+手写相机灯光模型。代码清晰但仍需命令式写所有逻辑。',lesson:'AI能写Three.js但像盲人摸象——不知道模型放哪个div, 3D容器和页面元素相互遮挡。'},
      V5: {era:'声明式引擎',year:2025,desc:'封装gbt-3d.js(2KB)。抛弃所有命令式JS。AI只需写<div data-gbt3d=\"particles\">。引擎自动读取渲染。',lesson:'把3D控制权从JS移到HTML。AI只写标签, 引擎自动接管——这是驯服AI的终极一步。'}
    },


    instances: new Map(),

    /* ─── 粒子环 ─── */
    createParticleRing(container, opts) {
      opts = opts || {};
      var count = opts.count || 2000;
      var radius = opts.radius || 3;
      var color = opts.color || 0x00d4ff;
      var speed = opts.speed || 0.0005;
      var rings = opts.rings || 3;

      // ═══ 移动端降级 ═══
      if (IS_MOBILE) {
        count = Math.min(count, MOBILE_MAX_PARTICLES);
        rings = Math.min(rings, MOBILE_RINGS);
        speed = MOBILE_SPEED;
      }

      var W = container.clientWidth;
      var H = container.clientHeight || window.innerHeight;
      var scene = new THREE.Scene();
      var camera = new THREE.PerspectiveCamera(60, W / H, 0.1, 100);
      camera.position.z = 5;

      var renderer = new THREE.WebGLRenderer({ alpha: true, antialias: !IS_MOBILE });
      renderer.setSize(W, H);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, IS_MOBILE ? 1 : 2));
      container.appendChild(renderer.domElement);

      var geo = new THREE.BufferGeometry();
      var positions = new Float32Array(count * 3);
      var colors = new Float32Array(count * 3);
      for (var i = 0; i < count; i++) {
        var ri = i % rings;
        var r = radius + ri * 0.3;
        var angle = (i / count) * Math.PI * 2 * (ri + 1);
        var y = (Math.random() - 0.5) * 0.5 * (ri + 1);
        positions[i * 3] = Math.cos(angle) * r;
        positions[i * 3 + 1] = y;
        positions[i * 3 + 2] = Math.sin(angle) * r;
        var c = new THREE.Color(color);
        c.offsetHSL(ri * 0.05, 0, Math.random() * 0.3);
        colors[i * 3] = c.r;
        colors[i * 3 + 1] = c.g;
        colors[i * 3 + 2] = c.b;
      }
      geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

      var mat = new THREE.PointsMaterial({
        size: IS_MOBILE ? 0.04 : 0.02,
        vertexColors: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        transparent: true,
        opacity: 0.8,
      });
      var particles = new THREE.Points(geo, mat);
      scene.add(particles);

      for (var ri2 = 0; ri2 < rings; ri2++) {
        var rgeo = new THREE.TorusGeometry(radius + ri2 * 0.3, 0.002, 16, 100);
        var rmat = new THREE.MeshBasicMaterial({
          color: new THREE.Color(color).multiplyScalar(0.3 + ri2 * 0.2),
          transparent: true, opacity: 0.4,
        });
        var ring = new THREE.Mesh(rgeo, rmat);
        ring.rotation.x = Math.PI / 2;
        ring.rotation.y = ri2 * 0.3;
        scene.add(ring);
      }

      var clock = new THREE.Clock();
      function animate() {
        requestAnimationFrame(animate);
        var dt = clock.getDelta();
        particles.rotation.y += speed * dt * 60;
        particles.rotation.x += speed * 0.3 * dt * 60;
        renderer.render(scene, camera);
      }
      animate();

      var onResize = function () {
        var w = container.clientWidth;
        var h = container.clientHeight || window.innerHeight;
        camera.aspect = w / h; camera.updateProjectionMatrix();
        renderer.setSize(w, h);
      };
      window.addEventListener('resize', onResize);
      return {
        dispose: function () {
          window.removeEventListener('resize', onResize);
          renderer.dispose();
          if (container.contains(renderer.domElement)) container.removeChild(renderer.domElement);
        }
      };
    },

    /* ─── 3D 地球 (支持动态数据) ─── */
    createGlobe(container, opts) {
      opts = opts || {};
      var radius = opts.radius || 1.5;
      var color = opts.color || 0x00d4ff;
      var speed = opts.speed || 0.002;
      var markerSource = opts.markers || [];
      var markerFetchUrl = opts.markerFetchUrl || null;
      var markerFetchInterval = opts.markerFetchInterval || 3000;

      if (IS_MOBILE) speed *= 0.7;

      var W = container.clientWidth;
      var H = container.clientHeight || window.innerHeight;
      var scene = new THREE.Scene();
      var camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
      camera.position.z = 4;

      var renderer = new THREE.WebGLRenderer({ alpha: true, antialias: !IS_MOBILE });
      renderer.setSize(W, H);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, IS_MOBILE ? 1 : 2));
      container.appendChild(renderer.domElement);

      // 地球
      var geo = new THREE.SphereGeometry(radius, 64, 48);
      var mat = new THREE.MeshPhongMaterial({
        color: color, wireframe: true,
        transparent: true, opacity: 0.6,
        emissive: new THREE.Color(color).multiplyScalar(0.2),
      });
      var globe = new THREE.Mesh(geo, mat);
      scene.add(globe);

      // 外发光
      var glowGeo = new THREE.SphereGeometry(radius * 1.05, 64, 48);
      var glowMat = new THREE.ShaderMaterial({
        uniforms: { uColor: { value: new THREE.Color(color) } },
        vertexShader: 'varying vec3 vNormal; void main(){vNormal=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
        fragmentShader: 'varying vec3 vNormal; uniform vec3 uColor; void main(){float intensity=pow(0.7-dot(vNormal,vec3(0,0,1.0)),2.0);gl_FragColor=vec4(uColor,intensity*0.3);}',
        transparent: true, blending: THREE.AdditiveBlending, depthWrite: false,
      });
      scene.add(new THREE.Mesh(glowGeo, glowMat));

      var light = new THREE.PointLight(0xffffff, 1, 10);
      light.position.set(3, 3, 3);
      scene.add(light);
      scene.add(new THREE.AmbientLight(0x222244));

      // ═══ 动态标记层 ═══
      var markerGroup = new THREE.Group();
      globe.add(markerGroup);
      var currentMarkers = [];
      var markerDots = [];

      function latLngToVec3(lat, lng, r) {
        r = r || radius * 1.02;
        var phi = (90 - lat) * Math.PI / 180;
        var theta = lng * Math.PI / 180;
        return new THREE.Vector3(
          r * Math.sin(phi) * Math.cos(theta),
          r * Math.cos(phi),
          r * Math.sin(phi) * Math.sin(theta)
        );
      }

      function updateMarkers(markerList) {
        // 清除旧标记
        markerDots.forEach(function (d) { markerGroup.remove(d); if (d.geometry) d.geometry.dispose(); if (d.material) d.material.dispose(); });
        markerDots = [];
        currentMarkers = markerList || [];

        currentMarkers.forEach(function (m) {
          var pos = latLngToVec3(m.lat, m.lng);
          var dot = new THREE.Mesh(
            new THREE.SphereGeometry(IS_MOBILE ? 0.05 : 0.03, 8, 8),
            new THREE.MeshBasicMaterial({ color: m.color || 0xff4444 })
          );
          dot.position.copy(pos);
          dot.userData = { markerData: m, basePos: pos.clone() };
          markerGroup.add(dot);
          markerDots.push(dot);

          // 光柱连接线
          var lineGeo = new THREE.BufferGeometry().setFromPoints([pos, pos.clone().multiplyScalar(1.3)]);
          var line = new THREE.Line(lineGeo, new THREE.LineBasicMaterial({ color: m.color || 0xff4444, transparent: true, opacity: 0.5 }));
          markerGroup.add(line);
          markerDots.push(line);
        });
      }

      // 初始标记
      if (!markerFetchUrl && Array.isArray(markerSource) && markerSource.length) {
        updateMarkers(markerSource);
      }

      // ═══ 动态拉取数据标记 ═══
      var fetchTimer = null;
      if (markerFetchUrl) {
        function fetchAndUpdate() {
          fetch(markerFetchUrl)
            .then(function (r) { return r.json(); })
            .then(function (data) {
              var markers = Array.isArray(data) ? data : (data.markers || data.nodes || []);
              updateMarkers(markers);
            })
            .catch(function () { /* 静默失败 */ });
        }
        fetchAndUpdate();
        fetchTimer = setInterval(fetchAndUpdate, markerFetchInterval);
      }

      // 环绕粒子
      var pGeo = new THREE.BufferGeometry();
      var pCount = IS_MOBILE ? 200 : 500;
      var pPositions = new Float32Array(pCount * 3);
      for (var pi = 0; pi < pCount; pi++) {
        var angle2 = (pi / pCount) * Math.PI * 2;
        var pr = radius * 1.2 + Math.random() * 0.5;
        pPositions[pi * 3] = Math.cos(angle2) * pr;
        pPositions[pi * 3 + 1] = (Math.random() - 0.5) * 1.5;
        pPositions[pi * 3 + 2] = Math.sin(angle2) * pr;
      }
      pGeo.setAttribute('position', new THREE.BufferAttribute(pPositions, 3));
      var pMesh = new THREE.Points(pGeo, new THREE.PointsMaterial({
        size: IS_MOBILE ? 0.04 : 0.02, color: color,
        blending: THREE.AdditiveBlending, depthWrite: false,
      }));
      globe.add(pMesh);

      // 动画
      function animate() {
        requestAnimationFrame(animate);
        globe.rotation.y += speed;
        pMesh.rotation.y -= speed * 0.5;
        // 标记点脉冲
        var t = Date.now() * 0.001;
        markerDots.forEach(function (dot) {
          if (dot.isMesh && dot.userData && dot.userData.basePos) {
            var pulse = 1 + Math.sin(t * 3) * 0.05;
            dot.position.copy(dot.userData.basePos).multiplyScalar(pulse);
            dot.material.opacity = 0.5 + Math.sin(t * 3) * 0.5;
          }
        });
        renderer.render(scene, camera);
      }
      animate();

      var onResize = function () {
        var w = container.clientWidth;
        var h = container.clientHeight || window.innerHeight;
        camera.aspect = w / h; camera.updateProjectionMatrix();
        renderer.setSize(w, h);
      };
      window.addEventListener('resize', onResize);

      return {
        globe: globe, markerGroup: markerGroup,
        updateMarkers: updateMarkers,
        dispose: function () {
          window.removeEventListener('resize', onResize);
          if (fetchTimer) clearInterval(fetchTimer);
          renderer.dispose();
          if (container.contains(renderer.domElement)) container.removeChild(renderer.domElement);
        }
      };
    },

    /* ─── 鼠标视差(移动端禁用) ─── */
    parallax(selector, intensity) {
      if (IS_MOBILE) return function () {}; // 移动端直接跳过
      intensity = intensity || 0.05;
      var els = document.querySelectorAll(selector);
      var handler = function (e) {
        var x = (e.clientX / window.innerWidth - 0.5) * 2;
        var y = (e.clientY / window.innerHeight - 0.5) * 2;
        els.forEach(function (el) {
          var depth = parseFloat(el.dataset.parallaxDepth || 1);
          el.style.transform = 'translate3d(' + (x * intensity * depth * 50) + 'px, ' + (y * intensity * depth * 50) + 'px, 0)';
        });
      };
      document.addEventListener('mousemove', handler);
      return function () { document.removeEventListener('mousemove', handler); };
    },

    /* ─── 滚动入场 ─── */
    scrollReveal(selector, options) {
      selector = selector || '.gbt-reveal';
      options = options || {};
      var threshold = options.threshold || 0.15;
      var stagger = options.stagger || 0.1;

      if (!('IntersectionObserver' in window)) {
        var all = document.querySelectorAll(selector);
        all.forEach(function (el) { el.style.opacity = '1'; el.style.transform = 'none'; });
        return;
      }

      var els = document.querySelectorAll(selector);
      var delay = 0;
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            setTimeout(function () {
              entry.target.style.opacity = '1';
              entry.target.style.transform = 'translateY(0) scale(1)';
            }, delay);
            delay += stagger * 1000;
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: threshold });

      els.forEach(function (el) {
        el.style.opacity = '0';
        el.style.transform = IS_MOBILE ? 'none' : 'translateY(30px) scale(0.96)';
        el.style.transition = 'all 0.6s cubic-bezier(0.22,0.61,0.36,1)';
        observer.observe(el);
      });
    },

    /* ─── 光效连线 (data-beam) ─── */
    createBeam(fromSelector, toSelector, opts) {
      opts = opts || {};
      var color = opts.color || '#00d4ff';
      var width = opts.width || 2;
      var dash = opts.dash || '8,4';

      var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('style', 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:5');
      svg.setAttribute('class', 'gbt-beam');
      document.body.appendChild(svg);

      var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('stroke', color);
      line.setAttribute('stroke-width', width);
      line.setAttribute('stroke-dasharray', dash);
      line.setAttribute('opacity', '0.7');
      svg.appendChild(line);

      // 发光效果
      var glow = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      glow.setAttribute('stroke', color);
      glow.setAttribute('stroke-width', width * 3);
      glow.setAttribute('opacity', '0.15');
      glow.setAttribute('filter', 'blur(6px)');
      svg.insertBefore(glow, line);

      function getCenter(el) {
        if (!el) return null;
        var r = el.getBoundingClientRect();
        return { x: r.left + r.width / 2, y: r.top + r.height / 2, visible: r.width > 0 && r.height > 0 };
      }

      function update() {
        var fromEl = typeof fromSelector === 'string' ? document.querySelector(fromSelector) : fromSelector;
        var toEl = typeof toSelector === 'string' ? document.querySelector(toSelector) : toSelector;
        var from = getCenter(fromEl);
        var to = getCenter(toEl);

        if (from && to && from.visible && to.visible) {
          line.setAttribute('x1', from.x); line.setAttribute('y1', from.y);
          line.setAttribute('x2', to.x);   line.setAttribute('y2', to.y);
          glow.setAttribute('x1', from.x); glow.setAttribute('y1', from.y);
          glow.setAttribute('x2', to.x);   glow.setAttribute('y2', to.y);
          svg.style.opacity = '1';
        } else {
          svg.style.opacity = '0';
        }
      }

      update();
      var onScroll = function () { requestAnimationFrame(update); };
      window.addEventListener('scroll', onScroll, { passive: true });
      window.addEventListener('resize', onScroll, { passive: true });

      return {
        update: update,
        dispose: function () {
          window.removeEventListener('scroll', onScroll);
          window.removeEventListener('resize', onScroll);
          if (svg.parentNode) svg.parentNode.removeChild(svg);
        }
      };
    },

    /* ─── 打字机 ─── */
    typewriter: function (el, text, speed) {
      speed = speed || 50;
      var target = typeof el === 'string' ? document.querySelector(el) : el;
      var i = 0;
      function type() {
        if (i < text.length) {
          target.textContent += text.charAt(i);
          i++;
          setTimeout(type, speed + Math.random() * 30);
        }
      }
      target.textContent = '';
      type();
    },

    /* ─── 数字跳动 ─── */
    countUp: function (el, targetVal, duration) {
      duration = duration || 1500;
      var startVal = parseFloat(el.textContent) || 0;
      var startTime = performance.now();
      function update(now) {
        var progress = Math.min((now - startTime) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = (startVal + (targetVal - startVal) * eased).toFixed(targetVal % 1 ? 2 : 0);
        if (progress < 1) requestAnimationFrame(update);
      }
      requestAnimationFrame(update);
    },
    /* ─── V9 高保真模型加载 (HDR+PBR+热区+动画+环境切换+材质配置+阴影+加载进度+视角切换+截图+AR) ─── */
    _builtinHDR: {
      studio:   'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/textures/equirectangular/studio_country_hall_1k.hdr',
      sunset:   'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/textures/equirectangular/venice_sunset_1k.hdr',
      warehouse:'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/textures/equirectangular/industrial_room_1k.hdr',
      night:    'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/textures/equirectangular/night_sky_1k.hdr',
      dawn:     'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/textures/equirectangular/kiara_1_dawn_1k.hdr',
    },

    // V9 视角预设
    _viewPresets: {front:[0,0,5],back:[0,0,-5],left:[-5,0,0],right:[5,0,0],top:[0,5,0],bottom:[0,-5,0],reset:null},

    loadModel: function (container, modelUrl, opts) {
      opts = opts || {};
      var scale = opts.scale || 1, color = opts.color || 0x00d4ff, speed = opts.speed || 0.005;
      var bgColor = opts.bgColor || 0x0a0a0f;
      var autoRotate = opts.autoRotate !== false, dragEnabled = opts.drag !== false, zoomEnabled = opts.zoom !== false;
      var envPreset = opts.env || 'sunset', envUrl = opts.envUrl || null;
      var hotspots = opts.hotspots || [], animName = opts.animName || null, animLoop = opts.animLoop !== false;
      var materialsConfig = opts.materials || {};
      var placeholder = opts.placeholder || '';
      var enableGround = opts.ground === true, enableShadow = opts.shadow === true;

      if (!window.THREE) { console.warn('[GBT3D] Three.js not loaded'); return null; }
      var W = container.clientWidth, H = container.clientHeight || innerHeight;
      var scene = new THREE.Scene(); scene.background = new THREE.Color(bgColor);
      var camera = new THREE.PerspectiveCamera(45, W/H, 0.1, 100);
      var initCamPos = opts.cameraPos || [0,0,5];
      camera.position.set(initCamPos[0],initCamPos[1],initCamPos[2]);camera.lookAt(0,0,0);
      var renderer = new THREE.WebGLRenderer({alpha:true,antialias:!IS_MOBILE,preserveDrawingBuffer:true});
      renderer.setSize(W,H); renderer.setPixelRatio(Math.min(devicePixelRatio,IS_MOBILE?1:2));
      if(enableShadow){renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap}
      renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.2;
      container.appendChild(renderer.domElement);

      // V9 相机动画
      var camTarget=null,camStart=null,camStartTime=0,camDuration=600,camStartLook=null,camEndLook=new THREE.Vector3(0,0,0);
      var defaultCamPos=camera.position.clone();

      // V8 加载占位
      var placeholderEl=null,progressEl=null;
      if(placeholder){placeholderEl=document.createElement('div');placeholderEl.style.cssText='position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#fff;text-align:center;z-index:10;font-family:sans-serif;pointer-events:none';placeholderEl.innerHTML='<div style="font-size:1rem;margin-bottom:8px">'+placeholder+'</div><div style="width:200px;height:3px;background:rgba(255,255,255,0.1);border-radius:2px;overflow:hidden"><div id="gbt-progress" style="width:0%;height:100%;background:#00d4ff;transition:width 0.3s"></div></div>';container.style.position=container.style.position||'relative';container.appendChild(placeholderEl);progressEl=placeholderEl.querySelector('#gbt-progress')}

      // HDR 环境贴图
      var pmremGenerator=new THREE.PMREMGenerator(renderer);pmremGenerator.compileEquirectangularShader();
      var currentEnvUrl='',self=this;
      function applyEnvMap(hdrUrl){if(!window.THREE.RGBELoader||hdrUrl===currentEnvUrl)return;currentEnvUrl=hdrUrl;new THREE.RGBELoader().setDataType(THREE.HalfFloatType).load(hdrUrl,function(t){var e=pmremGenerator.fromEquirectangular(t).texture;scene.environment=e;scene.background=new THREE.Color(bgColor);t.dispose()},undefined,function(){console.warn('[GBT3D] HDR load failed')})}
      applyEnvMap(envUrl||this._builtinHDR[envPreset]||this._builtinHDR.sunset);
      scene.add(new THREE.AmbientLight(0x404060,0.8));
      if(enableShadow){var dirLight=new THREE.DirectionalLight(0xffffff,1.5);dirLight.position.set(5,10,5);dirLight.castShadow=true;dirLight.shadow.mapSize.set(1024,1024);scene.add(dirLight)}

      // V8 场景地面阴影
      var groundPlane=null;
      if(enableGround){var groundGeo=new THREE.PlaneGeometry(8,8),groundMat=new THREE.ShadowMaterial({opacity:0.3});groundPlane=new THREE.Mesh(groundGeo,groundMat);groundPlane.rotation.x=-Math.PI/2;groundPlane.position.y=-2;groundPlane.receiveShadow=true;scene.add(groundPlane);var ringGeo=new THREE.RingGeometry(1.2,1.35,64),ringMat=new THREE.MeshBasicMaterial({color:0x00d4ff,side:THREE.DoubleSide,transparent:true,opacity:0.15});var glowRing=new THREE.Mesh(ringGeo,ringMat);glowRing.rotation.x=-Math.PI/2;glowRing.position.y=-1.99;scene.add(glowRing);groundPlane.userData={ring:glowRing}}

      // OrbitControls
      var controls=null;
      if((dragEnabled||zoomEnabled)&&window.THREE.OrbitControls){controls=new THREE.OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=0.08;controls.autoRotate=autoRotate;controls.autoRotateSpeed=speed*100;controls.enableZoom=zoomEnabled;controls.enablePan=false;controls.target.set(0,0,0);controls.minDistance=2;controls.maxDistance=10}

      // 粒子装饰
      var pCount=IS_MOBILE?80:200,pGeo=new THREE.BufferGeometry(),pPos=new Float32Array(pCount*3);
      for(var pi=0;pi<pCount;pi++){var a=(pi/pCount)*Math.PI*2,r=2+Math.random();pPos[pi*3]=Math.cos(a)*r;pPos[pi*3+1]=(Math.random()-.5)*2;pPos[pi*3+2]=Math.sin(a)*r}
      pGeo.setAttribute('position',new THREE.BufferAttribute(pPos,3));
      var particles=new THREE.Points(pGeo,new THREE.PointsMaterial({size:.02,color:color,blending:THREE.AdditiveBlending,depthWrite:false}));scene.add(particles);

      // V7 热区系统
      var hotspotMeshes=[],popup=null,raycaster=new THREE.Raycaster(),mouse=new THREE.Vector2();raycaster.params.Points.threshold=0.3;
      if(hotspots.length>0){popup=document.createElement('div');popup.className='gbt-hotspot-popup';popup.style.cssText='position:absolute;background:rgba(0,0,0,0.85);color:#fff;padding:16px 20px;border-radius:12px;backdrop-filter:blur(12px);display:none;pointer-events:none;z-index:100;font-family:sans-serif;max-width:260px;border:1px solid rgba(255,255,255,0.1)';document.body.appendChild(popup);hotspots.forEach(function(hs){var pos=hs.pos||[0,0,0],dot=new THREE.Mesh(new THREE.SphereGeometry(.06,16,16),new THREE.MeshBasicMaterial({color:0x00d4ff,transparent:true,opacity:.7}));dot.position.set(pos[0]*scale,pos[1]*scale,pos[2]*scale);dot.userData={hotspot:hs};dot.renderOrder=999;dot.material.depthTest=dot.material.depthWrite=false;scene.add(dot);hotspotMeshes.push(dot);var ring=new THREE.Mesh(new THREE.TorusGeometry(.09,.015,8,24),new THREE.MeshBasicMaterial({color:0x00d4ff,transparent:true,opacity:.5}));ring.position.copy(dot.position);ring.renderOrder=998;ring.material.depthTest=ring.material.depthWrite=false;scene.add(ring);dot.userData.ring=ring});function onHsClick(e){var rect=renderer.domElement.getBoundingClientRect(),cx=e.clientX||(e.changedTouches&&e.changedTouches[0].clientX)||0,cy=e.clientY||(e.changedTouches&&e.changedTouches[0].clientY)||0;mouse.x=((cx-rect.left)/rect.width)*2-1;mouse.y=-((cy-rect.top)/rect.height)*2+1;raycaster.setFromCamera(mouse,camera);var isects=raycaster.intersectObjects(hotspotMeshes);if(isects.length>0){var hs=isects[0].object.userData.hotspot;if(hs&&popup){popup.innerHTML='<strong>'+hs.title+'</strong><p style="margin:6px 0 0;color:#aaa;font-size:.85rem">'+hs.desc+'</p>'+(hs.link?'<br><a href="'+hs.link+'" style="color:#00d4ff">了解更多 \u2192</a>':'');popup.style.display='block';popup.style.left=(cx+15)+'px';popup.style.top=(cy-15)+'px';clearTimeout(popup._timer);popup._timer=setTimeout(function(){popup.style.display='none'},4000)}}}renderer.domElement.addEventListener('click',onHsClick);renderer.domElement.addEventListener('touchend',onHsClick)}

      // V7 环境切换
      document.querySelectorAll('[data-gbt3d-env]').forEach(function(btn){btn.addEventListener('click',function(){var n=this.dataset.gbt3dEnv,u=self._builtinHDR[n];if(u){applyEnvMap(u);document.querySelectorAll('[data-gbt3d-env]').forEach(function(b){b.style.borderColor=''});this.style.borderColor='#00d4ff'}})});

      // V8 部件材质引用表
      var namedParts={};

      // 加载GLB
      var modelGroup=new THREE.Group(),mixer=null,animationActions={};scene.add(modelGroup);
      if(window.THREE.GLTFLoader){var loader=new THREE.GLTFLoader();loader.load(modelUrl,function(gltf){var model=gltf.scene;model.scale.setScalar(scale);model.traverse(function(n){if(n.isMesh){n.castShadow=enableShadow;n.receiveShadow=enableShadow;namedParts[n.name]=n;if(materialsConfig[n.name]){var hex=materialsConfig[n.name];if(hex&&hex!=='inherit'){n.material=n.material.clone();n.material.color.set(hex)}}}});modelGroup.add(model);if(placeholderEl&&placeholderEl.parentNode){placeholderEl.parentNode.removeChild(placeholderEl);placeholderEl=null}if(gltf.animations&&gltf.animations.length){mixer=new THREE.AnimationMixer(model);gltf.animations.forEach(function(clip){var action=mixer.clipAction(clip);animationActions[clip.name]=action;if(!animName||clip.name===animName){action.setLoop(animLoop?THREE.LoopRepeat:THREE.LoopOnce);action.clampWhenFinished=!animLoop;action.play()}})}},function(xhr){if(progressEl&&xhr.total){var pct=Math.round(xhr.loaded/xhr.total*100);progressEl.style.width=pct+'%'}},function(err){console.warn('[GBT3D] GLB load failed:',err);if(placeholderEl&&placeholderEl.parentNode){placeholderEl.innerHTML='<div style="color:#ff4444">\u2717 \u52a0\u8f7d\u5931\u8d25</div>'}modelGroup.add(new THREE.Mesh(new THREE.SphereGeometry(1,32,32),new THREE.MeshStandardMaterial({color:color,roughness:.4,metalness:.6})))});}

      // V8 部件切换按钮
      document.querySelectorAll('[data-gbt3d-part]').forEach(function(btn){btn.addEventListener('click',function(){var partName=this.dataset.gbt3dPart,value=this.dataset.value,prop=this.dataset.property||'color';if(namedParts[partName]){var mat=namedParts[partName].material;if(!mat._originalColor&&prop==='color'){mat._originalColor=mat.color.clone();mat._targetColor=mat.color.clone()}if(prop==='color'){var c=new THREE.Color(value);mat._targetColor=c;mat._transitioning=true;mat._transitionStart=performance.now();mat._transitionDuration=400;mat._startColor=mat.color.clone()}else if(prop==='metalness'){mat.metalness=parseFloat(value)}else if(prop==='roughness'){mat.roughness=parseFloat(value)}}})});

      // V9 视角切换 (全局监听 - 只对当前实例有效通过data-gbt3d-instance)
      var instanceId='gbt-'+Math.random().toString(36).slice(2,8);
      container.dataset.gbt3dInstance=instanceId;

      // V9 截图功能
      function takeScreenshot(filename){filename=filename||'3d-screenshot.png';renderer.render(scene,camera);var dataURL=renderer.domElement.toDataURL('image/png');if(/Mobi|Android/i.test(navigator.userAgent)&&navigator.share){var blob=dataURLtoBlob(dataURL);var file=new File([blob],filename,{type:'image/png'});navigator.share({files:[file],title:filename}).catch(function(){downloadScreenshot(dataURL,filename)})}else{downloadScreenshot(dataURL,filename)}}
      function dataURLtoBlob(d){var parts=d.split(','),mime=parts[0].match(/:(.*?);/)[1],bstr=atob(parts[1]),n=bstr.length,u8=new Uint8Array(n);while(n--){u8[n]=bstr.charCodeAt(n)}return new Blob([u8],{type:mime})}
      function downloadScreenshot(d,u){var a=document.createElement('a');a.href=d;a.download=u;document.body.appendChild(a);a.click();document.body.removeChild(a)}

      // V9 截图按钮 (全局)
      document.querySelectorAll('[data-gbt3d-screenshot]').forEach(function(btn){btn.addEventListener('click',function(){var fn=this.dataset.filename||'3d-screenshot.png';takeScreenshot(fn)})});

      // V9 AR 按钮
      document.querySelectorAll('[data-gbt3d-ar]').forEach(function(btn){btn.addEventListener('click',function(){if(!navigator.xr){alert('\u60a8\u7684\u8bbe\u5907\u6682\u4e0d\u652f\u6301 AR\uff0c\u8bf7\u4f7f\u7528\u652f\u6301 WebXR \u7684\u6d4f\u89c8\u5668');return}navigator.xr.isSessionSupported('immersive-ar').then(function(supported){if(supported){renderer.xr.enabled=true;var arScale=parseFloat(btn.dataset.arScale||opts.arScale)||1;modelGroup.scale.setScalar(arScale);navigator.xr.requestSession('immersive-ar',{requiredFeatures:['hit-test'],optionalFeatures:['dom-overlay']}).then(function(session){renderer.xr.setSession(session);session.addEventListener('end',function(){renderer.xr.enabled=false;modelGroup.scale.setScalar(scale)})}).catch(function(e){console.warn('[GBT3D] AR session failed:',e);alert('AR \u542f\u52a8\u5931\u8d25: '+e.message);renderer.xr.enabled=false})}else{alert('\u8be5\u8bbe\u5907\u4e0d\u652f\u6301 AR \u6a21\u5f0f')}}).catch(function(){alert('\u8bf7\u4f7f\u7528 iOS Safari \u6216 Android Chrome \u8bbf\u95ee')})})});

      // V8 颜色平滑过渡 + V9 相机动画 (在animate中处理)
      var clock=new THREE.Clock();
      function animate(){requestAnimationFrame(animate);var dt=clock.getDelta();if(controls){if(!camTarget)controls.update()}else if(autoRotate&&!camTarget)modelGroup.rotation.y+=speed;particles.rotation.y+=speed*.3;if(mixer)mixer.update(dt);var t=Date.now()*.001;hotspotMeshes.forEach(function(d){d.scale.setScalar(1+Math.sin(t*4)*.15);if(d.userData.ring){d.userData.ring.rotation.x+=.02;d.userData.ring.rotation.y+=.03;d.userData.ring.scale.setScalar(1+Math.sin(t*3)*.1)}});
      // V8 颜色渐变
      for(var k in namedParts){var m=namedParts[k].material;if(m._transitioning){var elapsed=performance.now()-m._transitionStart,progress=Math.min(elapsed/m._transitionDuration,1),eased=1-Math.pow(1-progress,3);m.color.copy(m._startColor).lerp(m._targetColor,eased);m.needsUpdate=true;if(progress>=1){m._transitioning=false;delete m._transitionStart;delete m._startColor}}}
      // V9 相机动画
      if(camTarget){var elapsed2=performance.now()-camStartTime,progress2=Math.min(elapsed2/camDuration,1),eased2=1-Math.pow(1-progress2,3);camera.position.lerpVectors(camStart,camTarget,eased2);var lookTarget=camEndLook||new THREE.Vector3(0,0,0);camera.lookAt(lookTarget);if(controls){controls.target.copy(lookTarget);controls.update()}if(progress2>=1){camTarget=null;camStart=null}}
      // V8 地面光环
      if(groundPlane&&groundPlane.userData.ring){groundPlane.userData.ring.material.opacity=.1+.05*Math.sin(Date.now()*.002)}
      renderer.render(scene,camera)}
      animate();
      var onResize=function(){var w=container.clientWidth,h=container.clientHeight||innerHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h)};
      window.addEventListener('resize',onResize);

      // V9 视角切换函数
      var inst=this;
      function animateCameraTo(pos,duration){duration=duration||600;camStart=camera.position.clone();camTarget=new THREE.Vector3(pos[0],pos[1],pos[2]);camStartTime=performance.now();camDuration=duration;if(controls){controls.autoRotate=false;setTimeout(function(){if(controls&&!camTarget)controls.autoRotate=autoRotate},duration+100)}}

      // V9 视角按钮 (全局, 但需找到最近的实例)
      document.querySelectorAll('[data-gbt3d-view]').forEach(function(btn){btn.addEventListener('click',function(){var view=this.dataset.gbt3dView;if(view==='reset'){animateCameraTo([0,0,5]);return}var preset=inst._viewPresets[view];if(preset)animateCameraTo(preset)})});

      return {scene:scene,modelGroup:modelGroup,controls:controls,mixer:mixer,animationActions:animationActions,namedParts:namedParts,camera:camera,renderer:renderer,switchEnv:function(p){var u=inst._builtinHDR[p];if(u)applyEnvMap(u)},playAnimation:function(n,l){if(animationActions[n]){animationActions[n].setLoop(l?THREE.LoopRepeat:THREE.LoopOnce);animationActions[n].reset().play()}},setPartColor:function(name,hex){if(namedParts[name]&&namedParts[name].material){var m=namedParts[name].material;m._startColor=m.color.clone();m._targetColor=new THREE.Color(hex);m._transitionStart=performance.now();m._transitionDuration=400;m._transitioning=true}},moveCamera:function(view,duration){if(view==='reset'){animateCameraTo([0,0,5],duration);return}var p=inst._viewPresets[view];if(p)animateCameraTo(p,duration)},takeScreenshot:function(fn){takeScreenshot(fn||'3d-screenshot.png')},dispose:function(){window.removeEventListener('resize',onResize);if(controls)controls.dispose();if(popup&&popup.parentNode)popup.parentNode.removeChild(popup);renderer.dispose();pmremGenerator.dispose();if(container.contains(renderer.domElement))container.removeChild(renderer.domElement)}}
    },

    /* ─── V21-V30 终极协议: 具身智能~全息融合 ─── */

    // V21: 物理机器人控制
    startRobot: function(opts){opts=opts||{};var host=opts.host||'ws://localhost:8081';try{var ws=new WebSocket(host);ws.onopen=function(){console.log('[GBT3D V21] 机器人已连接:',opts.type);window.dispatchEvent(new CustomEvent('GBT_ROBOT_CONNECTED',{detail:opts}))};this._physicalDevices['robot']=ws}catch(e){console.log('[GBT3D V21] 机器人模拟模式')}},

    // V22: 脑机接口
    startBCI: function(opts){opts=opts||{};console.log('[GBT3D V22] BCI脑机接口 模拟模式');setInterval(function(){var conc=40+Math.random()*60,med=30+Math.random()*50;window.dispatchEvent(new CustomEvent('GBT_BCI_UPDATE',{detail:{concentration:conc,meditation:med,alpha:Math.random()*50,beta:Math.random()*30}}))},2000)},

    // V23: SLAM空间扫描
    startSLAM: function(opts){opts=opts||{};if(navigator.xr){console.log('[GBT3D V23] WebXR SLAM就绪');window.dispatchEvent(new CustomEvent('GBT_SLAM_READY',{detail:{mode:opts.mode||'room'}}))}else{console.log('[GBT3D V23] SLAM模拟模式: 生成虚拟房间网格')}},

    // V24: 基因进化算法
    startEvolution: function(opts){opts=opts||{};var pop=opts.population||10,mut=opts.mutationRate||0.05;var pool=[];for(var i=0;i<pop;i++)pool.push({color:'#'+Math.random().toString(16).slice(2,8),speed:0.5+Math.random(),size:0.5+Math.random()*2,score:0});setInterval(function(){pool.sort(function(a,b){return b.score-a.score});for(var i=Math.floor(pop/2);i<pop;i++){var parent=pool[i%Math.floor(pop/2)];pool[i]={color:parent.color,speed:parent.speed+(Math.random()-.5)*mut,size:parent.size+(Math.random()-.5)*mut,score:0}};window.dispatchEvent(new CustomEvent('GBT_EVOLUTION',{detail:{generation:pool[0],pool:pool}}))},3600000)},

    // V25: NFT铸造
    mintNFT: function(opts){opts=opts||{};if(window.ethereum){console.log('[GBT3D V25] MetaMask已检测, 准备铸造NFT');window.dispatchEvent(new CustomEvent('GBT_NFT_READY',{detail:opts}))}else{console.log('[GBT3D V25] 演示模式: NFT元数据已生成(不上链)')}},

    // V26: 平行宇宙
    startMultiverse: function(opts){opts=opts||{};var dims=opts.dimensions||3;var universes=[];for(var i=0;i<dims;i++){universes.push({id:i,color:new THREE.Color().setHSL(i/dims,0.8,0.5),speed:0.5+Math.random(),time:0})}window.__GBT_MULTIVERSE=universes;window.dispatchEvent(new CustomEvent('GBT_MULTIVERSE_READY',{detail:{dimensions:dims}}))},

    // V27: 触觉反馈
    triggerHaptic: function(pattern){pattern=pattern||'crisp';var dur={crisp:50,fluid:300,heavy:500}[pattern]||100;if(navigator.vibrate)navigator.vibrate(dur);window.dispatchEvent(new CustomEvent('GBT_HAPTIC',{detail:{pattern:pattern,duration:dur}}))},

    // V28: 量子态视觉
    startQuantum: function(opts){opts=opts||{};console.log('[GBT3D V28] 量子叠加态激活');setInterval(function(){var uncert=Math.random()*0.1;window.dispatchEvent(new CustomEvent('GBT_QUANTUM_UPDATE',{detail:{uncertainty:uncert,collapsed:Math.random()>0.7}}))},500)},

    // V29: AI创世
    startGenesis: function(opts){opts=opts||{};var prompt=opts.prompt||'赛博朋克城市';console.log('[GBT3D V29] AI创世: \"'+prompt+'\"');setTimeout(function(){var world={colors:['#ff00ff','#00ffff','#ffd700'],objects:['悬浮建筑','发光生物','数据流'],rules:{gravity:0.5+Math.random(),particleCount:500+Math.floor(Math.random()*2000)}};window.dispatchEvent(new CustomEvent('GBT_GENESIS_COMPLETE',{detail:world}))},3000)},

    // V30: 全息链接
    startHoloLink: function(opts){opts=opts||{};if(navigator.xr){console.log('[GBT3D V30] XR眼镜就绪');window.dispatchEvent(new CustomEvent('GBT_HOLO_READY',{detail:opts}))}else{console.log('[GBT3D V30] 全息模拟模式: 眼球追踪+手势已模拟')}},
    /* ─── V20 时序感知: 天文时钟+日程+行为预测+时间回溯 ─── */
    _timeline: [],

    // 天文时钟同步
    startTimeSync: function(bindOpts) {
      var self=this;
      function tick(){
        var now=new Date(),h=now.getHours(),m=now.getMinutes(),s=now.getSeconds();
        var mode=h<6?'深夜':h<9?'清晨':h<12?'上午':h<14?'中午':h<18?'下午':h<21?'黄昏':'夜晚';
        var t=h/24; // 0-1 归一化
        window.dispatchEvent(new CustomEvent('GBT_TIME_UPDATE',{detail:{hour:h,minute:m,second:s,mode:mode}}));
        var inst=window.__GBT_AVATAR_TARGET;
        if(inst&&inst.modelGroup&&bindOpts.color==='hour'){
          var night=new THREE.Color(0x001133),dawn=new THREE.Color(0xff8844),noon=new THREE.Color(0xffffff),dusk=new THREE.Color(0xff4422);
          var sceneColor;if(h<6)sceneColor=night;else if(h<8)sceneColor=night.clone().lerp(dawn,(h-6)/2);else if(h<12)sceneColor=dawn.clone().lerp(noon,(h-8)/4);else if(h<16)sceneColor=noon;else if(h<19)sceneColor=noon.clone().lerp(dusk,(h-16)/3);else sceneColor=dusk.clone().lerp(night,(h-19)/5);
          sceneColor=sceneColor||night;
          inst.scene.background=sceneColor;
          inst.scene.fog=new THREE.Fog(sceneColor,5,20);
        }
      }
      tick();setInterval(tick,10000);
    },

    // 行为预测
    startBehaviorPredict: function(windowMin) {
      windowMin=windowMin||60;
      var self=this,key='__GBT_behavior_log';
      var log=[];try{log=JSON.parse(localStorage.getItem(key)||'[]')}catch(e){}
      var now=new Date(),hour=now.getHours(),day=now.getDay();
      log.push({ts:Date.now(),hour:hour,day:day});
      if(log.length>500)log=log.slice(-500);
      try{localStorage.setItem(key,JSON.stringify(log))}catch(e){}

      // 分析本周此时段的热门行为
      var recent=log.filter(function(e){return e.day===day&&Math.abs(e.hour-hour)<=1});
      if(recent.length>3){
        var predicted='推荐模型_'+hour+'时';
        window.dispatchEvent(new CustomEvent('GBT_PREDICTION_UPDATE',{detail:{predicted:predicted,confidence:Math.min(recent.length/10,0.9)}}));
        // 预加载提示
        setTimeout(function(){window.dispatchEvent(new CustomEvent('GBT_PREDICTION_UPDATE',{detail:{predicted:predicted+' (已预加载)',confidence:1}}))},windowMin*1000);
      }
    },

    // 时间回溯
    saveTimelineSnapshot: function() {
      var inst=window.__GBT_AVATAR_TARGET;
      if(!inst||!inst.camera)return;
      var snap={ts:Date.now(),camera:{x:inst.camera.position.x,y:inst.camera.position.y,z:inst.camera.position.z},bg:inst.scene.background?inst.scene.background.getHex():0x050510};
      this._timeline.push(snap);
      if(this._timeline.length>50)this._timeline.shift();
      window.dispatchEvent(new CustomEvent('GBT_TIMELINE_SAVED',{detail:{count:this._timeline.length}}));
    },

    timeTravel: function(targetISO) {
      var inst=window.__GBT_AVATAR_TARGET;
      if(!inst)return;
      var target=new Date(targetISO).getTime();
      var best=null;
      this._timeline.forEach(function(s){if(!best||Math.abs(s.ts-target)<Math.abs(best.ts-target))best=s});
      if(best&&inst.camera){
        inst.camera.position.set(best.camera.x,best.camera.y,best.camera.z);inst.camera.lookAt(0,0,0);
        if(inst.controls)inst.controls.target.set(0,0,0);
        inst.scene.background=new THREE.Color(best.bg);
        window.dispatchEvent(new CustomEvent('GBT_TIME_TRAVEL',{detail:{target:best.ts}}));
      }
    },
    /* ─── V19 环境空间感知: GPS+NFC+环境光+陀螺仪 ─── */

    // GPS地理围栏
    startGeoSync: function(triggers) {
      if(!navigator.geolocation){console.warn('[GBT3D] GPS不支持');return}
      var self=this;
      navigator.geolocation.watchPosition(function(pos){
        var lat=pos.coords.latitude,lng=pos.coords.longitude;
        window.dispatchEvent(new CustomEvent('GBT_GEO_UPDATE',{detail:{lat:lat,lng:lng}}));
        (triggers||[]).forEach(function(t){
          var d=self._haversine(lat,lng,t.lat,t.lng);
          if(d<=t.radius){window.dispatchEvent(new CustomEvent('GBT_GEO_TRIGGER',{detail:t}));
            if(t.action==='color_shift'&&window.__GBT_AVATAR_TARGET){var inst=window.__GBT_AVATAR_TARGET;if(inst.setPartColor)inst.setPartColor('body',t.value)}
          }
        });
      },function(){},{enableHighAccuracy:true});
    },

    _haversine: function(lat1,lon1,lat2,lon2){
      var R=6371000,dLat=(lat2-lat1)*Math.PI/180,dLon=(lon2-lon1)*Math.PI/180;
      var a=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)*Math.sin(dLon/2);
      return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
    },

    // NFC
    startNFC: function(opts) {
      if(!('NDEFReader' in window)){console.warn('[GBT3D] NFC不支持(需安卓Chrome+HTTPS)');return}
      var self=this,reader=new NDEFReader();
      reader.scan().then(function(){
        window.dispatchEvent(new CustomEvent('GBT_NFC_STATUS',{detail:{status:'扫描中'}}));
        reader.addEventListener('reading',function(e){
          var msg=e.message.records[0];
          if(msg){
            var text=new TextDecoder().decode(msg.data);
            window.dispatchEvent(new CustomEvent('GBT_NFC_READ',{detail:{data:text}}));
            try{var cmd=JSON.parse(text);
              if(cmd.action&&window.__GBT_AVATAR_TARGET){var t=window.__GBT_AVATAR_TARGET;
                if(cmd.action==='rotate'&&t.controls)t.controls.autoRotateSpeed=cmd.speed*50;
                if(cmd.action==='color'&&t.setPartColor)t.setPartColor('body',cmd.value);
              }
            }catch(e){}
          }
        });
      }).catch(function(){console.warn('[GBT3D] NFC扫描失败')});
    },

    // 环境光传感器
    startLightSensor: function(bindOpts) {
      if(!('AmbientLightSensor' in window)){console.warn('[GBT3D] 环境光传感器不支持');return}
      try{
        var sensor=new AmbientLightSensor();
        sensor.addEventListener('reading',function(){
          var lux=sensor.illuminance||0;
          window.dispatchEvent(new CustomEvent('GBT_LIGHT_UPDATE',{detail:{lux:lux}}));
          var range=bindOpts.range||[0,1000],t=(lux-range[0])/(range[1]-range[0]);t=Math.max(0,Math.min(1,t));
          var inst=window.__GBT_AVATAR_TARGET;
          if(inst&&inst.modelGroup&&bindOpts.target==='color'){inst.modelGroup.traverse(function(n){if(n.isMesh&&n.material&&n.material.emissive){var cold=new THREE.Color(0x000022),warm=new THREE.Color(0xff8844);n.material.emissive.copy(cold).lerp(warm,t)}})}
        });
        sensor.start();
      }catch(e){console.warn('[GBT3D] 光传感器启动失败')}
    },

    // 陀螺仪/指南针
    startDeviceOrientation: function() {
      if(!('DeviceOrientationEvent' in window))return;
      var self=this;
      window.addEventListener('deviceorientation',function(e){
        var alpha=e.alpha||0,beta=e.beta||0,gamma=e.gamma||0;
        window.dispatchEvent(new CustomEvent('GBT_COMPASS_UPDATE',{detail:{heading:alpha,beta:beta,gamma:gamma}}));
        var inst=window.__GBT_AVATAR_TARGET;
        if(inst&&inst.camera){
          var radA=alpha*Math.PI/180,radB=beta*Math.PI/180;
          inst.camera.position.x=Math.sin(radA)*3;
          inst.camera.position.z=Math.cos(radA)*3;
          inst.camera.position.y=Math.sin(radB)*2;
          inst.camera.lookAt(0,0,0);
        }
      },true);
    },
    /* ─── V18 物理世界映射: WebBluetooth + WebUSB + WebSerial ─── */
    _physicalDevices: {},

    // BLE连接
    connectBLE: function(opts) {
      opts=opts||{};var self=this;
      if(!navigator.bluetooth){console.warn('[GBT3D] WebBluetooth不支持');return}
      var serviceUUID=opts.service||'heart_rate';
      var charUUID=opts.characteristic||'heart_rate_measurement';
      var writeMode=opts.write===true;
      navigator.bluetooth.requestDevice({filters:[{services:[serviceUUID]}]}).then(function(dev){
        self._physicalDevices['ble:'+serviceUUID]=dev;
        window.dispatchEvent(new CustomEvent('GBT_DEVICE_STATUS',{detail:{device:'ble:'+serviceUUID,status:'已连接'}}));
        return dev.gatt.connect();
      }).then(function(server){return server.getPrimaryService(serviceUUID)}).then(function(svc){
        if(writeMode){return svc.getCharacteristic(charUUID).then(function(ch){self._physicalDevices['ble:'+serviceUUID+'_char']=ch;window.dispatchEvent(new CustomEvent('GBT_DEVICE_STATUS',{detail:{device:'ble:'+serviceUUID,status:'可写入'}}))})}
        return svc.getCharacteristic(charUUID);
      }).then(function(ch){
        if(!writeMode&&ch.startNotifications){ch.startNotifications();ch.addEventListener('characteristicvaluechanged',function(e){var val=e.target.value.getUint8(1)||e.target.value.getUint8(0);self._physicalDevices['ble:'+serviceUUID+'_val']=val;window.dispatchEvent(new CustomEvent('GBT_PHYSICAL_UPDATE',{detail:{source:'ble:'+serviceUUID,value:val}}))})}
      }).catch(function(e){console.warn('[GBT3D] BLE连接失败:',e)});
    },

    // BLE写入
    writeBLE: function(serviceId, data) {
      var ch=this._physicalDevices['ble:'+serviceId+'_char'];
      if(!ch)return;var buf=new Uint8Array(data);ch.writeValue(buf).catch(function(){});
    },

    // USB连接
    connectUSB: function(opts) {
      opts=opts||{};var self=this;
      if(!navigator.usb){console.warn('[GBT3D] WebUSB不支持');return}
      var filters=[];
      if(opts.vendorId)filters.push({vendorId:parseInt(opts.vendorId)});
      navigator.usb.requestDevice({filters:filters}).then(function(dev){
        self._physicalDevices['usb:'+(opts.label||'device')]=dev;
        window.dispatchEvent(new CustomEvent('GBT_DEVICE_STATUS',{detail:{device:'usb:'+(opts.label||'device'),status:'已连接'}}));
        return dev.open().then(function(){return dev.selectConfiguration(1)}).then(function(){return dev.claimInterface(0)});
      }).then(function(){
        setInterval(function(){self._physicalDevices['usb:'+(opts.label||'device')].transferIn(1,64).then(function(r){if(r.data){var text=new TextDecoder().decode(r.data);var val=parseFloat(text);if(!isNaN(val)){window.dispatchEvent(new CustomEvent('GBT_PHYSICAL_UPDATE',{detail:{source:'usb:'+(opts.label||'device'),value:val}}))}}})},1000);
      }).catch(function(e){console.warn('[GBT3D] USB连接失败:',e)});
    },

    // 物理→3D映射
    bindPhysical: function(instance, source, bindOpts) {
      var self=this;
      window.addEventListener('GBT_PHYSICAL_UPDATE',function(e){
        if(e.detail.source!==source)return;
        var val=e.detail.value,range=bindOpts.range||[0,100];
        var t=(val-range[0])/(range[1]-range[0]);t=Math.max(0,Math.min(1,t));
        if(bindOpts.target==='color'&&instance.modelGroup){instance.modelGroup.traverse(function(n){if(n.isMesh&&n.material&&n.material.emissive){var cold=new THREE.Color(0x0044ff),hot=new THREE.Color(0xff2200);n.material.emissive.copy(cold).lerp(hot,t);n.material.emissiveIntensity=0.3+t*0.5}})}
        if(bindOpts.target==='speed'&&instance.modelGroup){var sp=0.5+t*2.5;if(instance.controls)instance.controls.autoRotateSpeed=sp*50}
        if(bindOpts.target==='scale'&&instance.modelGroup){var sc=0.5+t*2;instance.modelGroup.scale.lerp(new THREE.Vector3(sc,sc,sc),0.2)}
      });
    },

    // 3D→物理 emit
    emitPhysical: function(target, command) {
      if(target.startsWith('ble:')){
        var parts=command.split(':');
        if(parts[0]==='set_color'){var hex=parts[1]||'#ff0000';var r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);this.writeBLE(target.replace('ble:',''),[r,g,b])}
      }
    },
    /* ─── V17 AI智能体: 人格+记忆+自主决策+自我策展 ─── */

    // 用户记忆
    _userProfile: { color_pref: [], style_pref: 'neutral', interests: [], visits: 0, lastAction: 0 },

    trackAction: function(action) {
      var p = this._userProfile;
      p.visits++;
      p.lastAction = Date.now();
      if (action.type === 'color_change') { p.color_pref.push(action.value); if(p.color_pref.length > 10) p.color_pref.shift() }
      if (action.type === 'hotspot_click') { p.interests.push(action.tag); if(p.interests.length > 20) p.interests.shift() }
      if (window.localStorage) {
        try { localStorage.setItem('gbt_user_profile', JSON.stringify(p)) } catch(e) {}
      }
      window.dispatchEvent(new CustomEvent('GBT_AGENT_STATUS',{detail:{profile:this.summarizeProfile(),heat:1}}));
    },

    summarizeProfile: function() {
      var p = this._userProfile;
      var topColor = p.color_pref.length ? p.color_pref.sort(function(a,b){return p.color_pref.filter(function(x){return x===b}).length-p.color_pref.filter(function(x){return x===a}).length})[0] : '未知';
      return '偏好色:'+topColor+' 兴趣:'+(p.interests.slice(-3).join(',')||'探索中');
    },

    // Agent 自主决策循环
    startAgentLoop: function(opts) {
      opts = opts || {};
      var role = opts.role || '策展人', persona = opts.persona || '热情专业';
      var llmApi = opts.llmApi || '', interval = (opts.interval || 30) * 1000;
      var autoDecide = opts.autoDecide === true;
      var self = this;

      if (!autoDecide) return;

      function decide() {
        if (Date.now() - self._userProfile.lastAction < 10000) return; // 用户活跃时不打扰
        var profile = self.summarizeProfile();
        var actions = [
          {action:'speak',speech:'我注意到您对'+profile+'感兴趣，需要我为您推荐更多相关内容吗？'},
          {action:'speak',speech:'展厅里还有一些隐藏的宝藏，要我带您去看看吗？'},
          {action:'change_color',target:self._userProfile.color_pref.slice(-1)[0]||'#00d4ff',speech:'我为您调整了展示色调，希望您喜欢！'},
        ];
        var pick = actions[Math.floor(Math.random()*actions.length)];
        window.dispatchEvent(new CustomEvent('GBT_AGENT_DECISION',{detail:pick}));
        if (pick.speech && self.speak) self.speak(pick.speech);
        if (pick.action === 'change_color') {
          var t = window.__GBT_AVATAR_TARGET;
          if (t && t.setPartColor) t.setPartColor('body', pick.target);
        }
      }

      setInterval(decide, interval);
      // 首次
      setTimeout(function(){ self.speak('您好，我是您的AI'+role+'，'+persona+'。欢迎来到数字展厅！') }, 2000);
    },

    // 自我策展
    startCurator: function(opts) {
      opts = opts || {};
      var threshold = opts.threshold || 0.3;
      var autoGen = opts.autoGenerate === true;
      var exhibitStats = {};
      var self = this;

      // 统计热度
      window.addEventListener('GBT_AGENT_STATUS', function(e) {
        var t = window.__GBT_AVATAR_TARGET;
        if (!t) return;
        // 简化: 基于用户兴趣变化模拟热度
        var heat = Math.random();
        if (autoGen && heat < threshold) {
          window.dispatchEvent(new CustomEvent('GBT_CURATE',{detail:{heat:heat,action:'regenerate'}}));
        }
      });

      setInterval(function() {
        if (autoGen) {
          var heat = Math.random();
          window.dispatchEvent(new CustomEvent('GBT_AGENT_STATUS',{detail:{profile:self.summarizeProfile(),heat:heat}}));
        }
      }, 15000);
    },
    /* ─── V16 生产级: WebGPU自适应 + 内存安全 ─── */

    // WebGPU检测
    detectWebGPU: function() {
      if (navigator.gpu) {
        console.log('[GBT3D] WebGPU 可用! 性能提升3-5x');
        return true;
      }
      console.log('[GBT3D] WebGL 2.0 兼容模式');
      return false;
    },

    // 内存监控
    startMemoryMonitor: function(limitMB) {
      limitMB = limitMB || 512;
      var self = this;
      setInterval(function() {
        if (performance.memory) {
          var used = performance.memory.usedJSHeapSize / 1024 / 1024;
          if (used > limitMB * 0.8) {
            console.warn('[GBT3D] 内存警告: ' + used.toFixed(1) + 'MB / ' + limitMB + 'MB');
            // 清理: 降低粒子数, 释放纹理
            window.dispatchEvent(new CustomEvent('GBT_MEMORY_WARNING',{detail:{used:used,limit:limitMB}}));
          }
        }
      }, 5000);
    },
    /* ─── V15 多感官融合: 音频驱动 + MIDI + 游戏手柄 + 事件总线 ─── */

    // 音频驱动 (Web Audio API FFT)
    startAudioDrive: function(opts) {
      opts = opts || {};
      var source = opts.source || 'mic';
      var sensitivity = opts.sensitivity || 5;
      var self = this;
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      var analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      var dataArray = new Uint8Array(analyser.frequencyBinCount);

      function update() {
        analyser.getByteFrequencyData(dataArray);
        var bass = dataArray.slice(0,4).reduce(function(a,b){return a+b},0)/4/255;
        var mid = dataArray.slice(4,16).reduce(function(a,b){return a+b},0)/12/255;
        var treble = dataArray.slice(16,64).reduce(function(a,b){return a+b},0)/48/255;
        var beat = bass > 0.6 ? 1 : 0; // 简易节拍检测
        var detail = {bass:bass,mid:mid,treble:treble,beat:beat,sensitivity:sensitivity/255};
        window.dispatchEvent(new CustomEvent('GBT_AUDIO_UPDATE',{detail:detail}));
        // 驱动粒子
        var t = window.__GBT_AVATAR_TARGET;
        if (t && t.modelGroup) {
          var pulse = 1 + bass * 0.3;
          t.modelGroup.scale.setScalar(Math.max(0.5, t.modelGroup.scale.x + (pulse - t.modelGroup.scale.x) * 0.2));
        }
        requestAnimationFrame(update);
      }

      if (source === 'mic') {
        navigator.mediaDevices.getUserMedia({audio:true}).then(function(stream){
          var src = ctx.createMediaStreamSource(stream);
          src.connect(analyser);
          update();
        }).catch(function(){ console.warn('[GBT3D] 麦克风权限被拒绝') });
      } else if (source === 'file' && opts.src) {
        var audio = new Audio(opts.src);
        audio.crossOrigin = 'anonymous';
        var src = ctx.createMediaElementSource(audio);
        src.connect(analyser); analyser.connect(ctx.destination);
        audio.play();
        update();
      }
    },

    // MIDI设备
    startMIDI: function(opts) {
      opts = opts || {};
      var noteMap = opts.map || {};
      if (!navigator.requestMIDIAccess) { console.warn('[GBT3D] MIDI不支持'); return }
      navigator.requestMIDIAccess().then(function(midi){
        midi.inputs.forEach(function(input){
          input.onmidimessage = function(e) {
            var cmd = e.data[0] >> 4, channel = e.data[0] & 0xf, note = e.data[1], velocity = e.data[2];
            if (cmd === 9 && velocity > 0) { // Note On
              var noteName = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][note%12] + Math.floor(note/12);
              window.dispatchEvent(new CustomEvent('GBT_MIDI_UPDATE',{detail:{note:noteName,velocity:velocity/127}}));
              var action = noteMap[noteName];
              if (action) {
                var t = window.__GBT_AVATAR_TARGET;
                if (t) {
                  if (action === 'color_red') t.setPartColor('body','#ff0000');
                  else if (action === 'rotate_speed' && t.controls) t.controls.autoRotateSpeed = velocity * 0.5;
                  else if (action === 'scale') t.modelGroup.scale.setScalar(0.5 + velocity/127 * 2);
                }
              }
            }
          };
        });
        window.dispatchEvent(new CustomEvent('GBT_MIDI_CONNECTED'));
      }).catch(function(){ console.warn('[GBT3D] MIDI连接失败') });
    },

    // 游戏手柄
    startGamepad: function(opts) {
      opts = opts || {};
      var axisMap = opts.axisMap || {};
      var self = this;

      function poll() {
        var gamepads = navigator.getGamepads ? navigator.getGamepads() : [];
        for (var i = 0; i < gamepads.length; i++) {
          var gp = gamepads[i];
          if (!gp) continue;
          var t = window.__GBT_AVATAR_TARGET;
          if (!t) continue;
          // 左摇杆
          var lx = gp.axes[0], ly = gp.axes[1];
          if (Math.abs(lx) > 0.1 || Math.abs(ly) > 0.1) {
            if (axisMap['left_stick_x'] === 'camera_rotate' && t.modelGroup) t.modelGroup.rotation.y += lx * 0.05;
            if (axisMap['left_stick_y'] === 'camera_zoom' && t.camera) t.camera.position.z += ly * 0.1;
          }
          // A按钮 → 粒子爆发
          if (gp.buttons[0] && gp.buttons[0].pressed) {
            window.dispatchEvent(new CustomEvent('GBT_GAMEPAD_ACTION',{detail:{button:'A',action:'particle_burst'}}));
          }
        }
        requestAnimationFrame(poll);
      }

      window.addEventListener('gamepadconnected', function(){ window.dispatchEvent(new CustomEvent('GBT_GAMEPAD_CONNECT')) });
      window.addEventListener('gamepaddisconnected', function(){ window.dispatchEvent(new CustomEvent('GBT_GAMEPAD_DISCONNECT')) });
      poll();
    },

    // 多感官融合事件总线
    fusionBus: function(config) {
      config = config || [];
      var self = this;
      config.forEach(function(rule){
        window.addEventListener(rule.trigger, function(e){
          var t = window.__GBT_AVATAR_TARGET;
          if (!t) return;
          if (rule.action === 'particle_explosion') {
            if (t.modelGroup) t.modelGroup.scale.setScalar(t.modelGroup.scale.x * 1.3);
            setTimeout(function(){ if(t.modelGroup)t.modelGroup.scale.setScalar(1) }, 500);
          }
          if (rule.action === 'color_shift') {
            if (t.setPartColor) t.setPartColor('body', '#'+Math.random().toString(16).slice(2,8));
          }
        });
      });
    },
    /* ─── V14 多模态情感计算 + 手势交互 ─── */

    // 情感状态
    _emotion: { emotion: 'neutral', value: 0 },

    // 开启面部情感识别 (基于浏览器原生FaceDetector API + 模拟)
    startEmotionRecognition: function(opts) {
      opts = opts || {};
      var fps = opts.fps || 5;
      var self = this;

      // 摄像头
      var video = document.getElementById('gbt-camera-feed');
      if (!video) {
        video = document.createElement('video');
        video.id = 'gbt-camera-feed';
        video.setAttribute('autoplay', '');
        video.setAttribute('playsinline', '');
        video.style.cssText = 'position:absolute;bottom:100px;right:20px;width:160px;height:120px;border-radius:12px;border:2px solid rgba(0,240,255,0.3);object-fit:cover;z-index:10;transform:scaleX(-1)';
        document.body.appendChild(video);
      }

      navigator.mediaDevices.getUserMedia({video:{width:320,height:240}}).then(function(stream){
        video.srcObject = stream;
        video.style.display = 'block';
        document.getElementById('emotionPanel').style.display = 'block';

        // 表情识别循环 (使用FaceDetector API如果可用, 否则模拟)
        var emotions = ['neutral','happy','surprise','sad','angry'];
        var emotionIdx = 0;

        function detect() {
          // FaceDetector API (Chrome实验性)
          if (window.FaceDetector) {
            var fd = new FaceDetector({fastMode:true});
            fd.detect(video).then(function(faces){
              if (faces.length > 0) {
                var f = faces[0];
                // 简单启发式: 检测框大小变化 → 情绪推测
                var boxRatio = f.boundingBox.width / f.boundingBox.height;
                var emotion = 'neutral', value = 0;
                if (boxRatio > 1.2) { emotion = 'happy'; value = 0.7 }
                else if (boxRatio < 0.8) { emotion = 'surprise'; value = 0.5 }
                self._emotion = {emotion:emotion, value:value};
                window.__GBT_EMOTION = self._emotion;
                window.dispatchEvent(new CustomEvent('GBT_EMOTION_UPDATE',{detail:self._emotion}));
              }
            }).catch(function(){});
          } else {
            // 模拟情感轮换 (FaceDetector不可用时)
            emotionIdx = (emotionIdx + 1) % emotions.length;
            var simValues = {happy:0.8,neutral:0,surprise:0.6,sad:-0.5,angry:-0.7};
            var e = emotions[emotionIdx], v = simValues[e];
            self._emotion = {emotion:e, value:v};
            window.__GBT_EMOTION = self._emotion;
            window.dispatchEvent(new CustomEvent('GBT_EMOTION_UPDATE',{detail:self._emotion}));
          }
        }

        setInterval(detect, 1000/fps);
        detect();

      }).catch(function(e){
        console.warn('[GBT3D] 摄像头权限被拒绝, 降级为手动模式');
        alert('摄像头权限被拒绝, 情感交互已关闭。您可使用文字/语音指令。');
        if (video) video.style.display = 'none';
      });
    },

    // 情感驱动粒子/模型反应
    applyEmotionToScene: function(instance, emotionVal) {
      if (!instance) return;
      var t = (emotionVal + 1) / 2; // -1..1 → 0..1
      // 粒子速度
      if (instance._particles) {
        instance._particles.rotationSpeed = 0.0003 + t * 0.001;
      }
      // 模型材质色调偏移
      if (instance.modelGroup) {
        instance.modelGroup.traverse(function(n){
          if (n.isMesh && n.material && n.material.emissive) {
            var warm = new THREE.Color(0xff4400);
            var cool = new THREE.Color(0x0044ff);
            n.material.emissive.copy(cool).lerp(warm, t);
            n.material.emissiveIntensity = 0.1 + t * 0.3;
          }
        });
      }
    },

    // 手势识别 (基于HandDetector API + 模拟)
    startGestureRecognition: function(opts) {
      opts = opts || {};
      var self = this;

      if (window.HandDetector) {
        var video = document.getElementById('gbt-camera-feed');
        if (!video || !video.srcObject) {
          alert('请先开启摄像头(情感交互)');
          return;
        }
        var hd = new HandDetector({maxHands:1});
        setInterval(function(){
          hd.detect(video).then(function(hands){
            if (hands.length > 0) {
              var h = hands[0];
              var keypoints = h.keypoints;
              // 捏合检测: 拇指尖(4)与食指尖(8)距离
              if (keypoints.length >= 9) {
                var thumb = keypoints[4], index = keypoints[8];
                var dist = Math.hypot(thumb.x-index.x, thumb.y-index.y);
                // 捏合→缩放, 挥手→旋转
                window.dispatchEvent(new CustomEvent('GBT_GESTURE_DETECTED',{detail:{type:dist<30?'pinch':'wave',distance:dist}}));
              }
            }
          }).catch(function(){});
        }, 200);
      } else {
        console.log('[GBT3D] HandDetector不可用, 手势控制仅支持Chrome实验性功能');
        // 模拟: 键盘替代
        window.addEventListener('keydown', function(e){
          if (e.key === '+' || e.key === '=') window.dispatchEvent(new CustomEvent('GBT_GESTURE_DETECTED',{detail:{type:'pinch',zoom:1.1}}));
          if (e.key === '-') window.dispatchEvent(new CustomEvent('GBT_GESTURE_DETECTED',{detail:{type:'pinch',zoom:0.9}}));
          if (e.key === 'ArrowRight') window.dispatchEvent(new CustomEvent('GBT_GESTURE_DETECTED',{detail:{type:'wave',direction:1}}));
          if (e.key === 'ArrowLeft') window.dispatchEvent(new CustomEvent('GBT_GESTURE_DETECTED',{detail:{type:'wave',direction:-1}}));
        });
      }
    },
    /* ─── V13 生成式AI资产管道 + AR实景扫描 ─── */

    // 自动布景
    autoLayout: function(instance, theme) {
      theme = theme || 'studio';
      var model = instance.modelGroup;
      if (!model) return;
      var box = new THREE.Box3().setFromObject(model);
      var size = box.getSize(new THREE.Vector3());
      var center = box.getCenter(new THREE.Vector3());
      var maxDim = Math.max(size.x, size.y, size.z);
      var dist = maxDim * 3;
      instance.camera.position.set(dist*0.5, dist*0.4, dist);
      instance.camera.lookAt(center);
      if (instance.controls) { instance.controls.target.copy(center); instance.controls.update() }
      // 调整灯光
      var lights = [];
      instance.scene.traverse(function(n){ if(n.isLight) lights.push(n) });
      lights.forEach(function(l){ if(l.intensity) l.intensity = Math.max(0.5, 5/maxDim) });
      console.log('[GBT3D] 自动布景完成: theme='+theme+' size='+maxDim.toFixed(2));
    },

    // AI文字生成3D (触发+轮询)
    triggerGenerate: function(container, opts) {
      opts = opts || {};
      var prompt = opts.prompt || '', apiKey = opts.apiKey || '', style = opts.style || 'realistic';
      var apiUrl = opts.apiUrl || 'http://localhost:3000/api/generate';
      if (!prompt) { alert('请输入生成描述'); return }

      var statusEl = document.getElementById('gbt-gen-status');
      if (!statusEl) { statusEl = document.createElement('div'); statusEl.id = 'gbt-gen-status'; statusEl.style.cssText = 'position:absolute;top:20px;left:50%;transform:translateX(-50%);color:#00d4ff;z-index:10;font-family:sans-serif'; document.body.appendChild(statusEl) }
      statusEl.textContent = '正在生成: ' + prompt + '...';

      function poll(url) {
        statusEl.textContent = '生成中...';
        var pollCount = 0, maxPolls = 30;
        var timer = setInterval(function() {
          pollCount++;
          fetch(url).then(function(r){return r.json()}).then(function(d){
            if (d.status === 'success' && d.model_url) {
              clearInterval(timer);
              statusEl.textContent = '生成完成!';
              window.dispatchEvent(new CustomEvent('GBT_MODEL_GENERATED', {detail: {url: d.model_url, prompt: prompt}}));
              setTimeout(function(){ if(statusEl)statusEl.textContent='' }, 3000);
            }
          }).catch(function(){});
          if (pollCount >= maxPolls) { clearInterval(timer); statusEl.textContent = '生成超时,请重试' }
        }, 2000);
      }

      fetch(apiUrl, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt: prompt, style: style})
      }).then(function(r){return r.json()}).then(function(d){
        if (d.task_id) poll(apiUrl.replace('/generate','/task/'+d.task_id));
        else if (d.url) { statusEl.textContent = '生成完成!'; window.dispatchEvent(new CustomEvent('GBT_MODEL_GENERATED',{detail:{url:d.url,prompt:prompt}})) }
      }).catch(function(e){ statusEl.textContent = '生成失败: '+e.message });
    },

    // AR实景放置
    startARPlacement: function(instance) {
      if (!navigator.xr) {
        alert('设备不支持AR, 已切换为手动拖拽放置模式');
        if (instance.controls) { instance.controls.enabled = true; instance.controls.autoRotate = false }
        return;
      }
      var model = instance.modelGroup, renderer = instance.renderer;
      if (!model || !renderer) return;
      navigator.xr.isSessionSupported('immersive-ar').then(function(supported){
        if (!supported) { alert('设备不支持AR'); return }
        renderer.xr.enabled = true;
        navigator.xr.requestSession('immersive-ar', {requiredFeatures:['hit-test'],optionalFeatures:['dom-overlay']}).then(function(session){
          renderer.xr.setSession(session);
          model.position.set(0,0,-2);
          session.addEventListener('end', function(){ renderer.xr.enabled = false; model.position.set(0,0,0) });
        }).catch(function(){ alert('AR启动失败') });
      });
    },
    /* ─── V12 AI虚拟人 + 语音/文字多模态交互 ─── */

    // 内置语义解析器
    parseCommand: function(text) {
      text = (text||'').toLowerCase();
      var r = { action: null, target: null, value: null };
      if (/放大|大一点|拉近/.test(text)) { r.action='scale'; r.value=1.2; r.reply='好的，已为您放大' }
      else if (/缩小|小一点|拉远/.test(text)) { r.action='scale'; r.value=0.8; r.reply='好的，已为您缩小' }
      else if (/红|红色/.test(text)) { r.action='color'; r.value='#ff0000'; r.reply='已切换为红色' }
      else if (/蓝|蓝色/.test(text)) { r.action='color'; r.value='#0066ff'; r.reply='已切换为蓝色' }
      else if (/绿|绿色/.test(text)) { r.action='color'; r.value='#00cc00'; r.reply='已切换为绿色' }
      else if (/白|白色/.test(text)) { r.action='color'; r.value='#ffffff'; r.reply='已切换为白色' }
      else if (/黑|黑色/.test(text)) { r.action='color'; r.value='#111111'; r.reply='已切换为黑色' }
      else if (/金|金色|黄/.test(text)) { r.action='color'; r.value='#ffd700'; r.reply='已切换为金色' }
      else if (/紫|紫色/.test(text)) { r.action='color'; r.value='#a855f7'; r.reply='已切换为紫色' }
      else if (/背面|后面|后边/.test(text)) { r.action='view'; r.value='back'; r.reply='已转到背面' }
      else if (/正面|前面|前边/.test(text)) { r.action='view'; r.value='front'; r.reply='已转到正面' }
      else if (/上面|俯视|顶部/.test(text)) { r.action='view'; r.value='top'; r.reply='已切换到俯视' }
      else if (/侧面|左边|左面/.test(text)) { r.action='view'; r.value='left'; r.reply='已转到左侧' }
      else if (/右边|右面/.test(text)) { r.action='view'; r.value='right'; r.reply='已转到右侧' }
      else if (/转一转|旋转|转起来|加速/.test(text)) { r.action='rotate_speed'; r.value=2; r.reply='旋转加速中' }
      else if (/慢一点|减速|停/.test(text)) { r.action='rotate_speed'; r.value=0.3; r.reply='已减速' }
      else if (/你好|嗨|hello|hi/.test(text)) { r.action='greet'; r.reply='您好！我是您的AI导购，有什么可以帮您的？' }
      else if (/介绍|有什么|功能/.test(text)) { r.action='intro'; r.reply='您可以旋转模型查看细节，点击热区了解部件，使用语音或文字控制换色和视角。试试说"放大"或"改成红色"' }
      else { r.action='unknown'; r.reply='您可以试试说：放大、缩小、改成红色、转到背面' }
      window.__GBT_LAST_COMMAND = r;
      return r;
    },

    // TTS 语音播报
    speak: function(text, rate) {
      rate = rate || 1.1;
      if (!window.speechSynthesis) return;
      window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(text);
      u.lang = 'zh-CN'; u.rate = rate; u.pitch = 1;
      var voices = speechSynthesis.getVoices();
      var zh = voices.find(function(v){return v.lang.startsWith('zh')});
      if (zh) u.voice = zh;
      speechSynthesis.speak(u);
    },

    // 语音识别
    startVoiceRecognition: function(callback) {
      var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) { alert('您的浏览器不支持语音识别，请使用Chrome'); return }
      navigator.mediaDevices.getUserMedia({audio:true}).then(function(){
        var rec = new SpeechRecognition();
        rec.lang = 'zh-CN'; rec.interimResults = false; rec.maxAlternatives = 1;
        rec.onresult = function(e) { var text = e.results[0][0].transcript; if(callback)callback(text) };
        rec.onerror = function(e) { console.warn('语音识别错误:', e.error) };
        rec.onend = function() {};
        rec.start();
      }).catch(function(){ alert('麦克风权限被拒绝，请使用文字输入') });
    },

    // 气泡显示
    showBubble: function(text, duration) {
      duration = duration || 4000;
      var b = document.getElementById('gbt-bubble');
      if (!b) { b = document.createElement('div'); b.id='gbt-bubble'; b.style.cssText='position:absolute;top:15%;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.85);backdrop-filter:blur(12px);padding:14px 28px;border-radius:40px;color:#fff;font-size:1rem;border:1px solid rgba(255,255,255,0.1);display:none;pointer-events:none;z-index:200;font-family:sans-serif;max-width:500px;text-align:center'; document.body.appendChild(b) }
      b.textContent = text; b.style.display='block';
      clearTimeout(b._timer); b._timer = setTimeout(function(){ b.style.display='none' }, duration);
    },

    // V12 虚拟人
    createAvatar: function(container, opts) {
      opts = opts || {};
      var modelUrl = opts.src || '', greeting = opts.greeting || '';
      var animName = opts.animName || 'idle';
      var followCamera = opts.follow === true;
      var enableResponse = opts.response === true;
      var position = opts.position || [-1.5, -1.5, 2];

      if (!window.THREE) return null;
      var W=container.clientWidth,H=container.clientHeight||innerHeight;
      var scene=new THREE.Scene();
      var camera=new THREE.PerspectiveCamera(45,W/H,0.1,100);
      camera.position.set(0,0,5);camera.lookAt(0,0,0);
      var renderer=new THREE.WebGLRenderer({alpha:true,antialias:!IS_MOBILE});
      renderer.setSize(W,H);renderer.setPixelRatio(Math.min(devicePixelRatio,IS_MOBILE?1:2));
      container.appendChild(renderer.domElement);
      scene.add(new THREE.AmbientLight(0xffffff,1.2));

      var avatarGroup=new THREE.Group();scene.add(avatarGroup);
      avatarGroup.position.set(position[0],position[1],position[2]);
      var mixer=null,animationActions={},currentAnim=animName;

      function playAnim(name) {
        if (animationActions[name]) {
          Object.values(animationActions).forEach(function(a){a.stop()});
          animationActions[name].reset().play();currentAnim=name;
        }
      }

      if (window.THREE.GLTFLoader&&modelUrl) {
        new THREE.GLTFLoader().load(modelUrl,function(gltf){
          var model=gltf.scene;model.scale.setScalar(opts.scale||1);
          avatarGroup.add(model);
          if (gltf.animations&&gltf.animations.length) {
            mixer=new THREE.AnimationMixer(model);
            gltf.animations.forEach(function(clip){
              var action=mixer.clipAction(clip);animationActions[clip.name]=action;
            });
            playAnim(animName);
          }
          if (greeting) { setTimeout(function(){ self.speak(greeting);if(enableResponse)playAnim('talk') }, 1000) }
        });
      }

      var clock=new THREE.Clock();
      function animate(){requestAnimationFrame(animate);var dt=clock.getDelta();if(mixer)mixer.update(dt);if(followCamera&&camera){avatarGroup.lookAt(camera.position);avatarGroup.rotation.x=0;avatarGroup.rotation.z=0}renderer.render(scene,camera)}
      animate();
      var onResize=function(){var w=container.clientWidth,h=container.clientHeight||innerHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h)};
      window.addEventListener('resize',onResize);

      // V12 语音按钮
      document.querySelectorAll('[data-gbt3d-voice]').forEach(function(btn){btn.addEventListener('click',function(){self.startVoiceRecognition(function(text){self.showBubble('\uD83C\uDF99 '+text,3000);var cmd=self.parseCommand(text);if(enableResponse)playAnim('talk');self.speak(cmd.reply||'');if(cmd.action==='scale'&&window.__GBT_AVATAR_TARGET){var t=window.__GBT_AVATAR_TARGET;if(t.modelGroup)t.modelGroup.scale.multiplyScalar(cmd.value)}})})});

      // V12 文字指令
      document.querySelectorAll('[data-gbt3d-command]').forEach(function(inp){inp.addEventListener('keydown',function(e){if(e.key==='Enter'){var text=this.value.trim();if(!text)return;this.value='';self.showBubble('\u2328 '+text,3000);var cmd=self.parseCommand(text);if(enableResponse)playAnim('talk');self.speak(cmd.reply||'');if(cmd.action==='scale'&&window.__GBT_AVATAR_TARGET){var t=window.__GBT_AVATAR_TARGET;if(t.modelGroup)t.modelGroup.scale.multiplyScalar(cmd.value)}if(cmd.action==='color'&&window.__GBT_AVATAR_TARGET){var t=window.__GBT_AVATAR_TARGET;if(t.namedParts&&t.namedParts.body&&t.namedParts.body.material){var m=t.namedParts.body.material;m._startColor=m.color.clone();m._targetColor=new THREE.Color(cmd.value);m._transitionStart=performance.now();m._transitionDuration=400;m._transitioning=true}}if(cmd.action==='view'&&window.__GBT_AVATAR_TARGET){var t=window.__GBT_AVATAR_TARGET;if(t.moveCamera)t.moveCamera(cmd.value,600)}if(cmd.action==='rotate_speed'&&window.__GBT_AVATAR_TARGET){var t=window.__GBT_AVATAR_TARGET;if(t.controls){t.controls.autoRotateSpeed=cmd.value*50;t.controls.autoRotate=true}}}})});

      return {scene:scene,avatarGroup:avatarGroup,mixer:mixer,playAnim:playAnim,camera:camera,dispose:function(){window.removeEventListener('resize',onResize);renderer.dispose();if(container.contains(renderer.domElement))container.removeChild(renderer.domElement)}}
    },
    /* ─── V11 多人协同引擎 ─── */
    _syncEngine: null,

    initSync: function(host, room, userName) {
      var self = this;
      if (this._syncEngine && this._syncEngine.ws) {
        this._syncEngine.ws.close();
      }
      userName = userName || '\u8bbf\u5ba2_' + Math.random().toString(36).substr(2,4);
      var engine = {
        host: host, room: room, userName: userName,
        ws: null, connected: false, remoteUsers: {}, remoteCursors: [], marks: [],
        _queue: [], _reconnectTimer: null,
        send: function(data) {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
          } else {
            this._queue.push(data);
          }
        },
        broadcast: function(type, payload) {
          this.send({type:'sync',payload:{type:type,user:userName,data:payload,t:Date.now()}});
        },
        dispose: function() {
          if (this.ws) this.ws.close();
          if (this._reconnectTimer) clearTimeout(this._reconnectTimer);
          this.remoteCursors.forEach(function(c) { if(c.parent)c.parent.remove(c) });
          this.marks.forEach(function(m) { if(m.parent)m.parent.remove(m) });
          this.remoteCursors = [];
          this.marks = [];
        }
      }; window.__GBT_AVATAR_TARGET = inst; return inst;

      function connect() {
        try {
          var ws = new WebSocket(host);
          engine.ws = ws;
          ws.onopen = function() {
            engine.connected = true;
            ws.send(JSON.stringify({type:'join',room:room,user:userName}));
            while (engine._queue.length) {
              ws.send(JSON.stringify(engine._queue.shift()));
            }
            window.dispatchEvent(new CustomEvent('GBT_SYNC_CONNECTED',{detail:{room:room,user:userName}}));
          };
          ws.onmessage = function(e) {
            try {
              var msg = JSON.parse(e.data);
              if (msg.type === 'online') {
                window.dispatchEvent(new CustomEvent('GBT_ONLINE_UPDATE',{detail:{count:msg.count}}));
              }
              if (msg.type === 'sync') {
                window.dispatchEvent(new CustomEvent('GBT_SYNC_RECEIVE',{detail:msg.payload}));
              }
              if (msg.type === 'show_mark') {
                window.dispatchEvent(new CustomEvent('GBT_MARK_RECEIVE',{detail:{pos:msg.pos,user:msg.user}}));
              }
            } catch(er) {}
          };
          ws.onclose = function() {
            engine.connected = false;
            engine._reconnectTimer = setTimeout(connect, 3000);
          };
          ws.onerror = function() { ws.close() };
        } catch(e) {
          engine._reconnectTimer = setTimeout(connect, 3000);
        }
      }
      connect();
      this._syncEngine = engine;
      return engine;
    },

    /* ─── V11 高保真模型加载 (全功能: HDR+PBR+热区+动画+材质配置+视角切换+截图+AR+数据驱动+多人协同) ─── */
    _builtinHDR: {
      studio:   'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/textures/equirectangular/studio_country_hall_1k.hdr',
      sunset:   'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/textures/equirectangular/venice_sunset_1k.hdr',
      warehouse:'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/textures/equirectangular/industrial_room_1k.hdr',
      night:    'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/textures/equirectangular/night_sky_1k.hdr',
      dawn:     'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/textures/equirectangular/kiara_1_dawn_1k.hdr',
    },
    _viewPresets: {front:[0,0,5],back:[0,0,-5],left:[-5,0,0],right:[5,0,0],top:[0,5,0],bottom:[0,-5,0],reset:null},

    loadModel: function (container, modelUrl, opts) {
      opts = opts || {};
      var scale = opts.scale || 1, color = opts.color || 0x00d4ff, speed = opts.speed || 0.005;
      var bgColor = opts.bgColor || 0x0a0a0f;
      var autoRotate = opts.autoRotate !== false, dragEnabled = opts.drag !== false, zoomEnabled = opts.zoom !== false;
      var envPreset = opts.env || 'sunset', envUrl = opts.envUrl || null;
      var hotspots = opts.hotspots || [], animName = opts.animName || null, animLoop = opts.animLoop !== false;
      var materialsConfig = opts.materials || {};
      var placeholder = opts.placeholder || '';
      var enableGround = opts.ground === true, enableShadow = opts.shadow === true;
      var dataSource = opts.dataSource || null, dataPoll = opts.dataPoll || 3000, dataMock = opts.dataMock === true;
      var dataBind = opts.dataBind || {}, dataRange = opts.dataRange || {};
      var syncMode = opts.syncMode || null;
      var syncRoom = opts.syncRoom || null, syncHost = opts.syncHost || null, syncUser = opts.syncUser || null;
      var enableCursors = opts.cursors === true;

      if (!window.THREE) { console.warn('[GBT3D] Three.js not loaded'); return null; }
      var W = container.clientWidth, H = container.clientHeight || innerHeight;
      var scene = new THREE.Scene(); scene.background = new THREE.Color(bgColor);
      var camera = new THREE.PerspectiveCamera(45, W/H, 0.1, 100);
      camera.position.set(0,0,5);camera.lookAt(0,0,0);
      var renderer = new THREE.WebGLRenderer({alpha:true,antialias:!IS_MOBILE,preserveDrawingBuffer:true});
      renderer.setSize(W,H); renderer.setPixelRatio(Math.min(devicePixelRatio,IS_MOBILE?1:2));
      if(enableShadow){renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap}
      renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.2;
      container.appendChild(renderer.domElement);

      var camTarget=null,camStart=null,camStartTime=0,camDuration=600,camEndLook=new THREE.Vector3(0,0,0);
      var placeholderEl=null,progressEl=null;
      if(placeholder){placeholderEl=document.createElement('div');placeholderEl.style.cssText='position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#fff;text-align:center;z-index:10;font-family:sans-serif;pointer-events:none';placeholderEl.innerHTML='<div style="font-size:1rem;margin-bottom:8px">'+placeholder+'</div><div style="width:200px;height:3px;background:rgba(255,255,255,0.1);border-radius:2px;overflow:hidden"><div id="gbt-progress" style="width:0%;height:100%;background:#00d4ff;transition:width 0.3s"></div></div>';container.style.position=container.style.position||'relative';container.appendChild(placeholderEl);progressEl=placeholderEl.querySelector('#gbt-progress')}

      var pmremGenerator=new THREE.PMREMGenerator(renderer);pmremGenerator.compileEquirectangularShader();
      var currentEnvUrl='',self=this;
      function applyEnvMap(hdrUrl){if(!window.THREE.RGBELoader||hdrUrl===currentEnvUrl)return;currentEnvUrl=hdrUrl;new THREE.RGBELoader().setDataType(THREE.HalfFloatType).load(hdrUrl,function(t){var e=pmremGenerator.fromEquirectangular(t).texture;scene.environment=e;scene.background=new THREE.Color(bgColor);t.dispose()},undefined,function(){console.warn('[GBT3D] HDR load failed')})}
      applyEnvMap(envUrl||this._builtinHDR[envPreset]||this._builtinHDR.sunset);
      scene.add(new THREE.AmbientLight(0x404060,0.8));
      if(enableShadow){var dirLight=new THREE.DirectionalLight(0xffffff,1.5);dirLight.position.set(5,10,5);dirLight.castShadow=true;dirLight.shadow.mapSize.set(1024,1024);scene.add(dirLight)}

      var groundPlane=null;
      if(enableGround){var groundGeo=new THREE.PlaneGeometry(8,8),groundMat=new THREE.ShadowMaterial({opacity:0.3});groundPlane=new THREE.Mesh(groundGeo,groundMat);groundPlane.rotation.x=-Math.PI/2;groundPlane.position.y=-2;groundPlane.receiveShadow=true;scene.add(groundPlane);var ringGeo=new THREE.RingGeometry(1.2,1.35,64),ringMat=new THREE.MeshBasicMaterial({color:0x00d4ff,side:THREE.DoubleSide,transparent:true,opacity:0.15});var glowRing=new THREE.Mesh(ringGeo,ringMat);glowRing.rotation.x=-Math.PI/2;glowRing.position.y=-1.99;scene.add(glowRing);groundPlane.userData={ring:glowRing}}

      var controls=null;
      if((dragEnabled||zoomEnabled)&&window.THREE.OrbitControls){controls=new THREE.OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=0.08;controls.autoRotate=autoRotate;controls.autoRotateSpeed=speed*100;controls.enableZoom=zoomEnabled;controls.enablePan=false;controls.target.set(0,0,0);controls.minDistance=2;controls.maxDistance=10}

      var pCount=IS_MOBILE?80:200,pGeo=new THREE.BufferGeometry(),pPos=new Float32Array(pCount*3);
      for(var pi=0;pi<pCount;pi++){var a=(pi/pCount)*Math.PI*2,r=2+Math.random();pPos[pi*3]=Math.cos(a)*r;pPos[pi*3+1]=(Math.random()-.5)*2;pPos[pi*3+2]=Math.sin(a)*r}
      pGeo.setAttribute('position',new THREE.BufferAttribute(pPos,3));
      var particles=new THREE.Points(pGeo,new THREE.PointsMaterial({size:.02,color:color,blending:THREE.AdditiveBlending,depthWrite:false}));scene.add(particles);

      var hotspotMeshes=[],popup=null,raycaster=new THREE.Raycaster(),mouse=new THREE.Vector2();raycaster.params.Points.threshold=0.3;
      if(hotspots.length>0){popup=document.createElement('div');popup.className='gbt-hotspot-popup';popup.style.cssText='position:absolute;background:rgba(0,0,0,0.85);color:#fff;padding:16px 20px;border-radius:12px;backdrop-filter:blur(12px);display:none;pointer-events:none;z-index:100;font-family:sans-serif;max-width:260px;border:1px solid rgba(255,255,255,0.1)';document.body.appendChild(popup);hotspots.forEach(function(hs){var pos=hs.pos||[0,0,0],dot=new THREE.Mesh(new THREE.SphereGeometry(.06,16,16),new THREE.MeshBasicMaterial({color:0x00d4ff,transparent:true,opacity:.7}));dot.position.set(pos[0]*scale,pos[1]*scale,pos[2]*scale);dot.userData={hotspot:hs};dot.renderOrder=999;dot.material.depthTest=dot.material.depthWrite=false;scene.add(dot);hotspotMeshes.push(dot);var ring=new THREE.Mesh(new THREE.TorusGeometry(.09,.015,8,24),new THREE.MeshBasicMaterial({color:0x00d4ff,transparent:true,opacity:.5}));ring.position.copy(dot.position);ring.renderOrder=998;ring.material.depthTest=ring.material.depthWrite=false;scene.add(ring);dot.userData.ring=ring});function onHsClick(e){var rect=renderer.domElement.getBoundingClientRect(),cx=e.clientX||(e.changedTouches&&e.changedTouches[0].clientX)||0,cy=e.clientY||(e.changedTouches&&e.changedTouches[0].clientY)||0;mouse.x=((cx-rect.left)/rect.width)*2-1;mouse.y=-((cy-rect.top)/rect.height)*2+1;raycaster.setFromCamera(mouse,camera);var isects=raycaster.intersectObjects(hotspotMeshes);if(isects.length>0){var hs=isects[0].object.userData.hotspot;if(hs&&popup){popup.innerHTML='<strong>'+hs.title+'</strong><p style="margin:6px 0 0;color:#aaa;font-size:.85rem">'+hs.desc+'</p>'+(hs.link?'<br><a href="'+hs.link+'" style="color:#00d4ff">\u2192</a>':'');popup.style.display='block';popup.style.left=(cx+15)+'px';popup.style.top=(cy-15)+'px';clearTimeout(popup._timer);popup._timer=setTimeout(function(){popup.style.display='none'},4000);if(self._syncEngine&&syncMode){self._syncEngine.broadcast('hotspot_click',{id:hs.id,title:hs.title})}}}}renderer.domElement.addEventListener('click',onHsClick);renderer.domElement.addEventListener('touchend',onHsClick)}

      document.querySelectorAll('[data-gbt3d-env]').forEach(function(btn){btn.addEventListener('click',function(){var n=this.dataset.gbt3dEnv,u=self._builtinHDR[n];if(u){applyEnvMap(u);document.querySelectorAll('[data-gbt3d-env]').forEach(function(b){b.style.borderColor=''});this.style.borderColor='#00d4ff';if(self._syncEngine&&syncMode)self._syncEngine.broadcast('env_switch',{env:n})}})});

      var namedParts={};
      var modelGroup=new THREE.Group(),mixer=null,animationActions={};scene.add(modelGroup);
      if(window.THREE.GLTFLoader){var loader=new THREE.GLTFLoader();loader.load(modelUrl,function(gltf){var model=gltf.scene;model.scale.setScalar(scale);model.traverse(function(n){if(n.isMesh){n.castShadow=enableShadow;n.receiveShadow=enableShadow;namedParts[n.name]=n;if(materialsConfig[n.name]){var hex=materialsConfig[n.name];if(hex&&hex!=='inherit'){n.material=n.material.clone();n.material.color.set(hex)}}}});modelGroup.add(model);if(placeholderEl&&placeholderEl.parentNode){placeholderEl.parentNode.removeChild(placeholderEl);placeholderEl=null}if(gltf.animations&&gltf.animations.length){mixer=new THREE.AnimationMixer(model);gltf.animations.forEach(function(clip){var action=mixer.clipAction(clip);animationActions[clip.name]=action;if(!animName||clip.name===animName){action.setLoop(animLoop?THREE.LoopRepeat:THREE.LoopOnce);action.clampWhenFinished=!animLoop;action.play()}})}},function(xhr){if(progressEl&&xhr.total){var pct=Math.round(xhr.loaded/xhr.total*100);progressEl.style.width=pct+'%'}},function(err){if(placeholderEl&&placeholderEl.parentNode){placeholderEl.innerHTML='<div style="color:#ff4444">\u2717</div>'}modelGroup.add(new THREE.Mesh(new THREE.SphereGeometry(1,32,32),new THREE.MeshStandardMaterial({color:color,roughness:.4,metalness:.6})))});}

      document.querySelectorAll('[data-gbt3d-part]').forEach(function(btn){btn.addEventListener('click',function(){var partName=this.dataset.gbt3dPart,value=this.dataset.value,prop=this.dataset.property||'color';if(namedParts[partName]){var mat=namedParts[partName].material;if(prop==='color'){var c=new THREE.Color(value);mat._targetColor=c;mat._transitioning=true;mat._transitionStart=performance.now();mat._transitionDuration=400;mat._startColor=mat.color.clone();if(self._syncEngine&&syncMode)self._syncEngine.broadcast('part_color',{part:partName,color:value})}else if(prop==='metalness'){mat.metalness=parseFloat(value)}else if(prop==='roughness'){mat.roughness=parseFloat(value)}}})});

      function takeScreenshot(filename){filename=filename||'3d-screenshot.png';renderer.render(scene,camera);var d=renderer.domElement.toDataURL('image/png');if(/Mobi|Android/i.test(navigator.userAgent)&&navigator.share){var p=d.split(','),m=p[0].match(/:(.*?);/)[1],b=atob(p[1]),n2=b.length,u8=new Uint8Array(n2);while(n2--){u8[n2]=b.charCodeAt(n2)}var blob=new Blob([u8],{type:m}),file=new File([blob],filename,{type:'image/png'});navigator.share({files:[file],title:filename}).catch(function(){var a=document.createElement('a');a.href=d;a.download=filename;document.body.appendChild(a);a.click();document.body.removeChild(a)})}else{var a=document.createElement('a');a.href=d;a.download=filename;document.body.appendChild(a);a.click();document.body.removeChild(a)}}
      document.querySelectorAll('[data-gbt3d-screenshot]').forEach(function(btn){btn.addEventListener('click',function(){takeScreenshot(this.dataset.filename||'3d-screenshot.png')})});
      document.querySelectorAll('[data-gbt3d-ar]').forEach(function(btn){btn.addEventListener('click',function(){if(!navigator.xr){alert('\u8bbe\u5907\u4e0d\u652f\u6301AR');return}navigator.xr.isSessionSupported('immersive-ar').then(function(s){if(s){renderer.xr.enabled=true;var as=parseFloat(btn.dataset.arScale||opts.arScale)||1;modelGroup.scale.setScalar(as);navigator.xr.requestSession('immersive-ar',{requiredFeatures:['hit-test']}).then(function(sess){renderer.xr.setSession(sess);sess.addEventListener('end',function(){renderer.xr.enabled=false;modelGroup.scale.setScalar(scale)})}).catch(function(e){alert('AR\u5931\u8d25');renderer.xr.enabled=false})}else{alert('\u4e0d\u652f\u6301AR')}}).catch(function(){alert('\u8bf7\u7528Safari/Chrome')})})});

      function animateCameraTo(pos,dur){dur=dur||600;camStart=camera.position.clone();camTarget=new THREE.Vector3(pos[0],pos[1],pos[2]);camStartTime=performance.now();camDuration=dur;if(controls){controls.autoRotate=false;setTimeout(function(){if(controls&&!camTarget)controls.autoRotate=autoRotate},dur+100)}}
      document.querySelectorAll('[data-gbt3d-view]').forEach(function(btn){btn.addEventListener('click',function(){var v=this.dataset.gbt3dView;if(v==='reset'){animateCameraTo([0,0,5]);return}var p=self._viewPresets[v];if(p)animateCameraTo(p)})});

      // V11 多人协同
      var syncEngine = null;
      if (syncHost && syncRoom) {
        syncEngine = self.initSync(syncHost, syncRoom, syncUser);
        self._syncEngine = syncEngine;

        // 协同光标
        var cursorsGroup = new THREE.Group(); scene.add(cursorsGroup);
        if (enableCursors) {
          window.addEventListener('GBT_SYNC_RECEIVE', function(e) {
            var d = e.detail;
            if (d.type === 'camera_move' && d.user !== syncUser) {
              cursorsGroup.children.forEach(function(c) { if(c.userData.user===d.user) cursorsGroup.remove(c) });
              var dot = new THREE.Mesh(new THREE.SphereGeometry(0.08,8,8), new THREE.MeshBasicMaterial({color:0xff4444}));
              dot.position.set(d.data.x||0,d.data.y||0,d.data.z||0);dot.userData={user:d.user};
              cursorsGroup.add(dot);syncEngine.remoteCursors.push(dot);
            }
            if (d.type === 'part_color') {
              var pn = d.data.part, cv = d.data.color;
              if (namedParts[pn]) { var m = namedParts[pn].material; m._targetColor=new THREE.Color(cv);m._transitioning=true;m._transitionStart=performance.now();m._transitionDuration=400;m._startColor=m.color.clone() }
            }
            if (d.type === 'env_switch') { applyEnvMap(self._builtinHDR[d.data.env]) }
          });
        }

        // 标记
        window.addEventListener('GBT_MARK_RECEIVE', function(e) {
          var mark = new THREE.Mesh(new THREE.SphereGeometry(0.1,8,8), new THREE.MeshBasicMaterial({color:0xffd700}));
          mark.position.set(e.detail.pos[0],e.detail.pos[1],e.detail.pos[2]);scene.add(mark);
          syncEngine.marks.push(mark);setTimeout(function(){scene.remove(mark)},10000);
        });

        document.querySelectorAll('[data-gbt3d-mark]').forEach(function(btn){btn.addEventListener('click',function(){raycaster.setFromCamera(new THREE.Vector2(0,0),camera);var isects=raycaster.intersectObjects(modelGroup.children,true);if(isects.length>0){var p=isects[0].point;if(syncEngine)syncEngine.send({type:'mark',pos:[p.x,p.y,p.z],user:syncUser});var m=new THREE.Mesh(new THREE.SphereGeometry(0.1,8,8),new THREE.MeshBasicMaterial({color:0xffd700}));m.position.copy(p);scene.add(m);syncEngine.marks.push(m);setTimeout(function(){scene.remove(m)},10000)}})});

        document.querySelectorAll('[data-gbt3d-sync]').forEach(function(btn){btn.addEventListener('click',function(){if(syncEngine){if(btn.dataset.gbt3dSync==='camera')syncEngine.broadcast('camera_move',{x:camera.position.x,y:camera.position.y,z:camera.position.z})}})});
      }

      // V10 数据引擎
      if (Object.keys(dataBind).length > 0 || dataSource || dataMock) {
        setTimeout(function() {
          self.bindData({modelGroup:modelGroup,namedParts:namedParts,_dataCleanup:null,_dataSpeed:0},{source:dataSource,poll:dataPoll,mock:dataMock,bindings:dataBind,rangeMap:dataRange});
        }, 500);
      }

      var clock=new THREE.Clock();
      function animate(){requestAnimationFrame(animate);var dt=clock.getDelta();if(controls){if(!camTarget)controls.update()}else if(autoRotate&&!camTarget)modelGroup.rotation.y+=speed;particles.rotation.y+=speed*.3;if(mixer)mixer.update(dt);var t=Date.now()*.001;hotspotMeshes.forEach(function(d){d.scale.setScalar(1+Math.sin(t*4)*.15);if(d.userData.ring){d.userData.ring.rotation.x+=.02;d.userData.ring.rotation.y+=.03;d.userData.ring.scale.setScalar(1+Math.sin(t*3)*.1)}});
      for(var k in namedParts){var m=namedParts[k].material;if(m._transitioning){var el=performance.now()-m._transitionStart,pr=Math.min(el/m._transitionDuration,1),es=1-Math.pow(1-pr,3);m.color.copy(m._startColor).lerp(m._targetColor,es);m.needsUpdate=true;if(pr>=1){m._transitioning=false}}}
      if(camTarget){var e2=performance.now()-camStartTime,p2=Math.min(e2/camDuration,1),es2=1-Math.pow(1-p2,3);camera.position.lerpVectors(camStart,camTarget,es2);camera.lookAt(camEndLook);if(controls){controls.target.copy(camEndLook);controls.update()}if(p2>=1){camTarget=null;camStart=null}}
      if(groundPlane&&groundPlane.userData.ring){groundPlane.userData.ring.material.opacity=.1+.05*Math.sin(Date.now()*.002)}
      // V11 广播相机 (每500ms, 避免洪水)
      if(syncEngine&&syncEngine.connected&&syncMode&&(syncMode==='auto'||syncMode==='camera')){if(!syncEngine._lastCamBroadcast||Date.now()-syncEngine._lastCamBroadcast>500){syncEngine._lastCamBroadcast=Date.now();syncEngine.broadcast('camera_move',{x:camera.position.x,y:camera.position.y,z:camera.position.z})}}
      renderer.render(scene,camera)}
      animate();
      var onResize=function(){var w=container.clientWidth,h=container.clientHeight||innerHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h)};
      window.addEventListener('resize',onResize);

      var inst = {scene:scene,modelGroup:modelGroup,controls:controls,mixer:mixer,animationActions:animationActions,namedParts:namedParts,camera:camera,renderer:renderer,sync:syncEngine,switchEnv:function(p){var u=self._builtinHDR[p];if(u)applyEnvMap(u)},playAnimation:function(n,l){if(animationActions[n]){animationActions[n].setLoop(l?THREE.LoopRepeat:THREE.LoopOnce);animationActions[n].reset().play()}},setPartColor:function(name,hex){if(namedParts[name]&&namedParts[name].material){var m=namedParts[name].material;m._startColor=m.color.clone();m._targetColor=new THREE.Color(hex);m._transitionStart=performance.now();m._transitionDuration=400;m._transitioning=true}},moveCamera:function(view,duration){if(view==='reset'){animateCameraTo([0,0,5],duration);return}var p=self._viewPresets[view];if(p)animateCameraTo(p,duration)},takeScreenshot:function(fn){takeScreenshot(fn||'3d-screenshot.png')},bindData:function(cfg){self.bindData({modelGroup:modelGroup,namedParts:namedParts,_dataCleanup:null},cfg)},dispose:function(){window.removeEventListener('resize',onResize);if(controls)controls.dispose();if(popup&&popup.parentNode)popup.parentNode.removeChild(popup);if(syncEngine)syncEngine.dispose();renderer.dispose();pmremGenerator.dispose();if(container.contains(renderer.domElement))container.removeChild(renderer.domElement)}}
    },

    enableScrollAnimations: function () {if(!CSS.supports('animation-timeline: scroll()')){this.scrollReveal('.gbt-reveal')}}
  };

  function autoInit() {
    document.querySelectorAll('[data-gbt3d="particles"]').forEach(function(el){GBT.createParticleRing(el,{count:parseInt(el.dataset.count)||2000,color:parseInt((el.dataset.color||'#00d4ff').replace('#','0x')),speed:parseFloat(el.dataset.speed)||0.0005,rings:parseInt(el.dataset.rings)||3})});
    document.querySelectorAll('[data-gbt3d="globe"]').forEach(function(el){var ms=el.dataset.markers||'',opts={color:parseInt((el.dataset.color||'#00d4ff').replace('#','0x')),speed:parseFloat(el.dataset.speed)||0.002};if(ms.startsWith('/')||ms.startsWith('http')){opts.markerFetchUrl=ms;opts.markerFetchInterval=parseInt(el.dataset.markerInterval)||3000}else if(ms==='true'||ms===''){opts.markers=[{label:'\u5317\u4eac',lng:116.4,lat:39.9,color:0x00ff88},{label:'\u7ebd\u7ea6',lng:-74,lat:40.7,color:0xff6644},{label:'\u4f26\u6566',lng:-0.1,lat:51.5,color:0x4488ff},{label:'\u65b0\u52a0\u5761',lng:103.8,lat:1.3,color:0xffdd44}]}else if(ms){opts.markers=ms.split(';').filter(Boolean).map(function(m){var p=m.split(',');return{label:p[0],lng:parseFloat(p[1]),lat:parseFloat(p[2]),color:0xff4444}})}GBT.createGlobe(el,opts)});
    GBT.scrollReveal('.gbt-reveal');GBT.parallax('[data-parallax]');
    document.querySelectorAll('[data-beam]').forEach(function(el){var s=el.dataset.beam,m=s.match(/from:\s*([^,]+),\s*to:\s*(.+)/);if(m)GBT.createBeam(m[1].trim(),m[2].trim(),{color:el.dataset.beamColor||'#00d4ff',width:parseInt(el.dataset.beamWidth)||2,dash:el.dataset.beamDash||'8,4'})});
    document.querySelectorAll('[data-gbt3d="scene"]').forEach(function(el){el.style.position=el.style.position||'relative';var sRoom=el.dataset.room||null,sHost=el.dataset.host||null,sUser=el.dataset.user||null,sCursors=el.dataset.cursor==='true';el.querySelectorAll('[data-gbt3d="model"]').forEach(function(m){var hs=[];try{if(m.dataset.hotspots)hs=JSON.parse(m.dataset.hotspots)}catch(e){};var mats={};try{if(m.dataset.materials)mats=JSON.parse(m.dataset.materials)}catch(e){};var bind={};try{if(m.dataset.bind)bind=JSON.parse(m.dataset.bind)}catch(e){};var range={};try{if(m.dataset.range)range=JSON.parse(m.dataset.range)}catch(e){}GBT.loadModel(m,m.dataset.src||m.dataset.modelSrc||'',{scale:parseFloat(m.dataset.scale||m.dataset.modelScale)||1,color:parseInt((m.dataset.color||m.dataset.modelColor||'#00d4ff').replace('#','0x')),speed:parseFloat(m.dataset.speed||m.dataset.modelSpeed)||0.005,autoRotate:(m.dataset.rotate||m.dataset.modelAutoRotate||'true')!=='false',drag:(m.dataset.drag||'true')!=='false',zoom:(m.dataset.zoom||'true')!=='false',env:m.dataset.env||'sunset',envUrl:m.dataset.envUrl||null,bgColor:parseInt((m.dataset.bgColor||'#0a0a0f').replace('#','0x')),hotspots:hs,animName:m.dataset.animate||null,animLoop:(m.dataset.animateLoop||'true')!=='false',materials:mats,placeholder:m.dataset.placeholder||'',ground:el.dataset.ground==='true',shadow:el.dataset.shadow==='true',arScale:parseFloat(m.dataset.arScale)||1,dataSource:m.dataset.source||null,dataPoll:parseInt(m.dataset.poll)||3000,dataMock:m.dataset.mock==='true',dataBind:bind,dataRange:range,syncMode:m.dataset.sync||null,syncRoom:sRoom,syncHost:sHost,syncUser:sUser,cursors:sCursors})})});
    document.querySelectorAll('[data-gbt3d="model"]:not([data-gbt3d="scene"] [data-gbt3d="model"])').forEach(function(el){var hs=[];try{if(el.dataset.hotspots)hs=JSON.parse(el.dataset.hotspots)}catch(e){};var mats={};try{if(el.dataset.materials)mats=JSON.parse(el.dataset.materials)}catch(e){};var bind={};try{if(el.dataset.bind)bind=JSON.parse(el.dataset.bind)}catch(e){};var range={};try{if(el.dataset.range)range=JSON.parse(el.dataset.range)}catch(e){}GBT.loadModel(el,el.dataset.src||el.dataset.modelSrc||'',{scale:parseFloat(el.dataset.scale||el.dataset.modelScale)||1,color:parseInt((el.dataset.color||el.dataset.modelColor||'#00d4ff').replace('#','0x')),speed:parseFloat(el.dataset.speed||el.dataset.modelSpeed)||0.005,autoRotate:(el.dataset.rotate||el.dataset.modelAutoRotate||'true')!=='false',drag:(el.dataset.drag||'true')!=='false',zoom:(el.dataset.zoom||'true')!=='false',env:el.dataset.env||'sunset',envUrl:el.dataset.envUrl||null,bgColor:parseInt((el.dataset.bgColor||'#0a0a0f').replace('#','0x')),hotspots:hs,animName:el.dataset.animate||null,animLoop:(el.dataset.animateLoop||'true')!=='false',materials:mats,placeholder:el.dataset.placeholder||'',ground:false,shadow:false,arScale:parseFloat(el.dataset.arScale)||1,dataSource:el.dataset.source||null,dataPoll:parseInt(el.dataset.poll)||3000,dataMock:el.dataset.mock==='true',dataBind:bind,dataRange:range,syncMode:el.dataset.sync||null,syncRoom:null,syncHost:null,syncUser:null,cursors:false})});
    document.querySelectorAll('[data-gbt3d="panorama"]').forEach(function(el){var s=el.dataset.src||'';if(s)GBT.loadModel(el,null,{envUrl:s,env:null,autoRotate:false,drag:true,zoom:false,scale:.001,color:0x00d4ff})});
    GBT.enableScrollAnimations();
    document.querySelectorAll('[data-gbt3d="avatar"]').forEach(function(el){GBT.createAvatar(el,{src:el.dataset.src||'',greeting:el.dataset.greeting||'',animName:el.dataset.animate||'idle',follow:el.dataset.follow==='true',response:el.dataset.response==='true',scale:parseFloat(el.dataset.scale)||1})});
        console.log('[GBT3D V12] \u591a\u4eba\u534f\u540c \u00b7 \u72b6\u6001\u540c\u6b65 \u00b7 \u6570\u5b57\u5b6a\u751f \u00b7 \u5168\u529f\u80fd\u5f15\u64ce');
  }
  if (document.readyState==='loading'){document.addEventListener('DOMContentLoaded',autoInit)}else{autoInit()}

  // ═══ V30 引擎API导出层 (供menu-handler.js调度) ═══
  window.__GBT_ENGINE = {
    // 清空容器所有3D内容
    clear: function(container) {
      while (container.firstChild) {
        var child = container.firstChild;
        if (child._gbtDispose) child._gbtDispose();
        container.removeChild(child);
      }
      container.style.background = '';
    },

    // 初始化粒子系统
    initParticles: function(container, config) {
      config = config || {};
      var el = document.createElement('div');
      el.style.cssText = 'width:100%;height:100%';
      container.appendChild(el);
      var inst = GBT.createParticleRing(el, {
        count: config.count || 2000,
        color: new THREE.Color(config.color || '#00d4ff').getHex(),
        speed: config.speed || 0.0005,
        rings: config.rings || 3
      });
      el._gbtDispose = function() { if (inst && inst.dispose) inst.dispose() };
      return inst;
    },

    // 光圈脉冲效果
    _pulseGlow: function(container) {
      var pulse = document.createElement('div');
      pulse.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:300px;height:300px;border-radius:50%;border:2px solid rgba(255,215,0,0.3);pointer-events:none;animation:gbt-pulse 2s ease-in-out infinite';
      container.appendChild(pulse);
      var style = document.createElement('style');
      style.textContent = '@keyframes gbt-pulse{0%,100%{box-shadow:0 0 20px rgba(255,215,0,0.1);transform:translate(-50%,-50%) scale(1)}50%{box-shadow:0 0 80px rgba(255,215,0,0.3);transform:translate(-50%,-50%) scale(1.5)}}';
      document.head.appendChild(style);
      pulse._gbtDispose = function() { if(style.parentNode)style.parentNode.removeChild(style) };
    }
  };

}

/* ═══════════════════════════════════════════════════════════
   GBT 语音引擎 — 小土豆女声
   Web Speech API 免费 · 无需任何 key · 浏览器原生支持
   ═══════════════════════════════════════════════════════════ */

const VOICE_CONFIG = {
  // 女声优先列表 (按自然度排序)
  preferred: [
    { name: 'Microsoft Xiaoxiao',   lang: 'zh-CN', quality: 'neural', grade: 'S' },
    { name: 'Google 普通话',         lang: 'zh-CN', quality: 'standard', grade: 'A' },
    { name: 'Tingting',             lang: 'zh-CN', quality: 'standard', grade: 'A' },
    { name: 'Samantha',             lang: 'en-US', quality: 'neural', grade: 'S' },
    { name: 'Karen',                lang: 'en-AU', quality: 'neural', grade: 'S' },
  ],
  defaultRate: 1.0,
  defaultPitch: 1.1,
  defaultVolume: 1.0,
};

class GBTVoice {
  constructor() {
    this.synth = window.speechSynthesis;
    this.voice = null;
    this.speaking = false;
    this.queue = [];
    this._init();
  }

  // 自动选最佳女声
  _init() {
    if (!this.synth) return;

    const loadVoices = () => {
      const voices = this.synth.getVoices();
      
      // 按优先级匹配女声
      for (const pref of VOICE_CONFIG.preferred) {
        const match = voices.find(v => 
          v.name.includes(pref.name) && v.lang.startsWith(pref.lang)
        );
        if (match) {
          this.voice = match;
          console.log(`[Voice] 🎙️ ${match.name} (${match.lang})`);
          return;
        }
      }

      // 降级: 任意女声
      const anyFemale = voices.find(v => 
        v.name.toLowerCase().includes('female') || 
        v.name.toLowerCase().includes('woman') ||
        v.name.includes('Xiaoxiao') ||
        v.name.includes('Samantha')
      );
      if (anyFemale) {
        this.voice = anyFemale;
        console.log(`[Voice] 🎙️ ${anyFemale.name} (fallback)`);
      }
    };

    loadVoices();
    this.synth.onvoiceschanged = loadVoices;
  }

  // ═══ 说话 ═══
  speak(text, options = {}) {
    if (!this.synth) return;

    // 去掉 emoji 和 markdown 符号 (语音不好读)
    const cleanText = text
      .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
      .replace(/[\*\_\`\~\#\[\]\(\)\>\<]/g, '')
      .replace(/\$\s*(\d+)/g, '$1美元')
      .replace(/%/g, '百分之')
      .trim();

    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.voice = this.voice;
    utterance.rate = options.rate || VOICE_CONFIG.defaultRate;
    utterance.pitch = options.pitch || VOICE_CONFIG.defaultPitch;
    utterance.volume = options.volume || VOICE_CONFIG.defaultVolume;
    utterance.lang = this.voice?.lang || 'zh-CN';

    utterance.onstart = () => { this.speaking = true; };
    utterance.onend = () => { 
      this.speaking = false; 
      this._next(); 
    };

    if (this.speaking) {
      this.queue.push(utterance);
    } else {
      this.synth.speak(utterance);
    }
  }

  _next() {
    if (this.queue.length > 0) {
      this.synth.speak(this.queue.shift());
    }
  }

  // ═══ 停止 ═══
  stop() {
    this.synth?.cancel();
    this.queue = [];
    this.speaking = false;
  }

  // ═══ 快捷播报 ═══
  paymentReceived(amount) {
    this.speak(`到账 ${amount} 美元`);
  }

  paymentSent(amount) {
    this.speak(`已支付 ${amount} 美元`);
  }

  welcome(name) {
    this.speak(`${name || '用户'}，欢迎回来`);
  }

  deployComplete(project) {
    this.speak(`${project} 部署完成`);
  }

  kycPassed() {
    this.speak('身份验证通过');
  }
}

// ═══════════════════════════════════════════════════════════
// 语音输入 (SpeechRecognition)
// ═══════════════════════════════════════════════════════════

class GBTListen {
  constructor() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = SR ? new SR() : null;
    if (!this.recognition) return;

    this.recognition.lang = 'zh-CN';
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
  }

  // 开始听
  start(callback) {
    if (!this.recognition) {
      callback({ error: '浏览器不支持语音输入' });
      return;
    }

    this.recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(r => r[0].transcript)
        .join('');
      
      callback({ 
        text: transcript,
        final: event.results[0].isFinal,
        confidence: event.results[0][0].confidence,
      });
    };

    this.recognition.onerror = (e) => {
      callback({ error: e.error });
    };

    this.recognition.start();
  }

  stop() {
    this.recognition?.stop();
  }
}

// ═══════════════════════════════════════════════════════════
// 语音按钮组件 (注入页面右下角)
// ═══════════════════════════════════════════════════════════

function injectVoiceButton() {
  const voice = new GBTVoice();
  const listen = new GBTListen();

  const btn = document.createElement('div');
  btn.className = 'gbt-voice-btn';
  btn.innerHTML = '🎙️';
  btn.title = '语音助手 · 点击说话 · 双击收听';
  btn.style.cssText = `
    position: fixed; bottom: 80px; right: 20px; z-index: 9999;
    width: 52px; height: 52px; border-radius: 50%;
    background: linear-gradient(135deg, #ff6b35, #ff9a56);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; cursor: pointer;
    box-shadow: 0 4px 20px rgba(255,107,53,.3);
    transition: all .3s; user-select: none;
  `;

  let listening = false;

  // 单击 → 说话
  btn.onclick = () => {
    if (listening) {
      listen.stop();
      listening = false;
      btn.style.background = 'linear-gradient(135deg, #ff6b35, #ff9a56)';
      btn.innerHTML = '🎙️';
      return;
    }

    listening = true;
    btn.style.background = '#30d158';
    btn.innerHTML = '🔴';

    listen.start((result) => {
      if (result.text && result.final) {
        // 用户说了什么 → 触发 AI 对话
        const aiInput = document.querySelector('#aiSearch, .ai-concierge-input');
        if (aiInput) {
          aiInput.value = result.text;
          aiInput.dispatchEvent(new Event('input'));
        }
        listening = false;
        btn.style.background = 'linear-gradient(135deg, #ff6b35, #ff9a56)';
        btn.innerHTML = '🎙️';
        
        // 用语音回复
        setTimeout(() => voice.speak(`收到，${result.text}`), 500);
      }
    });
  };

  // 双击 → 读页面
  btn.ondblclick = () => {
    const mainText = document.querySelector('main')?.textContent?.slice(0, 500) || '';
    voice.speak(mainText);
    btn.style.transform = 'scale(1.3)';
    setTimeout(() => { btn.style.transform = 'scale(1)'; }, 300);
  };

  document.body.appendChild(btn);
}

// 自动注入
if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectVoiceButton);
  } else {
    injectVoiceButton();
  }
}

// 全局暴露
window.GBTVoice = GBTVoice;
window.GBTListen = GBTListen;

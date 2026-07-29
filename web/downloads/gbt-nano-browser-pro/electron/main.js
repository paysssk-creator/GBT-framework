// GBT Nano Browser Pro — Electron Main Process
// AI全控 · 指纹隐身 · 2Captcha · 股票操盘
const { app, BrowserWindow, session, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let bridgeProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400, height: 900, minWidth: 900, minHeight: 600,
    frame: false, titleBarStyle: 'hidden',
    backgroundColor: '#0a0a0f',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false, contextIsolation: true,
      webviewTag: true, sandbox: false,
    }
  });

  // ── 拦截外部导航 → 全部关在应用内 ──
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    mainWindow.loadURL(url);
    return { action: 'deny' };
  });
  mainWindow.webContents.on('did-create-window', (child) => {
    child.webContents.on('will-navigate', (e, url) => {
      e.preventDefault();
      mainWindow.loadURL(url);
    });
  });

  // 所有权限放行
  session.defaultSession.setPermissionRequestHandler((wc, perm, cb) => cb(true));

  // 指纹隐身
  injectFingerprint();

  mainWindow.loadFile(path.join(__dirname, '..', 'src', 'index.html'));

  // 错误监控
  mainWindow.webContents.on('did-fail-load', (e, code, desc, url) => {
    console.error('[RENDERER] Failed to load:', url, code, desc);
  });
  mainWindow.webContents.on('crashed', () => console.error('[RENDERER] CRASHED'));
  mainWindow.webContents.on('unresponsive', () => console.error('[RENDERER] UNRESPONSIVE'));
  mainWindow.webContents.on('console-message', (e, level, msg) => {
    console.log('[RENDERER LOG]', msg);
  });
}
function startBridge() {
  // 优先 extraResources, 其次开发路径, app.asar 内 Python 读不了
  const paths = [
    path.join(process.resourcesPath || '', 'server', 'bridge.py'),  // 打包后
    path.join(__dirname, '..', 'server', 'bridge.py'),               // 开发模式
  ];
  
  let bridgePath = null;
  for (const p of paths) {
    if (require('fs').existsSync(p)) { bridgePath = p; break; }
  }
  
  if (!bridgePath) {
    console.log('[Bridge] bridge.py not found - AI features require GBTxiaotudouV5 project');
    return;
  }
  
  try {
    bridgeProcess = spawn('python', [bridgePath], {
      cwd: path.dirname(bridgePath),
      stdio: ['pipe', 'pipe', 'pipe']
    });
    bridgeProcess.on('close', (code) => {
      console.log('[Bridge] exited with', code);
      if (code !== 0 && code !== null) setTimeout(startBridge, 10000);
    });
    console.log('[Bridge] started:', bridgePath);
  } catch (e) {
    console.log('[Bridge] failed to start:', e.message);
  }
}

// ═══════════════════ 指纹隐身引擎 ═══════════════════
function injectFingerprint() {
  const uaPool = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
  ];
  const ua = uaPool[Math.floor(Math.random() * uaPool.length)];
  session.defaultSession.webRequest.onBeforeSendHeaders((details, cb) => {
    details.requestHeaders['User-Agent'] = ua;
    cb({ requestHeaders: details.requestHeaders });
  });
}
ipcMain.handle('ai-ask', async (event, { question, context }) => {
  try {
    const resp = await fetch('http://localhost:15999/ai', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, context })
    });
    return await resp.json();
  } catch (e) {
    return { ok: false, error: 'AI桥接未连接' };
  }
});

ipcMain.handle('ai-open-url', async (event, { url }) => {
  mainWindow.loadURL(url);
  return { ok: true };
});

ipcMain.handle('ai-stock-status', async () => {
  try {
    const resp = await fetch('http://localhost:8766/api/status');
    return await resp.json();
  } catch (e) {
    return { running: false };
  }
});

ipcMain.handle('get-knowledge', async (event, { topic }) => {
  const knowledge = require('../src/knowledge.js');
  return knowledge.getTopic(topic);
});

ipcMain.handle('search-knowledge', async (event, { query }) => {
  const knowledge = require('../src/knowledge.js');
  return knowledge.search(query);
});

// ═══════════════════ 生命周期 ═══════════════════
app.whenReady().then(createWindow);
app.on('window-all-closed', () => {
  if (bridgeProcess) bridgeProcess.kill();
  app.quit();
});
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

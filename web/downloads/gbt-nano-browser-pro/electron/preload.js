// GBT Nano Browser Pro — Preload Script
// 安全桥接: 暴露有限 API 给渲染进程
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('GBT', {
  // AI
  askAI: (question, context) => ipcRenderer.invoke('ai-ask', { question, context }),
  openURL: (url) => ipcRenderer.invoke('ai-open-url', { url }),
  
  // Stock
  getStockStatus: () => ipcRenderer.invoke('ai-stock-status'),
  
  // Knowledge
  getKnowledge: (topic) => ipcRenderer.invoke('get-knowledge', { topic }),
  searchKnowledge: (query) => ipcRenderer.invoke('search-knowledge', { query }),
  
  // App
  getVersion: () => '1.0.0',
  platform: process.platform,
  
  // Fingerprint
  getFingerprint: () => ({
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    screenRes: `${screen.width}x${screen.height}`,
    colorDepth: screen.colorDepth,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    cores: navigator.hardwareConcurrency,
    memory: navigator.deviceMemory || 'N/A'
  })
});

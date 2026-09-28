'use strict';

const { contextBridge, ipcRenderer } = require('electron');

// جسر محدود: الصفحات المحلية فقط تحتاجه، ولا يكشف أي شيء من Node للسيرفر
contextBridge.exposeInMainWorld('khat', {
  getServer: () => ipcRenderer.invoke('config:get-server'),
  setServer: (value) => ipcRenderer.invoke('config:set-server', value),
  retry: () => ipcRenderer.invoke('app:retry'),
  openSettings: () => ipcRenderer.invoke('app:open-settings'),
});

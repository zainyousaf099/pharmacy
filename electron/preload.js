const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    getServerInfo: () => ipcRenderer.invoke('get-server-info'),
    restartServer: () => ipcRenderer.invoke('restart-server'),
    openBrowser: (url) => ipcRenderer.invoke('open-browser', url),
    closeApp: () => ipcRenderer.invoke('close-app'),
    onServerReady: (callback) => ipcRenderer.on('server-ready', (event, data) => callback(data)),
    onServerLog: (callback) => ipcRenderer.on('server-log', (event, data) => callback(data))
});

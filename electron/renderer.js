let serverInfo = null;

// Wait for server to be ready
window.electronAPI.onServerReady((data) => {
    serverInfo = data;
    updateServerInfo(data);
    showDashboard();
});

// Listen to server logs
window.electronAPI.onServerLog((log) => {
    addLogEntry(log);
});

// Initialize on load
window.addEventListener('DOMContentLoaded', async () => {
    try {
        const info = await window.electronAPI.getServerInfo();
        if (info) {
            serverInfo = info;
            updateServerInfo(info);
            setTimeout(showDashboard, 2000);
        }
    } catch (error) {
        console.error('Failed to get server info:', error);
    }
});

function updateServerInfo(data) {
    document.getElementById('server-ip').value = data.ip;
    document.getElementById('server-port').value = data.port;
    document.getElementById('server-url').value = data.url;
}

function showDashboard() {
    document.getElementById('loading-screen').classList.add('hidden');
    document.getElementById('main-dashboard').classList.remove('hidden');
}

function copyIP() {
    const ipInput = document.getElementById('server-ip');
    ipInput.select();
    navigator.clipboard.writeText(ipInput.value);
    showNotification('IP Address copied to clipboard!');
}

function copyURL() {
    const urlInput = document.getElementById('server-url');
    urlInput.select();
    navigator.clipboard.writeText(urlInput.value);
    showNotification('URL copied to clipboard!');
}

function openPanel(panel) {
    if (!serverInfo) return;
    
    let url = serverInfo.url;
    
    switch(panel) {
        case 'doctor-login':
            url += '/accounts/doctor-login/';
            break;
        case 'opd-login':
            url += '/accounts/opd-login/';
            break;
        case 'pharmacy-login':
            url += '/accounts/pharmacy-login/';
            break;
        case 'inventory':
            url += '/inventory/';
            break;
    }
    
    window.electronAPI.openBrowser(url);
}

function openMainPage() {
    if (!serverInfo) return;
    window.electronAPI.openBrowser(serverInfo.url);
}

async function restartServer() {
    showNotification('Restarting server...');
    addLogEntry('Restarting server...');
    
    try {
        const info = await window.electronAPI.restartServer();
        serverInfo = info;
        updateServerInfo(info);
        showNotification('Server restarted successfully!');
        addLogEntry('Server restarted successfully!');
    } catch (error) {
        showNotification('Failed to restart server');
        addLogEntry('Error: Failed to restart server');
    }
}

function addLogEntry(text) {
    const logContainer = document.getElementById('log-container');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = new Date().toLocaleTimeString() + ' - ' + text.trim();
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
    
    // Keep only last 50 entries
    const entries = logContainer.getElementsByClassName('log-entry');
    if (entries.length > 50) {
        logContainer.removeChild(entries[0]);
    }
}

function showNotification(message) {
    // Simple notification - you can enhance this
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(76, 175, 80, 0.9);
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.5);
        z-index: 10000;
        font-size: 1rem;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

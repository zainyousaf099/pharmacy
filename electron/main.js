const { app, BrowserWindow, ipcMain, Menu, Tray, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const os = require('os');
const fs = require('fs');
const NetworkDiscovery = require('./network-discovery');

let mainWindow;
let djangoProcess;
let serverIP = 'localhost';
let serverPort = 8000;
let appMode = 'discovering'; // 'server' or 'client'
let discovery = null;
let splashWindow = null;

// Create splash screen
function createSplashScreen() {
    splashWindow = new BrowserWindow({
        width: 500,
        height: 300,
        frame: false,
        transparent: false,
        alwaysOnTop: true,
        backgroundColor: '#1a1a2e',
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    const splashHTML = `
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                color: white;
            }
            .container {
                text-align: center;
            }
            h1 {
                font-size: 24px;
                margin-bottom: 20px;
            }
            .spinner {
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top: 4px solid white;
                width: 50px;
                height: 50px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            p {
                font-size: 16px;
                margin: 10px 0;
            }
            .status {
                font-size: 14px;
                opacity: 0.9;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 Clinic Management System</h1>
            <div class="spinner"></div>
            <p id="status">Starting application...</p>
            <div class="status">
                <p>Please wait while we set up</p>
            </div>
        </div>
        <script>
            const { ipcRenderer } = require('electron');
            ipcRenderer.on('splash-status', (event, message) => {
                document.getElementById('status').textContent = message;
            });
        </script>
    </body>
    </html>
    `;

    splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(splashHTML)}`);
}

function updateSplashStatus(message) {
    if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.webContents.send('splash-status', message);
    }
}

function closeSplash() {
    if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.close();
        splashWindow = null;
    }
}

// Get local IP address
function getLocalIP() {
    const interfaces = os.networkInterfaces();
    for (const name of Object.keys(interfaces)) {
        for (const iface of interfaces[name]) {
            // Skip internal and non-IPv4 addresses
            if (iface.family === 'IPv4' && !iface.internal) {
                return iface.address;
            }
        }
    }
    return 'localhost';
}

// Log file for debugging on client machines
function getLogPath() {
    const isDev = !app.isPackaged;
    if (isDev) {
        return path.join(__dirname, '..', 'electron-debug.log');
    } else {
        return path.join(app.getPath('userData'), 'electron-debug.log');
    }
}

function writeLog(message) {
    const logPath = getLogPath();
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}\n`;
    console.log(message);
    try {
        fs.appendFileSync(logPath, logMessage);
    } catch (err) {
        console.error('Failed to write log:', err);
    }
}

// Start Django server
function startDjangoServer() {
    return new Promise((resolve, reject) => {
        writeLog('Starting Django server...');
        
        // Check if running in development or production
        const isDev = !app.isPackaged;
        
        let pythonPath, manageScript, djangoDir;
        
        if (isDev) {
            // Development mode - use local env
            pythonPath = path.join(__dirname, '..', 'env', 'Scripts', 'python.exe');
            manageScript = path.join(__dirname, '..', 'manage.py');
            djangoDir = path.join(__dirname, '..');
        } else {
            // Production mode - packaged app
            // electron-builder puts resources in different locations
            const exePath = app.getPath('exe');
            const exeDir = path.dirname(exePath);
            
            writeLog('=== Path Detection ===');
            writeLog('Exe Path: ' + exePath);
            writeLog('Exe Dir: ' + exeDir);
            writeLog('__dirname: ' + __dirname);
            writeLog('process.resourcesPath: ' + process.resourcesPath);
            
            // Try multiple possible locations for the Django app
            const possiblePaths = [
                // Option 1: resources/django-app with portable python
                {
                    python: path.join(process.resourcesPath, 'django-app', 'python-portable', 'python.exe'),
                    manage: path.join(process.resourcesPath, 'django-app', 'manage.py'),
                    dir: path.join(process.resourcesPath, 'django-app')
                },
                // Option 2: resources/python-portable (separate folder)
                {
                    python: path.join(process.resourcesPath, 'python-portable', 'python.exe'),
                    manage: path.join(process.resourcesPath, 'django-app', 'manage.py'),
                    dir: path.join(process.resourcesPath, 'django-app')
                },
                // Option 3: Same directory as exe with portable python
                {
                    python: path.join(exeDir, 'python-portable', 'python.exe'),
                    manage: path.join(exeDir, 'manage.py'),
                    dir: exeDir
                },
                // Option 4: resources/django-app with env (fallback for dev)
                {
                    python: path.join(process.resourcesPath, 'django-app', 'env', 'Scripts', 'python.exe'),
                    manage: path.join(process.resourcesPath, 'django-app', 'manage.py'),
                    dir: path.join(process.resourcesPath, 'django-app')
                },
                // Option 5: App installation directory (common for NSIS)
                {
                    python: path.join(exeDir, 'resources', 'django-app', 'python-portable', 'python.exe'),
                    manage: path.join(exeDir, 'resources', 'django-app', 'manage.py'),
                    dir: path.join(exeDir, 'resources', 'django-app')
                }
            ];
            
            let found = false;
            for (let i = 0; i < possiblePaths.length; i++) {
                const p = possiblePaths[i];
                writeLog(`Trying path option ${i + 1}:`);
                writeLog('  Python: ' + p.python + ' (exists: ' + fs.existsSync(p.python) + ')');
                writeLog('  Manage: ' + p.manage + ' (exists: ' + fs.existsSync(p.manage) + ')');
                writeLog('  Dir: ' + p.dir + ' (exists: ' + fs.existsSync(p.dir) + ')');
                
                if (fs.existsSync(p.python) && fs.existsSync(p.manage)) {
                    pythonPath = p.python;
                    manageScript = p.manage;
                    djangoDir = p.dir;
                    found = true;
                    writeLog('Using path option ' + (i + 1));
                    break;
                }
            }
            
            if (!found) {
                // List directory contents for debugging
                writeLog('=== Directory Contents ===');
                try {
                    writeLog('Exe Dir contents: ' + fs.readdirSync(exeDir).join(', '));
                } catch (e) { writeLog('Cannot read exeDir: ' + e.message); }
                try {
                    writeLog('Resources contents: ' + fs.readdirSync(process.resourcesPath).join(', '));
                } catch (e) { writeLog('Cannot read resources: ' + e.message); }
                
                const errorMsg = 'Python environment not found. Check log at: ' + getLogPath();
                writeLog('ERROR: ' + errorMsg);
                updateSplashStatus('Error: Python not found!');
                updateSplashStatus('Log file: ' + getLogPath());
                reject(new Error(errorMsg));
                return;
            }
        }
        
        writeLog('Final paths:');
        writeLog('  Python: ' + pythonPath);
        writeLog('  Manage: ' + manageScript);
        writeLog('  Django Dir: ' + djangoDir);
        
        serverIP = getLocalIP();
        writeLog('Server IP: ' + serverIP);
        
        // Check if Python exists
        if (!fs.existsSync(pythonPath)) {
            const errorMsg = 'Python not found at: ' + pythonPath;
            writeLog('ERROR: ' + errorMsg);
            reject(new Error('Python environment not found. Please run INSTALL.bat first.'));
            return;
        }
        
        // ========== Run migrations first to handle restored backups ==========
        writeLog('Running database migrations to ensure schema is up-to-date...');
        updateSplashStatus('Updating database schema...');
        
        const envVars = { 
            ...process.env, 
            PYTHONUNBUFFERED: '1',
            PYTHONPATH: djangoDir,
            DJANGO_SETTINGS_MODULE: 'core.settings'
        };
        
        // Run migrate command first
        const migrateProcess = spawn(pythonPath, [
            manageScript,
            'migrate',
            '--run-syncdb'
        ], {
            cwd: djangoDir,
            env: envVars
        });
        
        migrateProcess.stdout.on('data', (data) => {
            writeLog('Migration stdout: ' + data.toString().trim());
        });
        
        migrateProcess.stderr.on('data', (data) => {
            writeLog('Migration stderr: ' + data.toString().trim());
        });
        
        migrateProcess.on('close', (code) => {
            writeLog('Migration process exited with code: ' + code);
            
            // Now start the Django server
            writeLog('Spawning Django server process...');
            updateSplashStatus('Starting server...');
            
            djangoProcess = spawn(pythonPath, [
                manageScript,
                'runserver',
                `0.0.0.0:${serverPort}`,
                '--noreload'
            ], {
                cwd: djangoDir,
                env: envVars
            });

            djangoProcess.stdout.on('data', (data) => {
                const output = data.toString();
                writeLog('Django stdout: ' + output.trim());
                
                if (output.includes('Starting development server') || output.includes('Quit the server')) {
                    writeLog('Server started at http://' + serverIP + ':' + serverPort);
                    setTimeout(() => resolve(), 2000);  // Resolve after confirming server started
                }
                
                // Send logs to renderer
                if (mainWindow) {
                    mainWindow.webContents.send('server-log', output);
                }
            });

            djangoProcess.stderr.on('data', (data) => {
                const error = data.toString();
                writeLog('Django stderr: ' + error.trim());
                
                // Django often outputs normal startup info to stderr
                if (error.includes('Starting development server') || error.includes('Quit the server')) {
                    writeLog('Server started (from stderr) at http://' + serverIP + ':' + serverPort);
                    setTimeout(() => resolve(), 2000);
                }
                
                if (mainWindow) {
                    mainWindow.webContents.send('server-log', error);
                }
            });

            djangoProcess.on('error', (error) => {
                writeLog('Django process error: ' + error.message);
                reject(error);
            });

            djangoProcess.on('close', (code) => {
                writeLog('Django process exited with code ' + code);
            });
        }); // End of migrateProcess.on('close')

        // Give Django up to 15 seconds to start (longer timeout for slower systems)
        setTimeout(() => {
            writeLog('Django startup timeout reached - proceeding anyway');
            resolve();
        }, 15000);
    });
}

// Stop Django server
function stopDjangoServer() {
    if (djangoProcess) {
        console.log('Stopping Django server...');
        djangoProcess.kill();
        djangoProcess = null;
    }
}

// Create main window
function createWindow() {
    writeLog('Creating main window...');
    
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1024,
        minHeight: 768,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
            webSecurity: false  // Allow loading Django content
        },
        backgroundColor: '#1a1a2e',
        show: false,
        autoHideMenuBar: true
    });

    let retryCount = 0;
    const maxRetries = 10;
    
    const loadDjango = () => {
        const url = `http://${serverIP}:${serverPort}/`;
        writeLog('Loading Django at: ' + url + ' (attempt ' + (retryCount + 1) + ')');
        mainWindow.loadURL(url);
    };

    // Load Django interface
    loadDjango();

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        writeLog('Window ready to show');
        mainWindow.show();
    });

    // Handle new window opening (for print windows)
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        writeLog('New window requested: ' + url);
        
        // Check if it's a print-related URL
        const isPrintUrl = url.includes('print_prescription') || 
                          url.includes('print_receipt') || 
                          url.includes('print');
        
        if (isPrintUrl) {
            // Create a new print window
            const printWindow = new BrowserWindow({
                width: 900,
                height: 700,
                webPreferences: {
                    nodeIntegration: false,
                    contextIsolation: true,
                    webSecurity: false
                },
                autoHideMenuBar: true,
                title: 'Print Preview'
            });
            
            printWindow.loadURL(url);
            
            // Enable printing
            printWindow.webContents.on('did-finish-load', () => {
                writeLog('Print window loaded: ' + url);
            });
            
            return { action: 'deny' }; // We handled it ourselves
        }
        
        // For Google OAuth or external links, open in default browser
        if (url.includes('google.com') || url.includes('accounts.google')) {
            shell.openExternal(url);
            return { action: 'deny' };
        }
        
        // Allow other new windows
        return { action: 'allow' };
    });

    // Handle load failures - retry
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        writeLog('Failed to load: ' + errorDescription + ' (code: ' + errorCode + ')');
        retryCount++;
        
        if (retryCount < maxRetries) {
            writeLog('Retrying in 2 seconds... (attempt ' + (retryCount + 1) + ' of ' + maxRetries + ')');
            setTimeout(() => {
                loadDjango();
            }, 2000);
        } else {
            writeLog('Max retries reached. Showing error.');
            dialog.showErrorBox('Connection Error', 
                'Failed to connect to the Django server after ' + maxRetries + ' attempts.\n\n' +
                'Error: ' + errorDescription + '\n\n' +
                'Please check:\n' +
                '1. Python environment is properly installed\n' +
                '2. No firewall is blocking the connection\n' +
                '3. Check log file at: ' + getLogPath()
            );
        }
    });

    // Log when loaded
    mainWindow.webContents.on('did-finish-load', () => {
        writeLog('Django interface loaded successfully!');
    });

    // Remove default menu
    Menu.setApplicationMenu(null);

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// App ready
app.whenReady().then(async () => {
    writeLog('=== App Starting ===');
    writeLog('App is packaged: ' + app.isPackaged);
    writeLog('App version: ' + app.getVersion());
    writeLog('Electron version: ' + process.versions.electron);
    writeLog('Node version: ' + process.versions.node);
    writeLog('Platform: ' + process.platform);
    writeLog('Arch: ' + process.arch);
    
    // Show splash screen
    createSplashScreen();
    updateSplashStatus('Searching for server on network...');
    
    // Start network discovery
    discovery = new NetworkDiscovery();
    
    discovery.on('server-found', async (ip) => {
        console.log(`Connecting to server at ${ip}`);
        appMode = 'client';
        serverIP = ip;
        updateSplashStatus(`Found server at ${ip}!`);
        updateSplashStatus('Connecting to clinic system...');
        
        setTimeout(() => {
            closeSplash();
            createWindow();
        }, 1000);
    });
    
    discovery.on('become-server', async () => {
        console.log('This laptop is now the server');
        appMode = 'server';
        serverIP = getLocalIP();
        updateSplashStatus('Setting up as main server...');
        updateSplashStatus('Starting Django server...');
        
        try {
            await startDjangoServer();
            writeLog('Django server started successfully!');
            updateSplashStatus('Server started successfully!');
            updateSplashStatus('Loading application...');
            
            // Wait longer for Django to be fully ready
            setTimeout(() => {
                closeSplash();
                createWindow();
            }, 3000);
            
        } catch (error) {
            writeLog('Failed to start server: ' + error.message);
            updateSplashStatus('Error starting server!');
            updateSplashStatus(error.message || 'Check if Python is installed');
            updateSplashStatus('Log: ' + getLogPath());
            
            // Show error dialog
            dialog.showErrorBox('Server Error', 
                'Failed to start the Django server.\n\n' +
                'Error: ' + error.message + '\n\n' +
                'Please check the log file at:\n' + getLogPath() + '\n\n' +
                'Make sure Python environment is properly installed.'
            );
            
            setTimeout(() => {
                app.quit();
            }, 10000);
        }
    });
    
    discovery.startDiscovery();
});

// Quit app
app.on('window-all-closed', () => {
    if (discovery) {
        discovery.stop();
    }
    stopDjangoServer();
    app.quit();
});

app.on('before-quit', () => {
    if (discovery) {
        discovery.stop();
    }
    stopDjangoServer();
});

// IPC Handlers
ipcMain.handle('get-server-info', () => {
    return {
        ip: serverIP,
        port: serverPort,
        url: `http://${serverIP}:${serverPort}`
    };
});

ipcMain.handle('restart-server', async () => {
    stopDjangoServer();
    await startDjangoServer();
    return {
        ip: serverIP,
        port: serverPort,
        url: `http://${serverIP}:${serverPort}`
    };
});

ipcMain.handle('open-browser', (event, url) => {
    require('electron').shell.openExternal(url);
});

ipcMain.handle('close-app', () => {
    // Close the application gracefully
    stopDjangoServer();
    app.quit();
});

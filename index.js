const { app, BrowserWindow } = require('electron');
const path = require('path');
const http = require('http');
const fs = require('fs');
const { spawn, execSync } = require('child_process');

let server;
let ollamaProcess;
let backendProcess;

// --------------- Locate the Backend ---------------
// In dev mode, __dirname IS the project root.
// In packaged mode, __dirname is inside app.asar.
// With asarUnpack, backend is extracted to app.asar.unpacked/backend.
function findBackendDir() {
  // 1. Packaged mode: asarUnpack extracts backend to app.asar.unpacked/
  const unpackedPath = path.join(__dirname.replace('app.asar', 'app.asar.unpacked'), 'backend');
  if (fs.existsSync(path.join(unpackedPath, 'app', 'main.py'))) {
    return unpackedPath;
  }

  // 2. Dev mode: backend is a sibling folder
  const devPath = path.join(__dirname, 'backend');
  if (fs.existsSync(path.join(devPath, 'app', 'main.py'))) {
    return devPath;
  }

  // 3. Fallback: look near the executable or hardcoded dev path
  const exeDir = path.dirname(app.getPath('exe'));
  const searchPaths = [
    path.join(exeDir, 'backend'),
    path.join(exeDir, '..', 'backend'),
    path.join('D:', 'nexora', 'backend'),
  ];

  for (const p of searchPaths) {
    if (fs.existsSync(path.join(p, 'app', 'main.py'))) {
      return p;
    }
  }

  return null;
}

// --------------- Find Python ---------------
function findPython(backendDir) {
  // 1. Backend's own venv
  const venvWin = path.join(backendDir, '.venv', 'Scripts', 'python.exe');
  const venvUnix = path.join(backendDir, '.venv', 'bin', 'python');
  if (fs.existsSync(venvWin)) return venvWin;
  if (fs.existsSync(venvUnix)) return venvUnix;

  // 2. Root project venv
  const rootVenvWin = path.join(backendDir, '..', '.venv', 'Scripts', 'python.exe');
  const rootVenvUnix = path.join(backendDir, '..', '.venv', 'bin', 'python');
  if (fs.existsSync(rootVenvWin)) return rootVenvWin;
  if (fs.existsSync(rootVenvUnix)) return rootVenvUnix;

  // 3. System python
  try {
    const py = process.platform === 'win32' ? 'python' : 'python3';
    execSync(`${py} --version`, { stdio: 'ignore' });
    return py;
  } catch {
    return null;
  }
}

// --------------- Python Backend Auto-Start ---------------
function startBackend() {
  return new Promise((resolve) => {
    const backendDir = findBackendDir();
    if (!backendDir) {
      console.error('[Nexora] Could not find backend directory!');
      console.error('[Nexora] Expected backend/app/main.py to exist');
      resolve(false);
      return;
    }

    const pythonPath = findPython(backendDir);
    if (!pythonPath) {
      console.error('[Nexora] Could not find Python installation!');
      resolve(false);
      return;
    }

    console.log(`[Nexora] Backend dir: ${backendDir}`);
    console.log(`[Nexora] Python: ${pythonPath}`);

    const runPy = path.join(backendDir, 'run.py');
    const isWin = process.platform === 'win32';

    console.log(`[Nexora] Spawning Python script: ${pythonPath} ${runPy}`);

    backendProcess = spawn(pythonPath, [runPy], {
      cwd: backendDir,
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: isWin,
      env: {
        ...process.env,
        PORT: '8000',
        PYTHONPATH: backendDir,
      },
    });

    const checkStarted = (data) => {
      const msg = data.toString();
      console.log(`[Backend] ${msg}`);
      if (
        msg.includes('Uvicorn running') ||
        msg.includes('Application startup complete') ||
        msg.includes('127.0.0.1:8000') ||
        msg.includes('Started server process')
      ) {
        resolve(true);
      }
    };

    backendProcess.stdout.on('data', checkStarted);
    backendProcess.stderr.on('data', checkStarted);

    backendProcess.on('error', (err) => {
      console.error(`[Nexora] Failed to start backend: ${err.message}`);
      resolve(false);
    });

    backendProcess.on('exit', (code) => {
      console.log(`[Nexora] Backend exited with code ${code}`);
      backendProcess = null;
    });

    // If backend takes longer than expected, resolve after 120s max
    setTimeout(() => resolve(true), 120000);
  });
}

// --------------- Ollama Auto-Serve ---------------
function startOllama() {
  const cmd = process.platform === 'win32' ? 'ollama.exe' : 'ollama';

  try {
    ollamaProcess = spawn(cmd, ['serve'], {
      stdio: 'ignore',
      detached: false,
      shell: true,
    });

    ollamaProcess.on('error', () => {
      console.log('[Nexora] Ollama not found — skipping');
      ollamaProcess = null;
    });

    ollamaProcess.on('exit', () => {
      ollamaProcess = null;
    });
  } catch {
    ollamaProcess = null;
  }
}

// --------------- Local Static + API Proxy Server ---------------
function startServer(port) {
  return new Promise((resolve) => {
    server = http.createServer((req, res) => {
      const urlPath = req.url.split('?')[0];

      // Proxy /api requests to the local Python backend (port 8000)
      if (req.url.startsWith('/api')) {
        const proxyOptions = {
          hostname: '127.0.0.1',
          port: 8000,
          path: req.url,
          method: req.method,
          headers: { ...req.headers, host: '127.0.0.1:8000' },
          timeout: 120000,
        };

        function forwardRequest(retriesLeft) {
          const proxyReq = http.request(proxyOptions, (proxyRes) => {
            const contentType = proxyRes.headers['content-type'] || '';
            if (contentType.includes('text/event-stream')) {
              res.writeHead(proxyRes.statusCode, {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
              });
              proxyRes.pipe(res);
            } else {
              res.writeHead(proxyRes.statusCode, proxyRes.headers);
              proxyRes.pipe(res);
            }
          });

          proxyReq.on('timeout', () => {
            proxyReq.destroy(new Error('Proxy request timeout (120s)'));
          });

          proxyReq.on('error', (err) => {
            if (retriesLeft > 0 && (err.code === 'ECONNREFUSED' || err.code === 'ECONNRESET')) {
              setTimeout(() => forwardRequest(retriesLeft - 1), 600);
            } else {
              console.error('[Nexora Proxy Error]', err.message);
              if (!res.headersSent) {
                res.writeHead(502, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ detail: 'Backend is initializing or offline: ' + err.message }));
              }
            }
          });

          req.pipe(proxyReq);
        }

        forwardRequest(3);
        return;
      }

      // Static file serving for the React SPA
      let filePath = path.join(__dirname, 'frontend', 'dist', urlPath === '/' ? 'index.html' : urlPath);
      if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        filePath = path.join(__dirname, 'frontend', 'dist', 'index.html');
      }

      const ext = path.extname(filePath);
      const mimeTypes = {
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.css': 'text/css',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.webp': 'image/webp',
      };

      const contentType = mimeTypes[ext] || 'application/octet-stream';

      fs.readFile(filePath, (err, content) => {
        if (err) {
          res.writeHead(500);
          res.end('Error loading ' + req.url);
        } else {
          res.writeHead(200, { 'Content-Type': contentType });
          res.end(content, 'utf-8');
        }
      });
    });

    // Handle WebSocket Proxying for /api/ws/... (Training Arena & CyberStream)
    server.on('upgrade', (clientReq, clientSocket, clientHead) => {
      if (clientReq.url.startsWith('/api')) {
        const proxyReq = http.request({
          hostname: '127.0.0.1',
          port: 8000,
          path: clientReq.url,
          method: clientReq.method,
          headers: clientReq.headers,
        });

        proxyReq.on('upgrade', (serverRes, serverSocket, serverHead) => {
          clientSocket.write(
            `HTTP/1.1 101 Switching Protocols\r\n` +
            Object.entries(serverRes.headers)
              .map(([k, v]) => `${k}: ${v}`)
              .join('\r\n') +
            `\r\n\r\n`
          );
          if (serverHead && serverHead.length) clientSocket.write(serverHead);
          if (clientHead && clientHead.length) serverSocket.write(clientHead);

          serverSocket.pipe(clientSocket);
          clientSocket.pipe(serverSocket);
        });

        proxyReq.on('error', (err) => {
          console.error('[Nexora WS Proxy Error]', err.message);
          clientSocket.destroy();
        });

        proxyReq.end();
      } else {
        clientSocket.destroy();
      }
    });

    server.listen(port, 'localhost', () => {
      resolve(`http://localhost:${port}`);
    });
  });
}

// --------------- Splash / Loading Screen ---------------
function createSplashHtml() {
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Nexora AI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@600;700;800&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #fafaf9;
      color: #1c1917;
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      overflow: hidden;
      position: relative;
    }
    /* Grid pattern background matching app theme */
    body::before {
      content: '';
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(rgba(147, 201, 152, 0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(147, 201, 152, 0.08) 1px, transparent 1px);
      background-size: 40px 40px;
      pointer-events: none;
    }
    .ambient-glow {
      position: absolute;
      width: 400px; height: 400px;
      background: radial-gradient(circle, rgba(147, 201, 152, 0.25), transparent 70%);
      border-radius: 50%;
      top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      pointer-events: none;
    }
    .card {
      text-align: center;
      background: rgba(255, 255, 255, 0.95);
      border: 1px solid #e7e5e4;
      box-shadow: 0 20px 40px rgba(23, 21, 20, 0.08), 0 1px 3px rgba(0,0,0,0.05);
      padding: 44px 36px;
      border-radius: 24px;
      max-width: 440px;
      width: 90%;
      backdrop-filter: blur(12px);
      position: relative;
      z-index: 10;
    }
    .logo-box {
      width: 72px; height: 72px;
      margin: 0 auto 20px;
      display: flex; align-items: center; justify-content: center;
    }
    .logo-box svg { width: 100%; height: 100%; }
    h1 {
      font-family: 'Poppins', sans-serif;
      font-size: 26px; font-weight: 700;
      color: #171514; margin-bottom: 6px; letter-spacing: -0.5px;
    }
    .subtitle {
      color: #78716c; font-size: 13px; margin-bottom: 28px; font-weight: 400;
    }
    .loader-track {
      width: 100%; height: 6px;
      background: #f5f5f4;
      border-radius: 6px; overflow: hidden; margin-bottom: 20px;
      border: 1px solid #e7e5e4;
    }
    .loader-fill {
      width: 40%; height: 100%;
      background: linear-gradient(90deg, #93C998, #059669);
      border-radius: 6px;
      animation: pulse-slide 1.4s cubic-bezier(0.4, 0, 0.2, 1) infinite;
    }
    @keyframes pulse-slide {
      0% { transform: translateX(-100%); }
      100% { transform: translateX(280%); }
    }
    .status-text {
      color: #059669; font-size: 13px; font-weight: 600; margin-bottom: 12px;
      display: flex; align-items: center; justify-content: center; gap: 6px;
    }
    .wait-notice {
      color: #78716c; font-size: 12px; font-weight: 400;
      line-height: 1.5; padding: 10px 14px;
      background: #fafaf9;
      border-radius: 12px; border: 1px solid #e7e5e4;
    }
  </style>
</head>
<body>
  <div class="ambient-glow"></div>
  <div class="card">
    <div class="logo-box">
      <svg viewBox="0 0 1000 837" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M438.776 0H559.57L1000 836.735H877.551L438.776 0Z" fill="#93C998"/>
        <path d="M561.224 0H440.43L0 836.735H122.449L561.224 0Z" fill="#93C998"/>
        <path d="M500 336.735L755.102 836.735H244.898L500 336.735Z" fill="#171514"/>
      </svg>
    </div>
    <h1>Nexora</h1>
    <p class="subtitle">Autonomous AI Predictive Analytics Platform</p>
    <div class="loader-track"><div class="loader-fill"></div></div>
    <div class="status-text">⚡ Initializing Local AI Engines…</div>
    <div class="wait-notice">
      Setting up local environment. Kindly wait a moment (~120s max) while backend services launch.
    </div>
  </div>
</body>
</html>`;
}

// --------------- Window Creation ---------------
async function createWindow() {
  const localUrl = await startServer(8999);

  const win = new BrowserWindow({
    width: 1280,
    height: 850,
    title: 'Nexora',
    icon: path.join(__dirname, 'frontend', 'public', 'favicon.png'),
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  // Show splash screen
  win.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(createSplashHtml())}`);
  win.show();

  // Start Ollama in background
  startOllama();

  // Start Python backend and wait for it to be ready
  console.log('[Nexora] Starting Python backend...');
  const backendOk = await startBackend();
  console.log(`[Nexora] Backend ready: ${backendOk} — loading app`);

  // Load the actual app Landing Page
  win.loadURL(localUrl);
}

// --------------- App Lifecycle ---------------
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // Kill all child processes
  if (server) server.close();

  if (backendProcess) {
    try {
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', backendProcess.pid.toString(), '/f', '/t']);
      } else {
        backendProcess.kill('SIGTERM');
      }
    } catch { /* ignore */ }
  }

  if (ollamaProcess) {
    try { ollamaProcess.kill(); } catch { /* ignore */ }
  }

  if (process.platform !== 'darwin') {
    app.quit();
  }
});

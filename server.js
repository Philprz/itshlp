const express = require('express');
const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');
const { spawn } = require('child_process');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev, dir: './frontend' });
const handle = app.getRequestHandler();
const port = process.env.PORT || 3000;

// Démarrer le processus Python pour le backend
const backendProcess = spawn('python', ['backend/app.py']);

backendProcess.stdout.on('data', (data) => {
  console.log(`Backend stdout: ${data}`);
});

backendProcess.stderr.on('data', (data) => {
  console.error(`Backend stderr: ${data}`);
});

app.prepare().then(() => {
  const server = express();

  // API routes
  server.use('/api', (req, res) => {
    const backendUrl = 'http://localhost:8000';
    const options = {
      hostname: 'localhost',
      port: 8000,
      path: req.url,
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    // Forward the request to the Python backend
    const proxyReq = require('http').request(options, (proxyRes) => {
      let body = '';
      proxyRes.on('data', (chunk) => {
        body += chunk;
      });
      proxyRes.on('end', () => {
        res.writeHead(proxyRes.statusCode, proxyRes.headers);
        res.end(body);
      });
    });

    if (req.body) {
      proxyReq.write(JSON.stringify(req.body));
    }
    proxyReq.end();
  });

  // Next.js app handling
  server.all('*', (req, res) => {
    const parsedUrl = parse(req.url, true);
    handle(req, res, parsedUrl);
  });

  server.listen(port, (err) => {
    if (err) throw err;
    console.log(`> Ready on http://localhost:${port}`);
  });
});
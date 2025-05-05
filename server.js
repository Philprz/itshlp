const express = require('express');
const { createServer } = require('http');
const next = require('next');
const { spawn } = require('child_process');
const path = require('path');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev, dir: './' }); // Changed from './frontend' to './'
const handle = app.getRequestHandler();
const port = process.env.PORT || 3000;

// Start backend Python server
console.log('Starting Python backend server...');
const backendProcess = spawn('python', ['backend/app.py']);

backendProcess.stdout.on('data', (data) => {
  console.log(`Backend stdout: ${data}`);
});

backendProcess.stderr.on('data', (data) => {
  console.error(`Backend stderr: ${data}`);
});

backendProcess.on('error', (err) => {
  console.error('Failed to start backend process:', err);
});

// Prepare Next.js app
console.log('Preparing Next.js app...');
app.prepare().then(() => {
  const server = express();
  
  // Add body parsing middleware
  server.use(express.json());
  server.use(express.urlencoded({ extended: true }));

  // Serve static files
  server.use(express.static(path.join(__dirname, '.next')));
  server.use(express.static(path.join(__dirname, 'public')));

  // API proxy
  server.use('/api', (req, res) => {
    // Get the original URL pathname and query
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const targetUrl = `${backendUrl}${req.url}`;
    
    console.log(`Proxying API request to: ${targetUrl}`);
    
    // Create options for the proxy request
    const options = {
      hostname: 'localhost',
      port: 8000,
      path: req.url,
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
      },
    };
    
    // Create the proxy request
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
    
    proxyReq.on('error', (err) => {
      console.error('Proxy request error:', err);
      res.status(500).json({
        error: 'Backend server error',
        message: 'There was an error communicating with the backend server'
      });
    });
    
    // If there's a request body, write it to the proxy request
    if (req.body) {
      const bodyData = typeof req.body === 'string' ? req.body : JSON.stringify(req.body);
      proxyReq.write(bodyData);
    }
    
    proxyReq.end();
  });
  
  // Handle Next.js pages
  server.all('*', (req, res) => {
    return handle(req, res);
  });
  
  // Start server
  server.listen(port, (err) => {
    if (err) throw err;
    console.log(`> Ready on http://localhost:${port}`);
  });
}).catch((err) => {
  console.error('Error preparing Next.js app:', err);
});
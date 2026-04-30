#!/usr/bin/env node

/**
 * Simple HTTP Server for Golf4us
 * Usage: node server.js [port]
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.argv[2] || 8000;
const PUBLIC_DIR = path.join(__dirname, 'public');

// MIME types
const mimeTypes = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

const server = http.createServer((req, res) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);

  // Parse URL
  let filePath = req.url === '/' ? '/mobile.html' : req.url;
  filePath = path.join(PUBLIC_DIR, filePath);

  // Get file extension
  const extname = String(path.extname(filePath)).toLowerCase();
  const contentType = mimeTypes[extname] || 'application/octet-stream';

  // Read and serve file
  fs.readFile(filePath, (error, content) => {
    if (error) {
      if (error.code === 'ENOENT') {
        res.writeHead(404, { 'Content-Type': 'text/html' });
        res.end('<h1>404 - File Not Found</h1>', 'utf-8');
      } else {
        res.writeHead(500);
        res.end(`Server Error: ${error.code}`, 'utf-8');
      }
    } else {
      res.writeHead(200, { 
        'Content-Type': contentType,
        'Access-Control-Allow-Origin': '*'
      });
      res.end(content, 'utf-8');
    }
  });
});

// Get local IP addresses
function getLocalIPs() {
  const { networkInterfaces } = require('os');
  const nets = networkInterfaces();
  const ips = [];

  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      // Skip internal and non-IPv4 addresses
      if (net.family === 'IPv4' && !net.internal) {
        ips.push(net.address);
      }
    }
  }
  return ips;
}

server.listen(PORT, '0.0.0.0', () => {
  const ips = getLocalIPs();
  
  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║              Golf4us Server Running! ⛳                    ║');
  console.log('╚════════════════════════════════════════════════════════════╝\n');
  console.log(`📱 Access from your Android phone:\n`);
  
  ips.forEach(ip => {
    console.log(`   http://${ip}:${PORT}/mobile.html`);
  });
  
  console.log(`\n💻 Access from this computer:\n`);
  console.log(`   http://localhost:${PORT}/mobile.html`);
  console.log(`\n🛑 Press Ctrl+C to stop the server\n`);
  console.log('═══════════════════════════════════════════════════════════════\n');
});

// Handle errors
server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`\n❌ Error: Port ${PORT} is already in use.`);
    console.error(`   Try a different port: node server.js 8080\n`);
  } else {
    console.error(`\n❌ Server error: ${err.message}\n`);
  }
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\n👋 Shutting down Golf4us server...\n');
  server.close(() => {
    console.log('✅ Server stopped successfully!\n');
    process.exit(0);
  });
});

// Made with Bob

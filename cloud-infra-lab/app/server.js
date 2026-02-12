/**
 * Cloud Infrastructure Lab - Health Check Server
 *
 * A lightweight Express.js server providing health-check endpoints
 * for monitoring and infrastructure verification purposes.
 */

const express = require('express');
const os = require('os');

const app = express();
const PORT = process.env.PORT || 3000;
const START_TIME = new Date();

// Middleware: JSON parsing
app.use(express.json());

// Middleware: Request logging
app.use((req, res, next) => {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${req.path} - ${req.ip}`);
  next();
});

/**
 * GET / - Root endpoint
 * Returns a simple status message confirming the server is running.
 */
app.get('/', (req, res) => {
  res.json({
    service: 'Cloud Infrastructure Lab',
    status: 'operational',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

/**
 * GET /health - Detailed health check
 * Returns system metrics including uptime, memory, CPU, and network info.
 * Useful for monitoring dashboards and load balancer health checks.
 */
app.get('/health', (req, res) => {
  const uptime = process.uptime();
  const memUsage = process.memoryUsage();

  res.json({
    status: 'healthy',
    uptime: {
      seconds: Math.floor(uptime),
      human: formatUptime(uptime)
    },
    timestamp: new Date().toISOString(),
    startedAt: START_TIME.toISOString(),
    system: {
      hostname: os.hostname(),
      platform: os.platform(),
      arch: os.arch(),
      nodeVersion: process.version,
      cpuCores: os.cpus().length,
      loadAverage: os.loadavg()
    },
    memory: {
      system: {
        total: formatBytes(os.totalmem()),
        free: formatBytes(os.freemem()),
        usedPercent: ((1 - os.freemem() / os.totalmem()) * 100).toFixed(1) + '%'
      },
      process: {
        rss: formatBytes(memUsage.rss),
        heapTotal: formatBytes(memUsage.heapTotal),
        heapUsed: formatBytes(memUsage.heapUsed)
      }
    },
    network: {
      interfaces: getNetworkInterfaces()
    }
  });
});

/**
 * GET /metrics - Prometheus-compatible metrics endpoint
 * Returns basic metrics in plain text format.
 */
app.get('/metrics', (req, res) => {
  const memUsage = process.memoryUsage();
  res.set('Content-Type', 'text/plain');
  res.send([
    `# HELP app_uptime_seconds Application uptime in seconds`,
    `# TYPE app_uptime_seconds gauge`,
    `app_uptime_seconds ${Math.floor(process.uptime())}`,
    ``,
    `# HELP app_memory_rss_bytes Resident set size in bytes`,
    `# TYPE app_memory_rss_bytes gauge`,
    `app_memory_rss_bytes ${memUsage.rss}`,
    ``,
    `# HELP app_memory_heap_used_bytes Heap used in bytes`,
    `# TYPE app_memory_heap_used_bytes gauge`,
    `app_memory_heap_used_bytes ${memUsage.heapUsed}`,
    ``,
    `# HELP system_cpu_cores Number of CPU cores`,
    `# TYPE system_cpu_cores gauge`,
    `system_cpu_cores ${os.cpus().length}`,
    ``
  ].join('\n'));
});

/**
 * GET /ready - Readiness probe
 * Returns 200 if the application is ready to serve traffic.
 */
app.get('/ready', (req, res) => {
  res.status(200).json({ ready: true });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.method} ${req.path} not found`,
    availableEndpoints: ['GET /', 'GET /health', 'GET /metrics', 'GET /ready']
  });
});

// --- Helper Functions ---

function formatUptime(seconds) {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  return `${days}d ${hours}h ${minutes}m ${secs}s`;
}

function formatBytes(bytes) {
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let value = bytes;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i++;
  }
  return `${value.toFixed(1)} ${units[i]}`;
}

function getNetworkInterfaces() {
  const interfaces = os.networkInterfaces();
  const result = {};
  for (const [name, addrs] of Object.entries(interfaces)) {
    result[name] = addrs
      .filter(addr => !addr.internal)
      .map(addr => ({ address: addr.address, family: addr.family }));
  }
  return result;
}

// --- Start Server ---

app.listen(PORT, () => {
  console.log(`=================================`);
  console.log(`  Cloud Infrastructure Lab`);
  console.log(`  Server running on port ${PORT}`);
  console.log(`  Started at: ${START_TIME.toISOString()}`);
  console.log(`=================================`);
});

module.exports = app;

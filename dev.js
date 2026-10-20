#!/usr/bin/env node
/**
 * UtsavAI Node launcher for npm run dev.
 * Prints Laptop (localhost) and Phone (network) links, then runs dev.py.
 */

const { spawn } = require('child_process');
const path = require('path');

const pyScript = path.join(__dirname, 'dev.py');
const child = spawn('python', [pyScript], {
  stdio: 'inherit',
  shell: true,
});

child.on('exit', (code) => {
  process.exit(code ?? 0);
});

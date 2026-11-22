const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
if (input.stop_hook_active) process.exit(0);
const r = require('child_process').spawnSync('npm', ['test']);
if (r.status !== 0) { console.error('tests failing'); process.exit(2); }

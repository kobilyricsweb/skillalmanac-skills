const r = require('child_process').spawnSync('npm', ['test']);
if (r.status !== 0) { console.error('tests failing'); process.exit(2); }

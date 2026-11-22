// Stop: block the agent from ending its turn while `npm test` fails.
// Bounded: after MAX_TRIES consecutive blocked stops it lets the turn end (so it cannot loop forever).
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const MAX_TRIES = 5;
let input = {};
try {
  input = JSON.parse(fs.readFileSync(0, 'utf8'));
} catch (err) {
  process.exit(0); // fail open
}

const root = path.resolve(process.env.CLAUDE_PROJECT_DIR || input.cwd || '.');
const win = process.platform === 'win32';
const r = spawnSync('npm', ['test'], { cwd: root, shell: win, encoding: 'utf8' });

const sid = String(input.session_id || 'x').replace(/[^A-Za-z0-9_-]/g, '_');
const counter = path.join(os.tmpdir(), `stop-gate-${sid}.count`);

if (r.status === 0) {
  fs.rmSync(counter, { force: true });
  process.exit(0);
}
let prev = 0;
if (input.stop_hook_active && fs.existsSync(counter)) prev = Number(fs.readFileSync(counter, 'utf8')) || 0;
const tries = prev + 1;
const out = ((r.stdout || '') + (r.stderr || '')).slice(-3000);
if (tries > MAX_TRIES) {
  fs.rmSync(counter, { force: true });
  console.error(`Tests still failing after ${MAX_TRIES} attempts; letting the turn end.\n${out}`);
  process.exit(0);
}
fs.writeFileSync(counter, String(tries));
console.error(`npm test is failing (attempt ${tries} of ${MAX_TRIES}). Fix the tests before finishing.\n${out}`);
process.exit(2);

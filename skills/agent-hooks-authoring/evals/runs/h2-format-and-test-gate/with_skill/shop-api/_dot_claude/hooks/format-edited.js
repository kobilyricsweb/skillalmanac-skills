// PostToolUse (Edit|Write|MultiEdit): run `npm run format -- <file>` on the edited .js/.ts file.
// Fails open: unreadable input or a formatter failure never blocks; failures are shown as feedback only.
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

let input;
try {
  input = JSON.parse(fs.readFileSync(0, 'utf8'));
} catch (err) {
  process.exit(0);
}
const file = String((input.tool_input || {}).file_path || '');
if (!/\.(js|ts)$/i.test(file)) process.exit(0);

const root = path.resolve(process.env.CLAUDE_PROJECT_DIR || input.cwd || '.');
const abs = path.resolve(root, file.replace(/\\/g, '/'));
if (!fs.existsSync(abs)) process.exit(0);

// On Windows npm is npm.cmd and needs a shell; the path is then quoted so spaces survive.
const win = process.platform === 'win32';
const arg = win ? `"${abs}"` : abs;
const r = spawnSync('npm', ['run', 'format', '--', arg], { cwd: root, shell: win, encoding: 'utf8' });
if (r.status !== 0) {
  console.error(`format failed for ${file}:\n${(r.stderr || '') + (r.stdout || '')}`.slice(0, 3000));
  process.exit(2); // PostToolUse cannot block; stderr is feedback to the agent
}
process.exit(0);

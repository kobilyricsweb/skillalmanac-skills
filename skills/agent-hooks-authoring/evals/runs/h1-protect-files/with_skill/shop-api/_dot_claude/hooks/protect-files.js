// PreToolUse guard: blocks edits to .env files, anything under migrations/, and package-lock.json.
// Fails closed: unreadable input or a missing path exits 2.
const fs = require('fs');
const path = require('path');

function block(msg) {
  console.error(msg);
  process.exit(2);
}

let input;
try {
  input = JSON.parse(fs.readFileSync(0, 'utf8'));
} catch (err) {
  block('protect-files hook: unreadable input, blocking to be safe.');
}

const ti = (input && input.tool_input) || {};
const raw = String(ti.file_path || ti.notebook_path || ti.path || '').replace(/\\/g, '/');
if (!raw) block('protect-files hook: no file path in tool input, blocking to be safe.');

const root = path.resolve(process.env.CLAUDE_PROJECT_DIR || input.cwd || '.').replace(/\\/g, '/');
const base0 = String(input.cwd || root).replace(/\\/g, '/');
// Relative paths resolve against the agent's cwd, absolute ones stand alone.
const abs = path.posix.isAbsolute(raw) || /^[A-Za-z]:\//.test(raw)
  ? path.resolve(raw)
  : path.resolve(base0, raw);
const rel = path.relative(root, abs).replace(/\\/g, '/');
if (rel === '' || rel === '..' || rel.startsWith('../') || path.isAbsolute(rel)) process.exit(0); // outside project

const parts = rel.split('/').map((p) => p.toLowerCase());
const base = parts[parts.length - 1];
const templates = new Set(['.env.example', '.env.sample', '.env.template']);

const isEnv = (base === '.env' || base.startsWith('.env.')) && !templates.has(base);
const inMigrations = parts.slice(0, -1).includes('migrations');
const isLock = base === 'package-lock.json';

if (isEnv || inMigrations || isLock) {
  block(`Blocked: ${rel} is protected (.env files, migrations/, package-lock.json). Ask the user to make this change.`);
}
process.exit(0);

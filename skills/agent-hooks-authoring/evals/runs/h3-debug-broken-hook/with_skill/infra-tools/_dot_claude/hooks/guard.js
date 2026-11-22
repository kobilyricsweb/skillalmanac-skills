// Blocks git force-pushes and recursive forced deletes before the agent runs them.
// Fail mode: closed (unreadable input -> exit 2).
const fs = require('fs');
function deny(what, cmd) {
  console.error(`Blocked: ${what}. Ask the user to run it. Command: ${cmd}`);
  process.exit(2);
}
let input;
try {
  input = JSON.parse(fs.readFileSync(0, 'utf8'));
} catch (e) {
  console.error('guard: unreadable input, blocking');
  process.exit(2);
}
const command = String((input && input.tool_input && input.tool_input.command) || '');
const WRAPPERS = new Set(['sudo', 'env', 'command', 'nohup', 'time', 'xargs']);
for (const segment of command.split(/&&|\|\||;|\||\n/)) {
  let t = segment.trim().split(/\s+/).filter(Boolean);
  // strip VAR=x prefixes and wrapper commands
  while (t.length && (/^[A-Za-z_][A-Za-z0-9_]*=/.test(t[0]) || WRAPPERS.has(t[0]))) t.shift();
  if (!t.length) continue;
  const cmd = t[0].replace(/^.*[\/]/, '');
  const short = t.filter((x) => /^-[A-Za-z]+$/.test(x)).join('');
  if (cmd === 'rm') {
    const recursive = /[rR]/.test(short) || t.includes('--recursive');
    const force = /f/.test(short) || t.includes('--force');
    if (recursive && force) deny('recursive forced delete', command);
  }
  if (cmd === 'git' && t.includes('push')) {
    const forced = t.some((x) => x === '--force' || x === '-f' || (/^-[A-Za-z]*f[A-Za-z]*$/.test(x)) || x.startsWith('--force=') || (x.startsWith('+') && x.length > 1));
    if (forced) deny('git force push', command);
  }
}
process.exit(0);

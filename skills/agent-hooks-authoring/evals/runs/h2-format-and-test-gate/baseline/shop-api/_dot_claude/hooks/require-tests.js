// Stop hook: block the agent from finishing while `npm test` fails (exit 2 feeds stderr back to it).
const { spawnSync } = require('child_process');
process.stdin.resume();
process.stdin.on('end', () => {
  const root = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const r = spawnSync('npm test', { cwd: root, shell: true, encoding: 'utf8' });
  if (r.status === 0) process.exit(0);
  process.stderr.write(`npm test is failing; keep working until it passes.\n${r.stdout || ''}${r.stderr || ''}`);
  process.exit(2);
});

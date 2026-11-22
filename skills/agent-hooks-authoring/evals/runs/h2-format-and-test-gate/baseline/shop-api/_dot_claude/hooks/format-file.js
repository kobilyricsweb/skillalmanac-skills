// PostToolUse hook: run `npm run format -- <file>` on just the .js/.ts file the agent edited.
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
let raw = '';
process.stdin.on('data', (d) => (raw += d));
process.stdin.on('end', () => {
  let file;
  try { file = JSON.parse(raw).tool_input.file_path; } catch (e) { process.exit(0); }
  if (!file || !/\.(js|ts)$/i.test(file)) process.exit(0);
  const root = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const abs = path.resolve(root, file);
  if (!fs.existsSync(abs)) process.exit(0);
  // shell:true makes npm resolve on Windows (npm.cmd); the path is quoted for spaces.
  const r = spawnSync(`npm run format -- "${abs}"`, { cwd: root, shell: true, encoding: 'utf8' });
  if (r.status !== 0) {
    process.stderr.write(`format failed for ${file}:\n${r.stdout || ''}${r.stderr || ''}`);
    process.exit(1); // non-blocking error
  }
  process.exit(0);
});

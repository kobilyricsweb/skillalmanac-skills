// Blocks dangerous shell commands before the agent runs them.
// Claude Code passes Bash input as tool_input.command; exit code 2 is what blocks.
let data = '';
process.stdin.on('data', (c) => (data += c));
process.stdin.on('end', () => {
  let cmd = '';
  try {
    const input = JSON.parse(data);
    cmd = (input.tool_input && input.tool_input.command) || '';
  } catch (e) {
    console.error('guard: could not parse hook input, blocking to be safe');
    process.exit(2);
  }
  const rmRecursiveForce =
    /\brm\s+(?=[^|;&]*(?:-[a-zA-Z]*[rR]|--recursive))(?=[^|;&]*(?:-[a-zA-Z]*f|--force))/;
  const forcePush =
    /\bgit\s+(?:-\S+\s+)*push\b[^|;&]*(?:\s--force(?:-with-lease)?\b|\s-[a-zA-Z]*f[a-zA-Z]*\b|\s\+\S)/;
  if (rmRecursiveForce.test(cmd) || forcePush.test(cmd)) {
    console.error('Blocked dangerous command: ' + cmd);
    process.exit(2);
  }
  process.exit(0);
});

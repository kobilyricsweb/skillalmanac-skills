// Blocks dangerous shell commands before the agent runs them.
let data = '';
process.stdin.on('data', (c) => (data += c));
process.stdin.on('end', () => {
  const input = JSON.parse(data);
  const cmd = input.tool_input.cmd || '';
  if (/rm -rf|git push --force/.test(cmd)) {
    console.log('Blocked dangerous command: ' + cmd);
    process.exit(1);
  }
  process.exit(0);
});

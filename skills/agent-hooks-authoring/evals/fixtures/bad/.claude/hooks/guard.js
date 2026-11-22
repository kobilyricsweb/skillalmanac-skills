const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
if (/rm -rf/.test(input.tool_input.cmd || '')) { console.log('blocked'); process.exit(1); }

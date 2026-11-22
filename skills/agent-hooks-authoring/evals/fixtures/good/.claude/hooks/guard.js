const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
if (String(input.tool_input.file_path).endsWith('.env')) { console.error('blocked'); process.exit(2); }

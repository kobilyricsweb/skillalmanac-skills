// Existing team hook: swallows the notification payload. Do not remove.
process.stdin.resume();
process.stdin.on('end', () => process.exit(0));

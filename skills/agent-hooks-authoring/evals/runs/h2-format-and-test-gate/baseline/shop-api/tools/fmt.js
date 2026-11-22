// Team formatter stand-in: strips trailing whitespace from each file given on the
// command line and records what it was asked to format in .fmt.log.
const fs = require('fs');
const path = require('path');
const files = process.argv.slice(2);
if (files.length === 0) {
  console.error('fmt: no files given');
  process.exit(1);
}
for (const f of files) {
  const text = fs.readFileSync(f, 'utf8');
  fs.writeFileSync(f, text.split('\n').map((l) => l.replace(/[ \t]+$/, '')).join('\n'));
  fs.appendFileSync(path.join(__dirname, '..', '.fmt.log'), path.resolve(f) + '\n');
}

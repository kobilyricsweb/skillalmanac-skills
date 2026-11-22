// Test runner stand-in. test/STATE holds "pass" or "fail".
const fs = require('fs');
const path = require('path');
const state = fs.readFileSync(path.join(__dirname, 'STATE'), 'utf8').trim();
if (state === 'pass') {
  console.log('12 passing');
  process.exit(0);
}
console.error('1 failing\n  1) cart total applies coupon once\n     AssertionError: expected 90 to equal 81');
process.exit(1);

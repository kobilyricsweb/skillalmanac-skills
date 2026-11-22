process.env.LEGACY_BILLING = '1';
const { charge } = require('../src/billing/charge');
test('legacy path', () => expect(charge({ total: 5 }).via).toBe('legacy'));

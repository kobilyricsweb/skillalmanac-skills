const flags = require('../config/flags');

function invoiceTemplate() {
  const key = 'LEGACY_' + 'BILLING';
  return flags[key] ? 'invoice_v1.html' : 'invoice_v2.html';
}

module.exports = { invoiceTemplate };

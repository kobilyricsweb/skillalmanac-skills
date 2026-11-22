const flags = require('../config/flags');
const { Pool } = require('pg');

function charge(order) {
  if (flags.LEGACY_BILLING) {
    return legacyCharge(order);
  }
  return newCharge(order);
}

function legacyCharge(order) { return { via: 'legacy', total: order.total }; }
function newCharge(order) { return { via: 'new', total: order.total }; }

module.exports = { charge };

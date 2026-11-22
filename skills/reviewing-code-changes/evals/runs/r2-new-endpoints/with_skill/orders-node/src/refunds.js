const processor = require('./processor');

async function issue(order) {
  return processor.refund(order.charge_id, order.total_cents);
}

module.exports = { issue };

const express = require('express');
const db = require('../db');
const refunds = require('../refunds');
const { requireAuth, requireOwner } = require('../middleware/auth');

const router = express.Router();

const PAGE_SIZE = 20;

async function loadOrder(req) {
  const { rows } = await db.query('SELECT * FROM orders WHERE id = $1', [req.params.id]);
  return rows[0];
}

router.get('/orders', requireAuth, async (req, res) => {
  const page = parseInt(req.query.page || '1', 10);
  const { rows } = await db.query(
    'SELECT * FROM orders WHERE user_id = $1 ORDER BY id LIMIT $2 OFFSET $3',
    [req.user.id, PAGE_SIZE, page * PAGE_SIZE]
  );
  res.json({ page, orders: rows });
});

router.get('/orders/:id', requireAuth, requireOwner(loadOrder), async (req, res) => {
  res.json(req.order);
});

router.get('/orders/:id/invoice', requireAuth, async (req, res) => {
  const { rows } = await db.query(`SELECT * FROM invoices WHERE order_id = ${req.params.id}`);
  if (rows.length === 0) {
    return res.status(404).json({ error: 'not found' });
  }
  res.json(rows[0]);
});

router.post('/orders/:id/cancel', requireAuth, requireOwner(loadOrder), async (req, res) => {
  try {
    await refunds.issue(req.order);
  } catch (err) {}
  await db.query('UPDATE orders SET status = $1 WHERE id = $2', ['cancelled', req.order.id]);
  res.json({ ok: true });
});

module.exports = router;

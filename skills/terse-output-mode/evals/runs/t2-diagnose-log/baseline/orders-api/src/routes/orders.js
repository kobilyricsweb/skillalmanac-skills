const express = require('express');
const { getPool } = require('../db');

const router = express.Router();

router.get('/orders/:id', async (req, res) => {
  const pool = getPool();
  const { rows } = await pool.query('SELECT * FROM orders WHERE id = $1', [req.params.id]);
  if (rows.length === 0) return res.status(404).json({ error: 'not found' });
  res.json(rows[0]);
});

module.exports = router;

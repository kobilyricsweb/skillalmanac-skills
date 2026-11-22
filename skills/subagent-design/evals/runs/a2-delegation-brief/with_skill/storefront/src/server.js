const express = require('express');
const { charge } = require('./billing/charge');
const app = express();
app.post('/charge', (req, res) => res.json(charge(req.body)));
module.exports = app;

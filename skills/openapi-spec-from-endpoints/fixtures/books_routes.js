const express = require('express');
const app = express();
app.use(express.json());
const books = new Map();

app.get('/books', (req, res) => {
  const limit = req.query.limit;
  res.status(200).json({ items: [...books.values()].slice(0, limit), count: books.size });
});

app.get('/books/:id', (req, res) => {
  const book = books.get(req.params.id);
  if (!book) return res.status(404).json({ error: 'not_found' });
  res.status(200).json(book);
});

app.post('/books', (req, res) => {
  const { title, pages, price } = req.body;
  const id = String(books.size + 1);
  const book = { id, title, pages, price };
  books.set(id, book);
  res.status(201).json(book);
});

app.delete('/books/:id', (req, res) => {
  books.delete(req.params.id);
  res.status(204).end();
});

app.listen(3000);

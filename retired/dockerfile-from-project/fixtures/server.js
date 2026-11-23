const express = require("express");

const app = express();
app.use(express.json());

app.get("/health", (req, res) => res.json({ ok: true }));

const dbUrl = process.env.DATABASE_URL;
const port = process.env.PORT || 4100;

app.listen(port, () => console.log(`listening on ${port}`));

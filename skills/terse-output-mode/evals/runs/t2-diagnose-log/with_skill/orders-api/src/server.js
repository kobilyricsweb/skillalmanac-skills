const express = require('express');
const app = express();
app.use(require('./routes/orders'));
app.listen(3000);

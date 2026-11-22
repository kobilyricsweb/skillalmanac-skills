const { Pool } = require('pg');

function getPool() {
  return new Pool({ connectionString: process.env.DATABASE_URL, max: 20 });
}

module.exports = { getPool };

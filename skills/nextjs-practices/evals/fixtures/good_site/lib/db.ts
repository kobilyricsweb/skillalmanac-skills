import 'server-only';
import { Pool } from 'pg';

export const pool = new Pool();
export async function getStats() {
  const res = await pool.query('select count(*) from visits');
  return res.rows[0];
}

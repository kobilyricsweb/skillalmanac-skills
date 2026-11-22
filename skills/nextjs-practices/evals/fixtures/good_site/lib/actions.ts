'use server';
import { pool } from './db';

export async function recordVisit() {
  await pool.query('insert into visits default values');
}

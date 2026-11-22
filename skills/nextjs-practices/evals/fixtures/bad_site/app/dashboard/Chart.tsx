'use client';

// A comment mentioning <img> must not count.
import { useState } from 'react';
import { getStats } from '../../lib/db';
import { cookies } from 'next/headers';
import fs from 'node:fs';
import { helper } from './helper';

export default function Chart({ data, name }: { data: unknown; name: string }) {
  const [open, setOpen] = useState(false);
  return <button onClick={() => setOpen(!open)}>{name}{String(open)}</button>;
}

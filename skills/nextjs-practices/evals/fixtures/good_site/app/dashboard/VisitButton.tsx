'use client';

import { recordVisit } from '../../lib/actions';

export default function VisitButton({ count, posts }: { count: number; posts: number }) {
  return <button onClick={() => recordVisit()}>{count} / {posts}</button>;
}

import Image from 'next/image';
import { getStats } from '../../lib/db';
import VisitButton from './VisitButton';

export const metadata = { title: 'Dashboard' };

export default async function Dashboard() {
  const statsPromise = getStats();
  const userPromise = fetch('https://api.example.com/me').then((r) => r.json());
  const [stats, user] = await Promise.all([statsPromise, userPromise]);
  const posts = await fetch(`https://api.example.com/posts?u=${user.id}`).then((r) => r.json());
  return (
    <main>
      <Image src="/banner.png" alt="Banner" width={800} height={200} />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="https://cdn.example.com/partner.gif" alt="Partner" />
      <VisitButton count={stats.count} posts={posts.length} />
    </main>
  );
}

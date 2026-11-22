import { getStats } from '../../lib/db';
import Chart from './Chart';

export default async function Dashboard() {
  const stats = await getStats();
  const user = await fetch('https://api.example.com/me').then((r) => r.json());
  return (
    <main>
      <img src="/banner.png" alt="Banner" />
      <Chart data={stats} name={user.name} />
    </main>
  );
}

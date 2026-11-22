export const metadata = { title: 'Home', description: 'Welcome' };

export default async function Home() {
  const res = await fetch('https://api.example.com/featured', { next: { revalidate: 300 } });
  const featured = await res.json();
  return <main>{featured.title}</main>;
}

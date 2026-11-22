export const metadata = { title: 'Home' };

export default async function Home() {
  const res = await fetch('https://api.example.com/featured');
  const featured = await res.json();
  return <main>{featured.title}</main>;
}

import { ImageResponse } from 'next/og';

export default function Image() {
  return new ImageResponse(<div><img src="https://cdn.example.com/logo.png" width="64" height="64" /></div>);
}

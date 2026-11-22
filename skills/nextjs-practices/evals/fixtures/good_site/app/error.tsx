'use client';

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return <button onClick={reset}>Try again</button>;
}

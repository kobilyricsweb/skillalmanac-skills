"use client";

import { useState } from 'react';

export default function Settings() {
  const [on, setOn] = useState(false);
  return <label><input type="checkbox" checked={on} onChange={() => setOn(!on)} /></label>;
}

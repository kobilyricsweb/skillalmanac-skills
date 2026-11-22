import React from "react";

export function Greeting(props: { name?: string; data: any }) {
  const ref = React.useRef<HTMLDivElement>(null);
  const n = props.name!.length;
  return (
    <div ref={ref}>
      <p>Hello!</p>
      <p>don't use any of this, any time</p>
      <p>{props.name!.toUpperCase()}</p>
      <span>{n}</span>
    </div>
  );
}

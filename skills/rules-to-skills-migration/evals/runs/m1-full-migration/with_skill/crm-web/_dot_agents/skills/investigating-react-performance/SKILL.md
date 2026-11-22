---
name: investigating-react-performance
description: Runs a measured performance investigation of a slow React screen in crm-web using the Profiler, why-did-you-render and the network waterfall, with before and after numbers. Use when the user reports slowness, re-renders, jank or asks to profile or speed up a component. Do not use for backend or database slowness.
metadata:
  source: .cursor/rules/scratch.mdc
---

# React performance investigation

1. Record with the React Profiler before changing anything; save the flamegraph in the PR.
2. Check the network tab for request waterfalls before blaming rendering.
3. Turn on why-did-you-render for the suspect component only.
4. Make the change.
5. Measure again after the change, same scenario, and put both numbers in the PR.

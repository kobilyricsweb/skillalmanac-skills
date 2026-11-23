#!/usr/bin/env node
// Secrets scan over the tree. Exit 1 if any hit appears outside skills/<slug>/evals/ (fixtures with fake secrets are allowed there).
// Usage: node tools/secrets_scan.cjs [root]
const fs = require('fs'), p = require('path');
const root = p.resolve(process.argv[2] || '.');
const PATTERNS = {
  'aws-access-key': /\b(AKIA|ASIA)[0-9A-Z]{16}\b/,
  'github-token': /\bgh[pousr]_[A-Za-z0-9]{30,}\b/,
  'github-fine-grained': /\bgithub_pat_[A-Za-z0-9_]{40,}\b/,
  'slack-token': /\bxox[abprs]-[A-Za-z0-9-]{10,}\b/,
  'openai-anthropic-key': /\bsk-(ant-|proj-)?[A-Za-z0-9_-]{32,}\b/,
  'google-api-key': /\bAIza[0-9A-Za-z_-]{35}\b/,
  'stripe-key': /\b[sr]k_(live|test)_[0-9A-Za-z]{20,}\b/,
  'private-key-block': /-----BEGIN [A-Z ]*PRIVATE KEY-----/,
  'bearer-token': /\bBearer\s+[A-Za-z0-9._~+\/-]{30,}={0,2}/,
  'jwt': /\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/,
  'assigned-secret': /\b(api[_-]?key|secret|token|passwd|password)\b["']?\s*[:=]\s*["'][A-Za-z0-9\/+_-]{20,}["']/i,
  'email': /\b[A-Za-z0-9._%+-]+@(?!(?:[A-Za-z0-9.-]*\.)?(?:example|test|invalid|localhost)(?:\.[a-z]+)?\b)(?!(?:domain\.tld|site\.org|x\.com|y\.com|users\.noreply\.github\.com)\b)(?![0-9]x\.)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/,
  'windows-user-path': /[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9._ -]+/,
};
const SKIPDIR = new Set(['.git', 'node_modules']);
const hits = [];
(function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const f = p.join(d, e.name);
    if (e.isDirectory()) { if (!SKIPDIR.has(e.name)) walk(f); continue; }
    const st = fs.statSync(f); if (st.size > 5e6) continue;
    const buf = fs.readFileSync(f); if (buf.includes(0)) continue;
    const lines = buf.toString('utf8').split('\n');
    lines.forEach((l, i) => { for (const [k, re] of Object.entries(PATTERNS)) if (re.test(l)) hits.push({ file: p.relative(root, f).split(p.sep).join('/'), line: i + 1, rule: k }); });
  }
})(root);
const inEvals = (f) => /^(skills|retired)\/[^/]+\/evals\//.test(f);
const bad = hits.filter((h) => !inEvals(h.file));
const byRule = {};
for (const h of hits) { const k = (inEvals(h.file) ? 'evals:' : 'OUTSIDE:') + h.rule; byRule[k] = (byRule[k] || 0) + 1; }
console.log(JSON.stringify({ total: hits.length, outside_evals: bad.length, byRule }, null, 1));
for (const h of bad.slice(0, 50)) console.log(`${h.file}:${h.line} ${h.rule}`);
process.exit(bad.length ? 1 : 0);

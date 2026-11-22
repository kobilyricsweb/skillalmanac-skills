#!/usr/bin/env node
// Generates catalog.json (slug, name, one_line, category, site URL) for every folder under skills/.
// Usage: node tools/build_catalog.cjs [--site-catalog <path to the site's generated catalog.json>]
// The site catalog supplies one_line and category (they are editorial fields kept on the site).
// Without it, one_line is the first sentence of the SKILL.md description and category is "uncategorized".
const fs = require('fs'), p = require('path');
const root = p.resolve(__dirname, '..');
const i = process.argv.indexOf('--site-catalog');
const site = {};
if (i > -1) {
  const c = JSON.parse(fs.readFileSync(process.argv[i + 1], 'utf8'));
  for (const s of c.skills) if (s.publisher_slug === 'skill-almanac') site[s.skill_slug] = s;
}
const SITE = 'https://skillalmanac.com';
const out = [];
for (const slug of fs.readdirSync(p.join(root, 'skills')).sort()) {
  const f = p.join(root, 'skills', slug, 'SKILL.md');
  if (!fs.existsSync(f)) continue;
  const fm = (fs.readFileSync(f, 'utf8').match(/^---\n([\s\S]*?)\n---/) || [])[1] || '';
  const get = (k) => ((fm.match(new RegExp('^' + k + ':\s*(.*)$', 'm')) || [])[1] || '').trim().replace(/^["']|["']$/g, '');
  const s = site[slug];
  const desc = get('description');
  out.push({
    slug,
    name: get('name') || slug,
    one_line: s ? s.one_line : desc.split(/(?<=\.)\s/)[0],
    category: s ? s.primary_category : 'uncategorized',
    site_url: `${SITE}/skills/skill-almanac/${slug}`,
  });
}
fs.writeFileSync(p.join(root, 'catalog.json'), JSON.stringify({ repo: 'kobilyricsweb/skillalmanac-skills', count: out.length, skills: out }, null, 2) + '\n');
console.log(`catalog.json: ${out.length} skills`);

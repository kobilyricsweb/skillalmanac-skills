# Hook recipes

Skeletons in Node because it needs no extra tools in a JavaScript project. Translate to the project's own runtime. Each recipe lists the cases to fire before it counts as working.

## Contents

- Shared reader
- File guard (PreToolUse on editing tools)
- Command guard (PreToolUse on Bash)
- Run a tool on the edited file (PostToolUse)
- Gate on a check before stopping (Stop)
- Add context at session start or on each prompt

## Shared reader

```js
const fs = require('fs');
function readInput(failClosed) {
  try {
    return JSON.parse(fs.readFileSync(0, 'utf8'));
  } catch (err) {
    if (failClosed) { console.error('hook: unreadable input, blocking'); process.exit(2); }
    process.exit(0);
  }
}
```

## File guard (PreToolUse on editing tools)

Matcher: `Edit|Write|MultiEdit|NotebookEdit`. Fail closed.

```js
const path = require('path');
const input = readInput(true);
const root = path.resolve(process.env.CLAUDE_PROJECT_DIR || input.cwd || '.');
const raw = String((input.tool_input || {}).file_path || '').replace(/\\/g, '/');
const rel = path.relative(root, path.resolve(root, raw)).replace(/\\/g, '/');
const parts = rel.split('/');
const base = parts[parts.length - 1];
const blocked =
  /^\.env(\..+)?$/.test(base) ||          // .env and .env.<anything>
  parts.slice(0, -1).includes('migrations') ||
  base === 'package-lock.json';
if (blocked) { console.error(`Blocked: ${rel} is protected. Ask the user to make this change.`); process.exit(2); }
```

Decide with the user whether templates such as `.env.example` are protected, and whether matching ignores case (it should on Windows and macOS file systems).

Fire: each protected path; a `..` path that resolves to one; a backslash path; a look-alike that must pass (`docs/migrations-guide.md`); a path outside the project.

This guard sees editing tools only. A shell command can still write the file; add a command guard or say so.

## Command guard (PreToolUse on Bash)

Fail closed. Tokenise, do not substring-match.

```js
const input = readInput(true);
const command = String((input.tool_input || {}).command || '');
for (const segment of command.split(/&&|\|\||;|\|/)) {
  const t = segment.trim().split(/\s+/);
  const flags = t.filter((x) => /^-[A-Za-z]+$/.test(x)).join('');
  if (t[0] === 'rm' && /r/i.test(flags) && /f/.test(flags)) deny('recursive forced delete');
  if (t[0] === 'git' && t.includes('push') && t.some((x) => x === '--force' || /^-[A-Za-z]*f/.test(x))) deny('force push');
}
function deny(what) { console.error(`Blocked: ${what}. Ask the user to run it.`); process.exit(2); }
```

Decide with the user whether `--force-with-lease` is allowed; the skeleton allows it. Commands wrapped in `sh -c "..."`, `sudo`, `env X=1` or an alias are not seen by this pattern; list that under "Not covered" or strip those prefixes first.

Fire: every flag spelling and position; a compound command (`cd x && git push -f`); similar safe commands (`git push`, `rm file`, `grep -rf pat dir`); a run from a subdirectory.

## Run a tool on the edited file (PostToolUse)

Matcher: `Edit|Write|MultiEdit`. Fail open. Filter on extension in the script; pass the path as an argument, not inside a shell string.

```js
const { spawnSync } = require('child_process');
const input = readInput(false);
const file = String((input.tool_input || {}).file_path || '');
if (!/\.(js|ts)$/.test(file)) process.exit(0);
const r = spawnSync('npm', ['run', 'format', '--', file], {
  cwd: process.env.CLAUDE_PROJECT_DIR, shell: process.platform === 'win32', encoding: 'utf8',
});
if (r.status !== 0) { console.error(r.stderr || r.stdout); process.exit(2); }  // feedback only; the edit already happened
```

On Windows `npm` is a `.cmd` file, so `shell: true` is needed there; when a shell is used, quote the path (`"${file}"`) because the arguments are joined into one string.

Fire: a matching file; a non-matching file (the tool must not run); a path with a space; a file that makes the tool fail.

## Gate on a check before stopping (Stop)

No matcher. Give it a timeout that fits the check.

```js
const { spawnSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');
const input = readInput(false);
const r = spawnSync('npm', ['test'], { cwd: process.env.CLAUDE_PROJECT_DIR, shell: process.platform === 'win32', encoding: 'utf8' });
const counter = path.join(os.tmpdir(), `stop-gate-${input.session_id || 'x'}.count`);
if (r.status === 0) { fs.rmSync(counter, { force: true }); process.exit(0); }
const tries = (input.stop_hook_active && fs.existsSync(counter) ? Number(fs.readFileSync(counter, 'utf8')) : 0) + 1;
fs.writeFileSync(counter, String(tries));
if (tries > 5) { console.error('Tests still failing after 5 attempts; letting the turn end.'); fs.rmSync(counter, { force: true }); process.exit(0); }
console.error(`Tests are failing (attempt ${tries} of 5). Fix them before finishing.\n${(r.stdout + r.stderr).slice(-3000)}`);
process.exit(2);
```

The bound is a choice. If the user wants "never stop while failing", keep blocking, and tell them the harness itself ends the turn after a run of consecutive continuations and that they can interrupt.

Fire: failing state (exit 2, output in the reason); passing state (exit 0); `stop_hook_active: true` with a failing state, repeated past the bound.

## Add context at session start or on each prompt

`SessionStart` or `UserPromptSubmit`. Print plain text on stdout and exit 0; it is added to the model's context. Keep it short, since it is paid for on every session or prompt, and never print secrets.

Fire: confirm the text printed; confirm exit 0 when the source of the context (a file, a git command) is missing.

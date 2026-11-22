## תקציר

- זהו תוכן עמוד ה-skill באתר: מה הוא עושה, מתי להשתמש, דוגמאות, מגבלות, תסריט הדגמה ושאלות נפוצות.
- ה-skill כותב, מתקין, בודק ומדבג hooks של סוכן קוד (פורמט Claude Code), ומחייב להפעיל כל hook עם קלט לדוגמה לפני שמכריזים שהוא עובד.
- כולל script סטטי לבדיקת קובץ ההגדרות (שמות אירועים, timeout בשניות, נתיבים יחסיים, לולאת Stop) ושישה קבצי payload לדוגמה.
- הראיה החזקה ביותר: בודק עצמאי שמריץ בפועל את ה-hooks שנכתבו עם payloads; ה-baseline השאיר timeout של 5000 שניות ו-Stop hook בלי גבול ובלי בדיקת מצב הכישלון.
- הדוגמאות והמספרים לקוחים מריצות שמורות; טיוטה, לא לפרסום לפני סקירה אנושית והשלמת הבדיקות.

---

# Listing page content: agent-hooks-authoring

**One line:** Write, install, test and debug coding-agent hooks that are proven by firing them with sample input.

## What it does

The skill makes the agent treat a hook as unattended code: it picks the event and matcher from a reference table instead of memory, merges into the existing settings file, writes the handler as a script in a runtime the project already has, chooses a fail-open or fail-closed mode on purpose, and then fires the hook with sample payloads for the block case, the allow case and the awkward variants before reporting. A static lint script checks the configuration for the mistakes that make hooks silently do nothing.

## Capabilities

- A reference of events, matchers, stdin fields, exit codes, JSON output, timeouts (seconds) and the Stop-hook loop rule, with the date it was checked
- Recipes: file guard, command guard, run a tool on the edited file, gate on a check before stopping, context injection
- `scripts/hook_config_lint.py`: unknown or mis-cased events, handler one level too high, millisecond-looking timeouts, relative or unquoted script paths, matchers that match nothing, Stop hooks with no loop guard, guards that exit 1
- Six sample payload files to pipe into a hook
- A fixed report: where it is installed, fail mode, test table, what it does not cover, how to turn it off

## When to use

You want something to happen every time regardless of what the model decides: format after each edit, block force-pushes or `rm -rf`, protect `.env` or migrations, keep working until tests pass, add context at session start; or a hook is not firing or blocks everything.

## When not to use

Git hooks (pre-commit, husky), React hooks, webhooks, plain permission allow/deny rules.

## Requirements

Python 3.9+ for the lint script (standard library). No network. The reference and lint target Claude Code hooks; other harnesses were not checked.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples (from saved runs)

1. Prompt: "The hook in infra-tools/ is supposed to block git force-pushes and rm -rf, but yesterday the agent still ran a force-push while working inside packages/api. Find out why and fix it." Result: `evals/runs/h3-debug-broken-hook/with_skill/reply.md`: six causes (wrong input field `cmd`, exit 1 instead of 2, relative script path, timeout 5000 read as seconds, fail-open parsing, narrow patterns) and a table of fired cases. The independent checker confirmed 5 of 5 behaviours; the run without the skill left the timeout at 5000.
2. Prompt: "Set up two hooks: format the edited .js/.ts file, and don't let the agent end its turn while npm test is failing." Result: `evals/runs/h2-format-and-test-gate/with_skill/reply.md`: a Stop gate with a bounded retry count that was fired in the failing and the passing state. The run without the skill had an unbounded gate and tested only the passing state. The same with-skill run also overwrote `src/my routes.js` with test content and said so; see Limits.

## Limits

- Facts describe Claude Code hooks as documented on 2026-11-20; they change between releases.
- Pattern guards reduce accidents; they are not a security boundary. A file guard does not see shell commands.
- The lint script reads configuration and script text; it never runs a hook.
- Known defect in the tested version: nothing tells the agent to fire PostToolUse tests against a scratch copy, and one eval run overwrote a real source file while testing.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model, Claude Code only, 2026-11-20. Assertions passed: 22/22 with the skill against 19/22 without. A blind grader preferred the with-skill result in 3 of 3 tasks. Average token overhead 14,108 per run (+19%). Blinding was imperfect and each cell ran once. Not tested: other tools, real triggering, human review.

## Demo script (60 to 90 seconds)

1. Show a broken guard hook and a transcript where a force-push went through.
2. Run the lint: it flags the 5000 timeout as 83 minutes, the relative path and the exit code.
3. The agent fires the fixed hook with three force-push spellings and from a subdirectory; a table of exit codes fills in.
4. Final report: causes found, tested cases, what is still not covered.

## FAQ seeds

- Does it work for tools other than Claude Code? The testing discipline carries over. The event tables and the lint script are for Claude Code only; other tools were not checked.
- Does the skill run my hooks? The lint script never does. The agent fires them by hand with sample payloads, in your project.
- Does it need network access? No.
- Will the guard stop a determined bypass? No. It catches accidents; the report lists what it does not cover.
- Why a script file instead of a one-line command? One-liners hide quoting and parsing mistakes and cannot be tested case by case.
- How do I remove a hook it added? The report names the settings entry and the script file to delete.

## Changelog

- 0.1.0 (2026-11-20): first version; all evals ran on this version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.

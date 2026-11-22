#!/bin/sh
# Runs every fixture case and compares stdout and exit code with evals/fixtures/expected/.
# Usage (from the skill root): sh evals/run_fixtures.sh   -> prints PASS/FAIL per case, exit 1 on any FAIL.
# Add "--record" to rewrite the expected files from the current output (review the diff before committing).
cd "$(dirname "$0")/.." || exit 2
mkdir -p evals/fixtures/expected
fail=0
run() { # name expected_exit command...
  name=$1; want=$2; shift 2
  out=$("$@" 2>&1); code=$?
  printf '%s\n[exit %s]\n' "$out" "$code" > "/tmp/fx_$$.txt" 2>/dev/null || return 2
  if [ "$RECORD" = "1" ]; then cp "/tmp/fx_$$.txt" "evals/fixtures/expected/$name.txt"; fi
  if [ "$code" = "$want" ] && diff -q "/tmp/fx_$$.txt" "evals/fixtures/expected/$name.txt" >/dev/null 2>&1; then
    echo "PASS $name (exit $code)"
  else
    echo "FAIL $name (exit $code, wanted $want)"; fail=1
  fi
  rm -f "/tmp/fx_$$.txt"
}
[ "$1" = "--record" ] && RECORD=1
PY="python -I"
run check_good 0 $PY scripts/skill_check.py evals/fixtures/good-skill
run check_bad 1 $PY scripts/skill_check.py evals/fixtures/bad-skill
run check_block 1 $PY scripts/skill_check.py evals/fixtures/block-skill
run triggers_good 0 $PY scripts/eval_score.py triggers evals/trigger_queries.json evals/fixtures/trigger_results_good.json
run triggers_bad 1 $PY scripts/eval_score.py triggers evals/trigger_queries.json evals/fixtures/trigger_results_bad.json
run tasks_with 0 $PY scripts/eval_score.py tasks evals/evals.json t1-runbook-to-skill evals/fixtures/out_with
run tasks_baseline 1 $PY scripts/eval_score.py tasks evals/evals.json t1-runbook-to-skill evals/fixtures/out_baseline
run tasks_pair 0 $PY scripts/eval_score.py tasks evals/evals.json t1-runbook-to-skill evals/fixtures/out_with evals/fixtures/out_baseline
run tasks_empty 1 $PY scripts/eval_score.py tasks evals/evals.json t2-fix-silent-skill evals/files/t3-eval-set
exit $fail

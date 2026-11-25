#!/bin/bash
W="$1"; SKILL_SRC="$2"; REPS=2
cd "$W"
run_one() {
  local tid="$1" arm="$2" rep="$3" short="${1%%-*}"
  local d="$W/sandbox/${tid}_${arm}_${rep}"
  rm -rf "$d"; mkdir -p "$d"
  cp -r "$W/inputs/$short/." "$d/"
  local prompt
  prompt=$(python -c "import json;t=[x for x in json.load(open('$W/tasks.json'))['tasks'] if x['id']=='$tid'][0];print(t['prompt'])")
  if [ "$arm" = with ]; then
    mkdir -p "$d/.tools"; cp -r "$SKILL_SRC" "$d/.tools/skill-lie-detector"
    prompt="Read .tools/skill-lie-detector/SKILL.md and the files it points to, then follow it for this task.

$prompt"
  fi
  mkdir -p "$W/runs/$tid"
  (cd "$d" && env -u ANTHROPIC_API_KEY claude -p "$prompt" --model claude-haiku-5-5 --allowedTools "Read" "Write" "Glob" "Grep" "Bash(python:*)" "Bash(python3:*)" "Bash(ls:*)" "Bash(cat:*)" > "$W/runs/$tid/${arm}_${rep}.md" 2> "$d/stderr.txt")
  echo "done $tid $arm $rep $(wc -c < "$W/runs/$tid/${arm}_${rep}.md")"
}
i=0
for tid in $(python -c "import json;print(' '.join(t['id'] for t in json.load(open('tasks.json'))['tasks']))"); do
  for arm in ${ARMS:-with without}; do for rep in $(seq 1 $REPS); do
    run_one "$tid" "$arm" "$rep" &
    i=$((i+1)); if [ $((i % 6)) -eq 0 ]; then wait; fi
  done; done
done
wait
echo ALL_DONE

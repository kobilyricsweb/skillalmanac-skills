"""Replay synthetic output-contract fixtures; no model or network access."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from check_output import check_schema, load, validate

root = Path(__file__).resolve().parents[1]
schema = load(root/'references/output-schema.json')
check_schema(schema)
fixtures = json.loads((root/'evals/contract-fixtures.json').read_text(encoding='utf-8'))
results = []
for item in fixtures:
    errors = validate(load(root/'evals'/item['file']), schema)
    passed = (not errors) == item['expected_valid']
    results.append({'id':item['id'], 'passed':passed, 'valid':not errors, 'errors':errors})
print(json.dumps({'passed':all(r['passed'] for r in results), 'fixtures':results}, ensure_ascii=False))
sys.exit(0 if all(r['passed'] for r in results) else 1)

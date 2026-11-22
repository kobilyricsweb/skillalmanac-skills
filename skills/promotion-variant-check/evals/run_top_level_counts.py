"""Normative observed-array counts on top-level schema rejection."""
import contextlib,io,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
from audit import main
count_key='variant_count';results=[]
for path in sorted((root/'evals/top-level-count-regressions').glob('*.json')):
    original=sys.argv[:];output=io.StringIO()
    try:
        sys.argv=['audit.py',str(path)]
        with contextlib.redirect_stdout(output):code=main()
    finally:sys.argv=original
    actual=json.loads(output.getvalue());expected_count=201 if path.stem=='oversized-array' else 0 if path.stem=='wrong-array-type' else 2
    passed=code==2 and actual.get('input_error') is True and actual.get('ok') is False and actual.get(count_key)==expected_count and actual.get('findings')==[]
    results.append({'id':path.stem,'passed':passed,'expected_count':expected_count,'exit':code,'actual':actual})
report={'method':'normative top-level schema errors retain observable supplied array length, not validated entities','passed':all(x['passed'] for x in results),'fixtures':results}
print(json.dumps(report));sys.exit(0 if report['passed'] else 1)

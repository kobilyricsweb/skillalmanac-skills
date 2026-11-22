"""Normative numeric-reader regression checks; no network or files written."""
import contextlib,io,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from audit import main
results=[]
for path in sorted((root/'evals/numeric-regressions').glob('*.json')):
    finite=path.stem in ('finite-large','finite-negative-large')
    captured=io.StringIO();original=sys.argv[:]
    try:
        sys.argv=['audit.py',str(path)]
        with contextlib.redirect_stdout(captured):code=main()
    finally:sys.argv=original
    value=json.loads(captured.getvalue())
    if not finite:
        passed=code==2 and value.get('input_error') is True and value.get('code')=='invalid_number' and value.get('ok') is False
    elif root.name=='dataset-field-profiler':
        passed=code==0 and value.get('ok') is True
    else:
        passed=code==2 and value.get('input_error') is True and value.get('code')!='invalid_number'
    results.append({'id':path.stem,'passed':passed,'exit':code,'actual':value})
report={'method':'normative independent input/error and finite-Decimal domain assertions','passed':all(r['passed'] for r in results),'fixtures':results}
print(json.dumps(report));sys.exit(0 if report['passed'] else 1)

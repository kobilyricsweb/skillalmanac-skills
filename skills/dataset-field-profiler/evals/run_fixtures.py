"""Replay actual audit.main against retained input files and observed results."""
import contextlib
import io
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from audit import main
saved=json.loads((root/'evals/script_results.json').read_text(encoding='utf-8'))
results=[]
for case in saved['fixtures']:
    ident=case['id']
    filename={'missing_file':'absent','empty_object':'invalid'}.get(ident,ident)
    fixture=root/'evals/fixtures'/(filename+'.json')
    captured=io.StringIO()
    original=sys.argv[:]
    try:
        sys.argv=['audit.py',str(fixture)]
        with contextlib.redirect_stdout(captured):
            exit_code=main()
    finally:
        sys.argv=original
    actual=json.loads(captured.getvalue())
    if ident=='missing_file':
        passed=exit_code==2 and actual.get('ok') is False and bool(actual.get('input_error'))
    else:
        expected=dict(case['output'])
        # Explicit diagnostic-contract migration; script_results remains the original capture.
        if expected.get('input_error') and (expected.get('message')=='non-finite JSON number' or expected.get('message','').startswith('number exceeds coefficient-digit')):
            expected['code']='invalid_number'
        passed=exit_code==case['exit'] and actual==expected
    results.append({'id':ident,'passed':passed,'exit':exit_code,'actual':actual})
report={'method':'retained observed-output regression replay; missing-file path excluded; not independent truth','passed':all(x['passed'] for x in results),'fixtures':results}
print(json.dumps(report))
sys.exit(0 if report['passed'] else 1)

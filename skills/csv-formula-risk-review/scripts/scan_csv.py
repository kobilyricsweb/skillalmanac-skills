"""Read-only CSV formula indicator scan. No application launch or network access."""
import argparse
import csv
import io
import json
from pathlib import Path
import sys

MAX_BYTES = 2 * 1024 * 1024
PREFIXES = '=+-@＝＋－＠'


def scan(path, delimiter=','):
    if delimiter == '\\t':
        delimiter = '\t'
    if len(delimiter) != 1 or delimiter in '\r\n\x00"':
        raise ValueError('delimiter must be one character other than CR, LF, NUL or double quote')
    # Read at most limit+1: enforce the limit without a file-size/read race.
    with Path(path).open('rb') as source:
        raw = source.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('input exceeds 2 MiB; no partial scan performed')
    text = raw.decode('utf-8-sig')
    if '\x00' in text:
        raise ValueError('NUL byte found; request a UTF-8 text export')
    findings = []
    records = cells = 0
    previous_limit = csv.field_size_limit(MAX_BYTES)
    try:
        reader = csv.reader(io.StringIO(text, newline=''), delimiter=delimiter, strict=True)
        for records, row in enumerate(reader, 1):
            for column, value in enumerate(row, 1):
                cells += 1
                indicators = []
                if value.startswith(('\t', '\r', '\n')):
                    indicators.append('leading_tab_cr_or_lf')
                candidate = value.lstrip(' \t\r\n')
                if candidate and candidate[0] in PREFIXES:
                    indicators.append('formula_prefix_' + candidate[0])
                if indicators:
                    findings.append({'record': records, 'physical_end_line': reader.line_num,
                                     'column': column, 'indicators': indicators})
    finally:
        csv.field_size_limit(previous_limit)
    if cells == 0:
        raise ValueError('no cells inspected; input is empty or blank')
    return {'status': 'review_required' if findings else 'no_candidates',
            'delimiter': delimiter, 'records_inspected': records,
            'cells_inspected': cells, 'findings': findings,
            'scope': 'ASCII and full-width prefix indicators plus leading tab/CR/LF; no cell values logged; not a safety certification'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path')
    parser.add_argument('--delimiter', default=',')
    args = parser.parse_args()
    try:
        result = scan(args.path, args.delimiter)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        # Avoid disclosing path names or cell contents in parser/OS error messages.
        print(json.dumps({'status': 'error', 'error_type': type(exc).__name__,
                          'message': 'Input could not be fully scanned; check path, UTF-8 encoding, CSV syntax, delimiter and 2 MiB limit.'}))
        return 2
    print(json.dumps(result, ensure_ascii=True))
    return 1 if result['findings'] else 0


if __name__ == '__main__':
    sys.exit(main())

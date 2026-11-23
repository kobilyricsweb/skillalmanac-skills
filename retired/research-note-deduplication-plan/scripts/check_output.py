"""Offline checker for the explicitly bounded schema profile shipped with this skill.

Python standard library only. This validates artifact structure, not factual correctness.
Supported keywords are listed in KEYS; unsupported schema features are errors.
"""
import argparse
import datetime
import decimal
import json
from pathlib import Path
import sys

KEYS = {'$schema', 'title', 'description', 'type', 'properties', 'required',
        'additionalProperties', 'items', 'enum', 'const', 'minItems', 'maxItems',
        'uniqueItems', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
        'minLength', 'maxLength', 'format', '$defs', '$ref', 'allOf', 'if', 'then', 'else', 'contains'}
TYPES = {'object', 'array', 'string', 'integer', 'number', 'boolean', 'null'}
LIMIT = 2 * 1024 * 1024


def number(text):
    if len(text) > 1000:
        raise ValueError('Numeric token exceeds 1000 characters')
    value = decimal.Decimal(text)
    if not value.is_finite() or abs(value.adjusted()) > 1000:
        raise ValueError('Nonfinite or oversized exponent')
    return value


def pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ValueError('Duplicate JSON key: ' + key)
        out[key] = value
    return out


def load(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('JSON file exceeds 2 MiB')
    value = json.loads(raw.decode('utf-8-sig'), parse_int=number, parse_float=number,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON: '+value)),
                      object_pairs_hook=pairs)
    stack = [(value, 0)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > 50000 or depth > 100:
            raise ValueError('JSON exceeds 50000 nodes or depth 100')
        children = item.values() if isinstance(item, dict) else item if isinstance(item, list) else ()
        stack.extend((child, depth+1) for child in children)
    return value


def numeric(value):
    return isinstance(value, (int, float, decimal.Decimal)) and not isinstance(value, bool)


def equal(left, right):
    if numeric(left) and numeric(right):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(equal(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(equal(a, b) for a, b in zip(left, right))
    return left == right


def frozen(value):
    if numeric(value):
        return ('number', value)
    if isinstance(value, dict):
        return ('object', tuple(sorted((key, frozen(item)) for key, item in value.items())))
    if isinstance(value, list):
        return ('array', tuple(frozen(item) for item in value))
    return (type(value).__name__, value)


def resolve(root, reference):
    if not isinstance(reference,str) or not reference.startswith('#/$defs/'):
        raise ValueError('Only local #/$defs/name references supported')
    token=reference[len('#/$defs/'):]
    if '/' in token or '~' in token.replace('~0','').replace('~1',''):
        raise ValueError('Unsupported local reference pointer')
    name=token.replace('~1','/').replace('~0','~')
    definitions=root.get('$defs',{}) if isinstance(root,dict) else {}
    if name not in definitions:
        raise ValueError('Unresolved local schema reference')
    return definitions[name]


def check_schema(schema, depth=0, root=None, refs=()):
    if root is None:
        root=schema
    if isinstance(schema, bool):
        return
    if depth > 60 or not isinstance(schema, dict):
        raise ValueError('Expected object schema with depth <=60')
    unknown = set(schema) - KEYS
    if unknown:
        raise ValueError('Unsupported schema keywords: ' + ', '.join(sorted(unknown)))
    kind = schema.get('type')
    kinds = kind if isinstance(kind, list) else [kind]
    if 'type' in schema and (not kinds or any(not isinstance(k,str) or k not in TYPES for k in kinds) or len(set(kinds))!=len(kinds)):
        raise ValueError('Unsupported explicit type')
    for key in ('title','description'):
        if key in schema and not isinstance(schema[key],str):
            raise ValueError('Expected string '+key)
    if '$schema' in schema and schema['$schema'] != 'https://json-schema.org/draft/2020-12/schema':
        raise ValueError('Unsupported schema dialect')
    if 'format' in schema and schema['format'] != 'date':
        raise ValueError('Only date format supported')
    if 'required' in schema and (not isinstance(schema['required'], list) or
            any(not isinstance(k, str) for k in schema['required']) or len(set(schema['required'])) != len(schema['required'])):
        raise ValueError('Invalid required list')
    if 'properties' in schema:
        if not isinstance(schema['properties'], dict):
            raise ValueError('Invalid properties')
        for child in schema['properties'].values():
            check_schema(child, depth + 1, root, refs)
    if 'items' in schema:
        check_schema(schema['items'], depth + 1, root, refs)
    if 'additionalProperties' in schema and not isinstance(schema['additionalProperties'], bool):
        check_schema(schema['additionalProperties'], depth + 1, root, refs)
    if '$defs' in schema:
        if not isinstance(schema['$defs'],dict):raise ValueError('Expected object $defs')
        for child in schema['$defs'].values():check_schema(child,depth+1,root,refs)
    if '$ref' in schema:
        reference=schema['$ref']
        if reference in refs:raise ValueError('Recursive schema references unsupported')
        check_schema(resolve(root,reference),depth+1,root,refs+(reference,))
    if 'allOf' in schema:
        if not isinstance(schema['allOf'],list) or not schema['allOf']:raise ValueError('Expected nonempty allOf')
        for child in schema['allOf']:check_schema(child,depth+1,root,refs)
    for key in ('if','then','else','contains'):
        if key in schema:check_schema(schema[key],depth+1,root,refs)
    for key in ('minItems', 'maxItems', 'minLength', 'maxLength'):
        if key in schema and (not numeric(schema[key]) or schema[key] < 0 or int(schema[key]) != schema[key]):
            raise ValueError('Invalid nonnegative integer ' + key)
    for key in ('minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum'):
        if key in schema and not numeric(schema[key]):
            raise ValueError('Invalid numeric bound ' + key)
    if 'uniqueItems' in schema and not isinstance(schema['uniqueItems'], bool):
        raise ValueError('Invalid uniqueItems')
    if 'enum' in schema and not isinstance(schema['enum'], list):
        raise ValueError('Invalid enum')


def matches(value, kind):
    return {'object': lambda: isinstance(value, dict), 'array': lambda: isinstance(value, list),
            'string': lambda: isinstance(value, str), 'number': lambda: numeric(value),
            'integer': lambda: numeric(value) and value == int(value),
            'boolean': lambda: isinstance(value, bool), 'null': lambda: value is None}[kind]()


def validate(value, schema, path='$', depth=0, root=None):
    if root is None:root=schema
    if schema is True:
        return []
    if schema is False:
        return [{'path':path, 'code':'false_schema', 'message':'Schema permits no value'}]
    if depth > 100:
        return [{'path': path, 'code': 'depth', 'message': 'Artifact nesting exceeds 100'}]
    errors = []
    def fail(code, message):
        if len(errors) < 100:
            errors.append({'path': path, 'code': code, 'message': message})
    kind = schema.get('type')
    kinds = kind if isinstance(kind, list) else [kind]
    if kind is not None and not any(matches(value, k) for k in kinds):
        fail('type', 'Expected ' + '|'.join(kinds))
        return errors
    if 'enum' in schema and not any(equal(value, item) for item in schema['enum']):
        fail('enum', 'Value is outside the permitted enum')
    if 'const' in schema and not equal(value, schema['const']):
        fail('const', 'Value differs from required constant')
    if '$ref' in schema:
        errors.extend(validate(value,resolve(root,schema['$ref']),path,depth+1,root))
    for child in schema.get('allOf',[]):
        errors.extend(validate(value,child,path,depth+1,root))
    if 'if' in schema:
        branch='then' if not validate(value,schema['if'],path,depth+1,root) else 'else'
        if branch in schema:errors.extend(validate(value,schema[branch],path,depth+1,root))
    if isinstance(value, dict):
        for key in schema.get('required', []):
            if key not in value:
                fail('required', 'Missing ' + key)
        props = schema.get('properties', {})
        for key, item in value.items():
            if key in props:
                errors.extend(validate(item, props[key], path + '/' + key.replace('~', '~0').replace('/', '~1'), depth + 1, root))
            elif schema.get('additionalProperties') is False:
                fail('additionalProperties', 'Unexpected property ' + key)
            elif isinstance(schema.get('additionalProperties'), dict):
                errors.extend(validate(item, schema['additionalProperties'], path+'/'+key.replace('~','~0').replace('/','~1'), depth+1, root))
    if isinstance(value, list):
        for key, op in [('minItems', lambda a, b: a < b), ('maxItems', lambda a, b: a > b)]:
            if key in schema and op(len(value), schema[key]):
                fail(key, 'Array length violates bound')
        if schema.get('uniqueItems') and len({frozen(item) for item in value}) != len(value):
            fail('uniqueItems', 'Duplicate array values')
        if 'contains' in schema and not any(not validate(item,schema['contains'],path+'/'+str(i),depth+1,root) for i,item in enumerate(value)):
            fail('contains','No array element matches contains')
        if 'items' in schema:
            for i, item in enumerate(value):
                errors.extend(validate(item, schema['items'], path+'/'+str(i), depth+1, root))
    if isinstance(value, str):
        for key, op in [('minLength', lambda a, b: a < b), ('maxLength', lambda a, b: a > b)]:
            if key in schema and op(len(value), schema[key]):
                fail(key, 'String length violates bound')
        if schema.get('format') == 'date':
            try:
                if len(value) != 10 or value[4] != '-' or value[7] != '-':
                    raise ValueError('Expected YYYY-MM-DD')
                datetime.date.fromisoformat(value)
            except ValueError:
                fail('format', 'Expected valid calendar date YYYY-MM-DD')
    if numeric(value):
        for key, op in [('minimum', lambda a, b: a < b), ('maximum', lambda a, b: a > b),
                        ('exclusiveMinimum', lambda a, b: a <= b), ('exclusiveMaximum', lambda a, b: a >= b)]:
            if key in schema and op(value, schema[key]):
                fail(key, 'Number violates bound')
    return errors[:100]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact', type=Path)
    parser.add_argument('--schema', type=Path, default=Path(__file__).resolve().parents[1]/'references/output-schema.json')
    args = parser.parse_args()
    try:
        schema = load(args.schema)
        check_schema(schema)
        errors = validate(load(args.artifact), schema)
    except (OSError, ValueError, TypeError, RecursionError, decimal.InvalidOperation) as exc:
        print(json.dumps({'status': 'input_or_contract_error', 'message': str(exc)}))
        return 2
    print(json.dumps({'status': 'invalid' if errors else 'valid', 'errors': errors}))
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())

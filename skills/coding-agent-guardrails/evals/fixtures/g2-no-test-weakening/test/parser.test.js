'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { parseRow, countFields } = require('../src/parser');

test('parses a plain row', () => {
  assert.deepStrictEqual(parseRow('a,b,c'), ['a', 'b', 'c']);
});

test('keeps commas inside quotes', () => {
  assert.deepStrictEqual(parseRow('"x,y",z'), ['x,y', 'z']);
});

test('counts the fields of a row', () => {
  assert.strictEqual(countFields('red,green,blue'), 3);
});

test('trims the line first', () => {
  assert.deepStrictEqual(parseRow('  p,q  '), ['p', 'q']);
});

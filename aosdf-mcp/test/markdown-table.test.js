'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { findTables, renderTable, replaceTableRows } = require('../src/markdown-table');

test('findTables parses a loosely-padded table', () => {
  const lines = [
    '| Task ID | Task | Status |',
    '| --- | --- | --- |',
    '| E2-T1 | Build the server | Planned |',
  ];
  const tables = findTables(lines);
  assert.equal(tables.length, 1);
  assert.deepEqual(tables[0].header, ['Task ID', 'Task', 'Status']);
  assert.deepEqual(tables[0].rows, [['E2-T1', 'Build the server', 'Planned']]);
});

test('findTables finds multiple tables in one document', () => {
  const lines = [
    '# Heading',
    '',
    '| A | B |',
    '| - | - |',
    '| 1 | 2 |',
    '',
    'Some prose.',
    '',
    '| C | D |',
    '| - | - |',
    '| 3 | 4 |',
  ];
  const tables = findTables(lines);
  assert.equal(tables.length, 2);
  assert.deepEqual(tables[1].header, ['C', 'D']);
});

test('renderTable pads dashes and cells to the Document Formatting Standard', () => {
  const header = ['Task ID', 'Task Name', 'Status'];
  const rows = [
    ['M1-T1', 'Infra Provisioning', 'Planned'],
    ['M1-T2', 'DB Schema', 'Planned'],
  ];
  const lines = renderTable(header, rows);
  assert.equal(lines[0], '| Task ID | Task Name          | Status  |');
  assert.equal(lines[1], '| ------- | ------------------ | ------- |');
  assert.equal(lines[2], '| M1-T1   | Infra Provisioning | Planned |');
  assert.equal(lines[3], '| M1-T2   | DB Schema          | Planned |');
});

test('replaceTableRows only touches the target table lines', () => {
  const lines = [
    'before',
    '| A | B |',
    '| - | - |',
    '| 1 | 2 |',
    'after',
  ];
  const tables = findTables(lines);
  const newLines = replaceTableRows(lines, tables[0], ['A', 'B'], [['1', '2'], ['3', '4']]);
  assert.equal(newLines[0], 'before');
  assert.equal(newLines[newLines.length - 1], 'after');
  assert.ok(newLines.some((l) => l.includes('3') && l.includes('4')));
});

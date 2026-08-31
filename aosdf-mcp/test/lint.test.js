'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { lintContent, fixContent, lintTree, fixTree } = require('../src/lint');

function tmpDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'aosdf-lint-test-'));
}

test('lintContent finds no violations in a compliant table', () => {
  const raw = ['| Task ID | Task | Status |', '| --- | --- | --- |', '| E2-T1 | Build the server | Planned |', ''].join(
    '\n'
  );
  const compliant = fixContent(raw);
  assert.deepEqual(lintContent(compliant), []);
});

test('lintContent flags unpadded separator dashes (Rule 1)', () => {
  const content = ['| Task ID | Task |', '| --- | --- |', '| E2-T1 | Build the server |', ''].join('\n');
  const violations = lintContent(content);
  assert.equal(violations.length, 1);
  assert.equal(violations[0].line, 1);
});

test('lintContent flags unpadded data cells (Rule 2)', () => {
  const content = [
    '| Task ID | Task              |',
    '| ------- | ----------------- |',
    '| E2-T1 | Build the server |',
    '',
  ].join('\n');
  assert.equal(lintContent(content).length, 1);
});

test('lintContent reports one violation per non-compliant table, not per file', () => {
  const content = [
    '| A | B |',
    '| --- | --- |',
    '| 1 | 2 |',
    '',
    'Some prose between tables.',
    '',
    '| Column One | Column Two |',
    '| - | - |',
    '| 3 | 4 |',
    '',
  ].join('\n');
  assert.equal(lintContent(content).length, 2);
});

test('fixContent produces content with zero remaining violations', () => {
  const content = ['| Task ID | Task |', '| --- | --- |', '| E2-T1 | Build the server |', ''].join('\n');
  const fixed = fixContent(content);
  assert.deepEqual(lintContent(fixed), []);
  assert.notEqual(fixed, content);
});

test('fixContent is a no-op on already-compliant content', () => {
  const raw = ['| Task ID | Task |', '| --- | --- |', '| E2-T1 | Build the server |', ''].join('\n');
  const compliant = fixContent(raw);
  assert.equal(fixContent(compliant), compliant);
});

test('lintTree walks nested directories and skips *-site/, node_modules, .git', () => {
  const root = tmpDir();
  try {
    fs.mkdirSync(path.join(root, 'docs', 'nested'), { recursive: true });
    fs.mkdirSync(path.join(root, 'docs-site'), { recursive: true });
    fs.mkdirSync(path.join(root, 'node_modules'), { recursive: true });
    fs.mkdirSync(path.join(root, '.git'), { recursive: true });

    const bad = '| A | B |\n| --- | --- |\n| 1 | 2 |\n';
    fs.writeFileSync(path.join(root, 'docs', 'nested', 'x.md'), bad);
    fs.writeFileSync(path.join(root, 'docs-site', 'ignored.md'), bad);
    fs.writeFileSync(path.join(root, 'node_modules', 'ignored.md'), bad);
    fs.writeFileSync(path.join(root, '.git', 'ignored.md'), bad);

    const report = lintTree(root);
    assert.equal(report.length, 1);
    assert.match(report[0].file, /nested[/\\]x\.md$/);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('fixTree rewrites only the files that need it, in place', () => {
  const root = tmpDir();
  try {
    const bad = '| A | B |\n| --- | --- |\n| 1 | 2 |\n';
    const good = '| A | B |\n| - | - |\n| 1 | 2 |\n';
    fs.writeFileSync(path.join(root, 'bad.md'), bad);
    fs.writeFileSync(path.join(root, 'good.md'), good);

    const changed = fixTree(root);
    assert.equal(changed.length, 1);
    assert.match(changed[0], /bad\.md$/);

    assert.equal(lintTree(root).length, 0);
    assert.equal(fs.readFileSync(path.join(root, 'good.md'), 'utf8'), good);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

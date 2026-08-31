'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');
const { readPendingPrompts } = require('../src/promptsData');

// Reused directly from aosdf-mcp's own fixtures (E2-T1) — one Executed row,
// one Pending Approval row.
const FIXTURES = path.join(__dirname, '..', '..', 'aosdf-mcp', 'test', 'fixtures');

test('readPendingPrompts skips the Executed row and surfaces only the pending one', () => {
  const pending = readPendingPrompts(FIXTURES);
  assert.equal(pending.length, 1);
  assert.equal(pending[0].fileName, 'E5-T1_write-actions_prompt.md');
  assert.equal(pending[0].task, 'E5-T1');
  assert.equal(pending[0].status, 'Pending Approval');
});

test('readPendingPrompts resolves promptPath relative to the index file\'s own directory', () => {
  const pending = readPendingPrompts(FIXTURES);
  const expectedDir = path.join(FIXTURES, 'documents', '05_AI_Agent_System', 'implementation_prompts');
  assert.equal(path.dirname(pending[0].promptPath), expectedDir);
});

test('readPendingPrompts returns an empty array when the index file does not exist', () => {
  const pending = readPendingPrompts(path.join(FIXTURES, 'nonexistent-root'));
  assert.deepEqual(pending, []);
});

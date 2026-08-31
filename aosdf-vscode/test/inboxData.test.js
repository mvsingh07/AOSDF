'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');
const { readInbox, isPlaceholderId, CLOSED_STATUS } = require('../src/inboxData');

// Reused directly rather than duplicated — aosdf-mcp (E2-T1) already
// maintains these fixtures for its own path-resolution/table-parsing tests.
const FIXTURES = path.join(__dirname, '..', '..', 'aosdf-mcp', 'test', 'fixtures');

test('readInbox surfaces the one open gap from the shared fixture, skipping nothing', () => {
  const { gaps } = readInbox(FIXTURES);
  assert.equal(gaps.length, 1);
  assert.equal(gaps[0].id, 'GAP-001');
  assert.equal(gaps[0].status, 'Open');
  assert.equal(gaps[0].kind, 'gap');
});

test('readInbox surfaces the one Pending manual action, and skips the archive table with no Status column', () => {
  const { actions } = readInbox(FIXTURES);
  assert.equal(actions.length, 1);
  assert.equal(actions[0].id, 'MA-001');
  assert.equal(actions[0].status, 'Pending');
  assert.ok(!actions.some((a) => a.id === 'MA-000'));
});

test('readInbox against the bare-"ID"-header identified_gaps fixture still matches on the id column', () => {
  const { resolvePaths } = require('../../aosdf-mcp/src/config');
  const { readOpenRows } = require('../src/inboxData');
  const bareIdPath = path.join(FIXTURES, 'identified_gaps_bare_id.md');
  const rows = readOpenRows(bareIdPath, /^(gap\s*id|id)$/i);
  assert.equal(rows.length, 0); // fixture's only row is the never-filled placeholder
});

test('isPlaceholderId recognizes the "(none yet...)" convention and rejects real ids', () => {
  assert.ok(isPlaceholderId('_(none yet — this file is appended to, never pre-filled)_'));
  assert.ok(isPlaceholderId(''));
  assert.ok(!isPlaceholderId('GAP-001'));
});

test('CLOSED_STATUS matches Done/Resolved/Cancelled regardless of trailing date', () => {
  assert.ok(CLOSED_STATUS.test('Resolved (2026-08-28)'));
  assert.ok(CLOSED_STATUS.test('Done (2026-08-27)'));
  assert.ok(CLOSED_STATUS.test('Cancelled'));
  assert.ok(!CLOSED_STATUS.test('Open'));
  assert.ok(!CLOSED_STATUS.test('Pending'));
});

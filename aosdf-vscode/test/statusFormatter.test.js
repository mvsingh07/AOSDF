'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { formatStatusBarText, formatTooltip } = require('../src/statusFormatter');

test('formatStatusBarText includes the next task id when one is planned', () => {
  const status = { currentState: 'IN_PROGRESS' };
  const nextTask = { taskId: 'E4-T1', task: 'Build editor-native views' };
  assert.equal(formatStatusBarText(status, nextTask), 'AOSDF: IN_PROGRESS — E4-T1');
});

test('formatStatusBarText falls back to state only when nothing is planned', () => {
  const status = { currentState: 'COMPLETE' };
  assert.equal(formatStatusBarText(status, { taskId: null }), 'AOSDF: COMPLETE');
});

test('formatStatusBarText handles a missing status gracefully', () => {
  assert.equal(formatStatusBarText(null, null), 'AOSDF: UNKNOWN');
});

test('formatTooltip surfaces phase heading and Next Action text', () => {
  const status = { currentState: 'PLANNING', nextAction: 'Do the next thing.' };
  const nextTask = { taskId: 'E4-T1', task: 'Build editor-native views', phaseHeading: 'E4 — Editor Integration MVP' };
  const tooltip = formatTooltip(status, nextTask);
  assert.match(tooltip, /Current State:\*\* PLANNING/);
  assert.match(tooltip, /E4-T1 — Build editor-native views/);
  assert.match(tooltip, /Phase:\*\* E4 — Editor Integration MVP/);
  assert.match(tooltip, /Do the next thing\./);
});

test('formatTooltip states plainly when no task is planned', () => {
  const tooltip = formatTooltip({ currentState: 'COMPLETE' }, { taskId: null });
  assert.match(tooltip, /none currently `Planned`/);
});

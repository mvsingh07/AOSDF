'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const os = require('os');

const readStatus = require('../src/tools/read-status');
const nextPlannedTask = require('../src/tools/next-planned-task');
const updateTaskStatus = require('../src/tools/update-task-status');
const logGap = require('../src/tools/log-gap');
const logManualAction = require('../src/tools/log-manual-action');
const readModuleIndex = require('../src/tools/read-module-index');

const FIXTURES = path.join(__dirname, 'fixtures');

// Every test gets its own copy of the fixtures so write tools never mutate
// the checked-in files and tests never interfere with each other.
function freshPaths() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'aosdf-mcp-test-'));
  fs.cpSync(FIXTURES, dir, { recursive: true });
  return {
    projectStatus: path.join(dir, 'project_status.md'),
    executionPlan: path.join(dir, 'documents', '06_Execution_Plan', 'execution_plan.md'),
    identifiedGaps: path.join(dir, 'identified_gaps.md'),
    manualActions: path.join(dir, 'documents', '12_Manual_Actions', 'actions.md'),
    moduleIndex: path.join(dir, 'documents', '03_System_Design', 'README.md'),
  };
}

test('aosdf_read_status extracts current state and Next Action only', () => {
  const paths = freshPaths();
  const result = readStatus.run({}, paths);
  assert.equal(result.currentState, 'PLANNING');
  assert.equal(result.nextAction, "Build the fixture's next task.");
  assert.ok(!result.nextAction.includes('Older Note'));
});

test('aosdf_next_planned_task skips phase-level rows and returns the task-level one', () => {
  const paths = freshPaths();
  const result = nextPlannedTask.run({}, paths);
  assert.equal(result.taskId, 'E2-T1');
  assert.equal(result.task, 'Build the server');
});

test('aosdf_next_planned_task returns null when nothing is Planned', () => {
  const paths = freshPaths();
  // Flip the one Planned task to Done first.
  updateTaskStatus.run({ id: 'E2-T1', status: 'Done' }, paths);
  const result = nextPlannedTask.run({}, paths);
  assert.equal(result.taskId, null);
});

test('aosdf_update_task_status rewrites only the matching row, format-standard-safe', () => {
  const paths = freshPaths();
  const result = updateTaskStatus.run({ id: 'E2-T1', status: 'Done (2026-08-27)' }, paths);
  assert.equal(result.tablesUpdated, 1);

  const content = fs.readFileSync(paths.executionPlan, 'utf8');
  assert.ok(content.includes('Done (2026-08-27)'));
  assert.ok(content.includes('E1-T1')); // untouched row survives

  // Re-parse to confirm the table is still well-formed (every row same column count).
  const { findTables } = require('../src/markdown-table');
  const tables = findTables(content.split('\n'));
  for (const t of tables) {
    for (const row of t.rows) assert.equal(row.length, t.header.length);
  }
});

test('aosdf_update_task_status can update a phase-level Master Sequence row too', () => {
  const paths = freshPaths();
  const result = updateTaskStatus.run({ id: 'E2', status: 'In Progress' }, paths);
  assert.equal(result.tablesUpdated, 1);
  const content = fs.readFileSync(paths.executionPlan, 'utf8');
  assert.ok(/\| E2\s*\| Server\s*\| In Progress\s*\|/.test(content));
});

test('aosdf_update_task_status throws on an unknown ID', () => {
  const paths = freshPaths();
  assert.throws(() => updateTaskStatus.run({ id: 'NOPE-T1', status: 'Done' }, paths), /No row with ID/);
});

test('aosdf_log_gap appends a row with an auto-generated sequential ID', () => {
  const paths = freshPaths();
  const result = logGap.run({ category: 'Security', description: 'New gap found' }, paths);
  assert.equal(result.gapId, 'GAP-002');

  const content = fs.readFileSync(paths.identifiedGaps, 'utf8');
  assert.ok(content.includes('GAP-002'));
  assert.ok(content.includes('New gap found'));
  assert.ok(content.includes('| Open '));
});

test('aosdf_log_manual_action appends to the Pending table, not Completed', () => {
  const paths = freshPaths();
  const result = logManualAction.run({ description: 'Do the new thing', priority: 'P2' }, paths);
  assert.equal(result.actionId, 'MA-002');

  const content = fs.readFileSync(paths.manualActions, 'utf8');
  const pendingSection = content.split('## Completed Actions')[0];
  const completedSection = content.split('## Completed Actions')[1];
  assert.ok(pendingSection.includes('MA-002'));
  assert.ok(!completedSection.includes('MA-002'));
});

test('aosdf_read_module_index returns structured rows', () => {
  const paths = freshPaths();
  const result = readModuleIndex.run({}, paths);
  assert.equal(result.rows.length, 2);
  assert.equal(result.rows[0]['Module Name'], 'billing');
});

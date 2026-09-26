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

test('aosdf_log_gap works against a bare "ID" header (no "Gap ID"/Owner/Identified/Resolution columns)', () => {
  // Regression test for a real drift found auditing this tool against this meta-project's own
  // identified_gaps.md (E2-T3): the ID column there is named "ID", not "Gap ID", and the file has
  // no Owner/Identified/Resolution columns at all. The original idIdx regex only matched "Gap ID",
  // so a real call against that real file silently wrote a row with a blank ID cell.
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'aosdf-mcp-test-'));
  fs.cpSync(FIXTURES, dir, { recursive: true });
  const identifiedGaps = path.join(dir, 'identified_gaps_bare_id.md');

  const result = logGap.run({ category: 'Compliance', description: 'bare-ID header case' }, { identifiedGaps });
  assert.equal(result.gapId, 'GAP-001');

  const content = fs.readFileSync(identifiedGaps, 'utf8');
  assert.ok(content.includes('| GAP-001'), 'the written row must carry its ID, not a blank cell');
  assert.ok(content.includes('bare-ID header case'));
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

// --- Regression tests for review1.md's seven reproduced defects (A-G) ---

test('[defect B] aosdf_log_manual_action writes `unblocks` to Blocks, not Milestone Task, when both columns exist', () => {
  // The real Pending Actions template (setup_aosdf.md) has "Milestone Task" positioned before
  // "Blocks" in the header — the fixture reproduces that exact ordering. Before the fix, the
  // column resolver took the first header match in left-to-right position order and silently
  // wrote into "Milestone Task" instead, so Superman's "Blocks"-only check never saw it.
  const paths = freshPaths();
  const result = logManualAction.run({ description: 'New blocker', unblocks: 'M2-T1' }, paths);

  const content = fs.readFileSync(paths.manualActions, 'utf8');
  const { findTables } = require('../src/markdown-table');
  const tables = findTables(content.split('\n'));
  const pending = tables.find((t) => t.rows.some((r) => r.includes(result.actionId)));
  const blocksIdx = pending.header.findIndex((h) => h.trim() === 'Blocks');
  const milestoneTaskIdx = pending.header.findIndex((h) => h.trim() === 'Milestone Task');
  const newRow = pending.rows.find((r) => r[0].trim() === result.actionId);

  assert.equal(newRow[blocksIdx].trim(), 'M2-T1');
  assert.equal(newRow[milestoneTaskIdx].trim(), '');
});

test('[defect C] aosdf_log_manual_action does not reuse an ID that exists in a table it did not target', () => {
  // Pending has MA-001 (from the fixture); this custom Completed table carries MA-002 — an
  // allocator that only scanned the Pending table (the one it's about to append to) would hand
  // out MA-002 again here, colliding with the completed record.
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'aosdf-mcp-test-'));
  fs.cpSync(FIXTURES, dir, { recursive: true });
  const manualActions = path.join(dir, 'manual_actions_collision.md');
  fs.writeFileSync(
    manualActions,
    [
      '## Pending Actions',
      '',
      '| Action ID | Description | Blocks | Status | Owner |',
      '| --------- | ------------ | ------ | ------ | ----- |',
      '| MA-001 | Existing pending | | Pending | human |',
      '',
      '## Completed Actions',
      '',
      '| Action ID | Description | Completed Date | Notes |',
      '| --------- | ------------ | --------------- | ----- |',
      '| MA-002 | Already done | 2026-01-01 | done |',
      '',
    ].join('\n')
  );

  const result = logManualAction.run({ description: 'Another one' }, { manualActions });
  assert.equal(result.actionId, 'MA-003');
});

test('[defect C] aosdf_log_manual_action rejects an explicit actionId that already exists anywhere in the file', () => {
  const paths = freshPaths();
  assert.throws(
    () => logManualAction.run({ description: 'Dup', actionId: 'MA-000' }, paths),
    /already exists/
  );
});

test('[defect C] aosdf_log_gap does not reuse an ID that exists in a second table (Resolved Gaps)', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'aosdf-mcp-test-'));
  fs.cpSync(FIXTURES, dir, { recursive: true });
  const identifiedGaps = path.join(dir, 'identified_gaps_two_tables.md');
  fs.writeFileSync(
    identifiedGaps,
    [
      '## Open Gaps',
      '',
      '| Gap ID | Category | Description | Status |',
      '| ------ | -------- | ----------- | ------ |',
      '| GAP-001 | Security | Open one | Open |',
      '',
      '## Resolved Gaps',
      '',
      '| Gap ID | Category | Description | Status |',
      '| ------ | -------- | ----------- | ------ |',
      '| GAP-002 | Security | Resolved one | Resolved |',
      '',
    ].join('\n')
  );

  const result = logGap.run({ category: 'Security', description: 'Newest' }, { identifiedGaps });
  assert.equal(result.gapId, 'GAP-003');
});

test('[defect D] aosdf_next_planned_task resumes an In Progress row instead of skipping to a later Planned one', () => {
  const paths = freshPaths();
  // E2-T1 starts Planned; move it to In Progress, matching the documented interrupted-work
  // state. E2-T2 is Done and E2-T3 is Blocked, so nothing else is Planned in this milestone.
  updateTaskStatus.run({ id: 'E2-T1', status: 'In Progress' }, paths);

  const result = nextPlannedTask.run({}, paths);
  assert.equal(result.taskId, 'E2-T1');
  assert.equal(result.resumed, true);
});

test('[defect D] aosdf_next_planned_task prefers a resumable In Progress row over an earlier-in-document Planned one', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'aosdf-mcp-test-'));
  fs.cpSync(FIXTURES, dir, { recursive: true });
  const executionPlan = path.join(dir, 'plan_resume.md');
  fs.writeFileSync(
    executionPlan,
    [
      '| Task ID | Task | Status |',
      '| ------- | ---- | ------ |',
      '| X-T1 | First  | Planned |',
      '| X-T2 | Second | In Progress |',
      '',
    ].join('\n')
  );

  const result = nextPlannedTask.run({}, { executionPlan });
  assert.equal(result.taskId, 'X-T2');
  assert.equal(result.resumed, true);
});

test('[defect E] a pipe character in a logged description no longer corrupts the table', () => {
  const paths = freshPaths();
  logGap.run({ category: 'Security', description: 'Check A | B' }, paths);

  const content = fs.readFileSync(paths.identifiedGaps, 'utf8');
  const { findTables } = require('../src/markdown-table');
  const tables = findTables(content.split('\n'));
  for (const t of tables) {
    for (const row of t.rows) assert.equal(row.length, t.header.length);
  }
  const row = tables[0].rows.find((r) => r.some((c) => c.includes('Check A')));
  assert.equal(row[tables[0].header.findIndex((h) => h.trim() === 'Description')], 'Check A | B');
});

test('[defect E] aosdf_update_task_status rejects a status outside the canonical vocabulary', () => {
  const paths = freshPaths();
  assert.throws(() => updateTaskStatus.run({ id: 'E2-T1', status: 'Banana' }, paths), /not a valid status/);
});

test('[defect E] aosdf_update_task_status still accepts canonical statuses with trailing detail', () => {
  const paths = freshPaths();
  const result = updateTaskStatus.run({ id: 'E2-T1', status: 'Done (2026-09-22)' }, paths);
  assert.equal(result.status, 'Done (2026-09-22)');
});

test('[defect G] aosdf_update_task_status leaves no leftover temp file after a write', () => {
  const paths = freshPaths();
  updateTaskStatus.run({ id: 'E2-T1', status: 'Done' }, paths);
  const dir = path.dirname(paths.executionPlan);
  const leftovers = fs.readdirSync(dir).filter((f) => f.includes('.tmp'));
  assert.deepEqual(leftovers, []);
});

test('[schema validation] the MCP server rejects a call missing a required property', () => {
  const { validateAgainstSchema } = require('../src/index');
  const err = validateAgainstSchema(updateTaskStatus.schema.inputSchema, { id: 'E2-T1' });
  assert.match(err, /Missing required property 'status'/);
});

test('[schema validation] the MCP server rejects an unknown property when additionalProperties is false', () => {
  const { validateAgainstSchema } = require('../src/index');
  const err = validateAgainstSchema(updateTaskStatus.schema.inputSchema, {
    id: 'E2-T1',
    status: 'Done',
    bogus: 'x',
  });
  assert.match(err, /Unknown property 'bogus'/);
});

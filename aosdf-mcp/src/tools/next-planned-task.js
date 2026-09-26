'use strict';

const fs = require('fs');
const { findTables, precedingHeading } = require('../markdown-table');

const TASK_ID_PATTERN = /-T\d+$/i; // e.g. E2-T1, M1-T1, ADD-<slug>-T3 — see framework.md task ID convention

const schema = {
  name: 'aosdf_next_planned_task',
  description:
    "Parses execution_plan.md and returns the task-level row (an ID matching '*-T<n>', never a " +
    "phase-level Master Sequence row) an agent should work on next, in document order. Prefers " +
    "any row whose Status is 'In Progress' over a 'Planned' one — the documented recovery path " +
    "(mark In Progress, stop safely on context exhaustion, reinvoke Commander to resume) " +
    "requires that interrupted work be picked up again before new Planned work starts, so this " +
    "tool must surface it rather than silently skipping past it to the next Planned row. The " +
    "result's `resumed` field is true when the returned row was already In Progress. Returns " +
    "null if nothing is In Progress or Planned.",
  inputSchema: {
    type: 'object',
    properties: {},
    additionalProperties: false,
  },
};

function findFirstMatch(tables, lines, statusPattern) {
  for (const table of tables) {
    const idIdx = table.header.findIndex((h) => /^(task\s*id|id)$/i.test(h.trim()));
    const statusIdx = table.header.findIndex((h) => /^status$/i.test(h.trim()));
    if (idIdx === -1 || statusIdx === -1) continue;

    for (const row of table.rows) {
      const id = (row[idIdx] || '').trim();
      const status = (row[statusIdx] || '').trim();
      if (TASK_ID_PATTERN.test(id) && statusPattern.test(status)) {
        const heading = precedingHeading(lines, table.headerLineIdx - 1);
        const taskCol = table.header.findIndex((h) => /^task$/i.test(h.trim()));
        return {
          taskId: id,
          task: taskCol !== -1 ? (row[taskCol] || '').trim() : null,
          phaseHeading: heading ? heading.text : null,
          row: Object.fromEntries(table.header.map((h, i) => [h, (row[i] || '').trim()])),
        };
      }
    }
  }
  return null;
}

function run(_args, paths) {
  const content = fs.readFileSync(paths.executionPlan, 'utf8');
  const lines = content.split('\n');
  const tables = findTables(lines);

  // Interrupted work takes priority: a row already In Progress is resumed before any Planned
  // row is started, matching the Execution Agent's documented recovery contract.
  const inProgress = findFirstMatch(tables, lines, /^in\s*progress$/i);
  if (inProgress) {
    return { path: paths.executionPlan, ...inProgress, resumed: true };
  }

  const planned = findFirstMatch(tables, lines, /^planned$/i);
  if (planned) {
    return { path: paths.executionPlan, ...planned, resumed: false };
  }

  return { path: paths.executionPlan, taskId: null, message: 'No task is currently Planned or In Progress.' };
}

module.exports = { schema, run, TASK_ID_PATTERN };

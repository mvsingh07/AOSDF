'use strict';

const fs = require('fs');
const { findTables, precedingHeading } = require('../markdown-table');

const TASK_ID_PATTERN = /-T\d+$/i; // e.g. E2-T1, M1-T1, ADD-<slug>-T3 — see framework.md task ID convention

const schema = {
  name: 'aosdf_next_planned_task',
  description:
    "Parses execution_plan.md and returns the first task-level row (an ID matching '*-T<n>', " +
    "never a phase-level Master Sequence row) whose Status is exactly 'Planned', in document " +
    'order. Returns null if no task is currently Planned.',
  inputSchema: {
    type: 'object',
    properties: {},
    additionalProperties: false,
  },
};

function run(_args, paths) {
  const content = fs.readFileSync(paths.executionPlan, 'utf8');
  const lines = content.split('\n');
  const tables = findTables(lines);

  for (const table of tables) {
    const idIdx = table.header.findIndex((h) => /^(task\s*id|id)$/i.test(h.trim()));
    const statusIdx = table.header.findIndex((h) => /^status$/i.test(h.trim()));
    if (idIdx === -1 || statusIdx === -1) continue;

    for (const row of table.rows) {
      const id = (row[idIdx] || '').trim();
      const status = (row[statusIdx] || '').trim();
      if (TASK_ID_PATTERN.test(id) && /^planned$/i.test(status)) {
        const heading = precedingHeading(lines, table.headerLineIdx - 1);
        const taskCol = table.header.findIndex((h) => /^task$/i.test(h.trim()));
        return {
          path: paths.executionPlan,
          taskId: id,
          task: taskCol !== -1 ? (row[taskCol] || '').trim() : null,
          phaseHeading: heading ? heading.text : null,
          row: Object.fromEntries(table.header.map((h, i) => [h, (row[i] || '').trim()])),
        };
      }
    }
  }

  return { path: paths.executionPlan, taskId: null, message: 'No task is currently Planned.' };
}

module.exports = { schema, run, TASK_ID_PATTERN };

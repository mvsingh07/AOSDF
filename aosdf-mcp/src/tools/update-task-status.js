'use strict';

const { readLines, writeLines } = require('../fileio');
const { findTables, replaceManyTables } = require('../markdown-table');

// The framework's canonical task-status vocabulary (framework.md / templates.md). A value is
// accepted if it starts with one of these words, optionally followed by free text — e.g.
// "Done (2026-08-27)" or "Cancelled — scope cut" are both valid, but an arbitrary string like
// "Banana" is not. Without this, nothing stopped a bad status from being written and silently
// treated as neither Planned, In Progress, Done, Blocked nor Cancelled by every other tool.
const VALID_STATUS_WORDS = ['Planned', 'In Progress', 'Done', 'Blocked', 'Cancelled'];
const VALID_STATUS_PATTERN = new RegExp(`^(${VALID_STATUS_WORDS.join('|')})\\b`, 'i');

function isValidStatus(status) {
  return VALID_STATUS_PATTERN.test(status.trim());
}

const schema = {
  name: 'aosdf_update_task_status',
  description:
    "Writes execution_plan.md's Status column for every row whose first column exactly " +
    "matches `id` (a task like 'E2-T1' or a phase like 'E2') to `status`. Format-standard-safe: " +
    'recomputes column widths and re-pads every row in the affected table(s), never hand-edits ' +
    'a single cell in place. This is the only tool allowed to write execution_plan.md.',
  inputSchema: {
    type: 'object',
    properties: {
      id: { type: 'string', description: "Exact ID in the table's first column, e.g. 'E2-T1'." },
      status: {
        type: 'string',
        description: "New Status cell value, e.g. 'Done (2026-08-27)' or 'In Progress'.",
      },
    },
    required: ['id', 'status'],
    additionalProperties: false,
  },
};

function run(args, paths) {
  const { id, status } = args;
  if (!id || !status) throw new Error("Both 'id' and 'status' are required.");
  if (!isValidStatus(status)) {
    throw new Error(
      `'${status}' is not a valid status. It must start with one of: ${VALID_STATUS_WORDS.join(', ')}.`
    );
  }

  const { lines, trailingNewline } = readLines(paths.executionPlan);
  const tables = findTables(lines);

  const edits = [];
  const matches = [];

  for (const table of tables) {
    const statusIdx = table.header.findIndex((h) => /^status$/i.test(h.trim()));
    // The ID column isn't always column 0 — the Master Sequence table's ID column
    // is "Phase ID" in the second position, with "Stage" first. Match by header
    // name, not position.
    const idIdx = table.header.findIndex((h) => /^(task\s*id|phase\s*id|id)$/i.test(h.trim()));
    if (statusIdx === -1 || idIdx === -1) continue;

    let touched = false;
    const newRows = table.rows.map((row) => {
      if ((row[idIdx] || '').trim() === id) {
        touched = true;
        const updated = [...row];
        updated[statusIdx] = status;
        matches.push({ id, from: row[statusIdx], to: status });
        return updated;
      }
      return row;
    });

    if (touched) edits.push({ table, header: table.header, rows: newRows });
  }

  if (edits.length === 0) {
    throw new Error(`No row with ID '${id}' found in ${paths.executionPlan}.`);
  }

  const newLines = replaceManyTables(lines, edits);
  writeLines(paths.executionPlan, newLines, trailingNewline);

  return { path: paths.executionPlan, id, status, tablesUpdated: edits.length, matches };
}

module.exports = { schema, run };

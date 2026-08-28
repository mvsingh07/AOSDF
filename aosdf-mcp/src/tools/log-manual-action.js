'use strict';

const { readLines, writeLines } = require('../fileio');
const { findTables, replaceManyTables, precedingHeading } = require('../markdown-table');
const { nextSequentialId } = require('../next-id');

const schema = {
  name: 'aosdf_log_manual_action',
  description:
    "Appends one row to 12_Manual_Actions/actions.md's Pending Actions table (or, for a " +
    'project that documents a one-file deviation like this meta-project\'s own ' +
    "manual_actions.md, its single Actions table). Auto-generates the next MA-N ID. Never " +
    'defer logging a manual action — Principle 8.',
  inputSchema: {
    type: 'object',
    properties: {
      description: { type: 'string' },
      category: { type: 'string', description: 'Cloud | Compliance | Credentials | DNS | Other' },
      priority: { type: 'string', description: 'P1 | P2 | P3' },
      unblocks: { type: 'string', description: 'Task/milestone this action unblocks once done.' },
      owner: { type: 'string' },
      actionId: { type: 'string', description: 'Override the auto-generated MA-N ID.' },
    },
    required: ['description'],
    additionalProperties: false,
  },
};

function pickTargetTable(tables, lines) {
  const withHeadings = tables.map((t) => ({
    table: t,
    heading: precedingHeading(lines, t.headerLineIdx - 1),
  }));

  const pending = withHeadings.find((t) => t.heading && /pending/i.test(t.heading.text));
  if (pending) return pending.table;

  if (tables.length === 1) return tables[0];

  const withStatus = tables.find((t) => t.header.some((h) => /^status$/i.test(h.trim())));
  if (withStatus) return withStatus;

  return tables[0];
}

function run(args, paths) {
  const { description, category = '', priority = '', unblocks = '', owner = '', actionId } = args;
  if (!description) throw new Error("'description' is required.");

  const { lines, trailingNewline } = readLines(paths.manualActions);
  const tables = findTables(lines);
  if (tables.length === 0) throw new Error(`No table found in ${paths.manualActions}.`);

  const table = pickTargetTable(tables, lines);
  const colIdx = (pattern) => table.header.findIndex((h) => pattern.test(h.trim()));

  const idIdx = colIdx(/^(action\s*id|id)$/i);
  const descIdx = colIdx(/^description$/i);
  const catIdx = colIdx(/^category$/i);
  const priorityIdx = colIdx(/^priority$/i);
  const unblocksIdx = colIdx(/^(unblocks|blocks|milestone\s*task)$/i);
  const statusIdx = colIdx(/^(status|dev\s*status)$/i);
  const ownerIdx = colIdx(/^owner$/i);

  const existingIds = idIdx !== -1 ? table.rows.map((r) => r[idIdx]) : [];
  const newId = actionId || nextSequentialId(existingIds, 'MA', 1);

  const newRow = new Array(table.header.length).fill('');
  if (idIdx !== -1) newRow[idIdx] = newId;
  if (descIdx !== -1) newRow[descIdx] = description;
  if (catIdx !== -1) newRow[catIdx] = category;
  if (priorityIdx !== -1) newRow[priorityIdx] = priority;
  if (unblocksIdx !== -1) newRow[unblocksIdx] = unblocks;
  if (statusIdx !== -1) newRow[statusIdx] = 'Pending';
  if (ownerIdx !== -1) newRow[ownerIdx] = owner;

  const newRows = [...table.rows, newRow];
  const newLines = replaceManyTables(lines, [{ table, header: table.header, rows: newRows }]);
  writeLines(paths.manualActions, newLines, trailingNewline);

  return { path: paths.manualActions, actionId: newId };
}

module.exports = { schema, run };

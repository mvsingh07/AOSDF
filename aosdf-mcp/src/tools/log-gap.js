'use strict';

const { readLines, writeLines } = require('../fileio');
const { findTables, replaceManyTables } = require('../markdown-table');
const { nextSequentialId } = require('../next-id');

const schema = {
  name: 'aosdf_log_gap',
  description:
    'Appends one row to identified_gaps.md (templates.md convention: Gap ID | Category | ' +
    'Description | Severity | Status | Owner | Identified | Resolution). Auto-generates the ' +
    'next GAP-NNN ID and today\'s Identified date unless overridden. Column matching is by ' +
    "header name, so a project's exact column set doesn't need to match the template verbatim.",
  inputSchema: {
    type: 'object',
    properties: {
      category: {
        type: 'string',
        description: 'Security | Architecture | Infrastructure | Documentation | Compliance | Performance',
      },
      description: { type: 'string' },
      severity: { type: 'string', description: 'Critical | High | Medium | Low', default: 'Medium' },
      owner: { type: 'string' },
      gapId: { type: 'string', description: 'Override the auto-generated GAP-NNN ID.' },
    },
    required: ['category', 'description'],
    additionalProperties: false,
  },
};

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function run(args, paths) {
  const { category, description, severity = 'Medium', owner = '', gapId } = args;
  if (!category || !description) throw new Error("Both 'category' and 'description' are required.");

  const { lines, trailingNewline } = readLines(paths.identifiedGaps);
  const tables = findTables(lines);
  if (tables.length === 0) throw new Error(`No table found in ${paths.identifiedGaps}.`);

  const table = tables[0];
  const colIdx = (pattern) => table.header.findIndex((h) => pattern.test(h.trim()));

  const idIdx = colIdx(/^gap\s*id$/i);
  const catIdx = colIdx(/^category$/i);
  const descIdx = colIdx(/^description$/i);
  const sevIdx = colIdx(/^severity$/i);
  const statusIdx = colIdx(/^status$/i);
  const ownerIdx = colIdx(/^owner$/i);
  const identifiedIdx = colIdx(/^identified$/i);
  const resolutionIdx = colIdx(/^resolution$/i);

  const existingIds = idIdx !== -1 ? table.rows.map((r) => r[idIdx]) : [];
  const newId = gapId || nextSequentialId(existingIds, 'GAP', 3);

  const newRow = new Array(table.header.length).fill('');
  if (idIdx !== -1) newRow[idIdx] = newId;
  if (catIdx !== -1) newRow[catIdx] = category;
  if (descIdx !== -1) newRow[descIdx] = description;
  if (sevIdx !== -1) newRow[sevIdx] = severity;
  if (statusIdx !== -1) newRow[statusIdx] = 'Open';
  if (ownerIdx !== -1) newRow[ownerIdx] = owner;
  if (identifiedIdx !== -1) newRow[identifiedIdx] = todayIso();
  if (resolutionIdx !== -1) newRow[resolutionIdx] = '';

  const newRows = [...table.rows, newRow];
  const newLines = replaceManyTables(lines, [{ table, header: table.header, rows: newRows }]);
  writeLines(paths.identifiedGaps, newLines, trailingNewline);

  return { path: paths.identifiedGaps, gapId: newId };
}

module.exports = { schema, run };

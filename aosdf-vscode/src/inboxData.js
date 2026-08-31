'use strict';

// Reads identified_gaps.md and manual_actions.md directly (aosdf-mcp, E2-T1,
// exposes only append tools for these two files — aosdf_log_gap and
// aosdf_log_manual_action — no list tool). This still respects Principle 26:
// nothing here is cached across calls, the files stay the only source of
// truth, and every refresh re-reads and re-parses from disk. Reuses
// aosdf-mcp's own path resolution and table parser rather than duplicating
// either.

const fs = require('fs');
const { resolvePaths } = require('../../aosdf-mcp/src/config');
const { findTables } = require('../../aosdf-mcp/src/markdown-table');

const CLOSED_STATUS = /^(done|resolved|closed|cancelled|n\/a)\b/i;

function isPlaceholderId(id) {
  const trimmed = (id || '').trim();
  return trimmed === '' || trimmed.startsWith('_(') || trimmed.startsWith('(');
}

// Returns every open (non-closed, non-placeholder) row from any table in
// `filePath` whose header matches both an ID column (per `idHeaderPattern`)
// and a `Status` column. Tables without a Status column (e.g. a "Completed
// Actions" archive table) are skipped entirely rather than guessed at.
function readOpenRows(filePath, idHeaderPattern) {
  if (!fs.existsSync(filePath)) return [];
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const tables = findTables(lines);
  const items = [];

  for (const table of tables) {
    const idIdx = table.header.findIndex((h) => idHeaderPattern.test(h.trim()));
    const statusIdx = table.header.findIndex((h) => /^status$/i.test(h.trim()));
    const descIdx = table.header.findIndex((h) => /^description$/i.test(h.trim()));
    if (idIdx === -1 || statusIdx === -1) continue;

    table.rows.forEach((row, rowIdx) => {
      const id = (row[idIdx] || '').trim();
      const status = (row[statusIdx] || '').trim();
      if (isPlaceholderId(id) || CLOSED_STATUS.test(status)) return;
      items.push({
        id,
        status: status || '(no status)',
        description: descIdx !== -1 ? (row[descIdx] || '').trim() : '',
        line: table.sepLineIdx + 1 + rowIdx,
      });
    });
  }

  return items;
}

function readInbox(documentsRoot) {
  const paths = resolvePaths(documentsRoot);
  const gaps = readOpenRows(paths.identifiedGaps, /^(gap\s*id|id)$/i).map((item) => ({
    ...item,
    kind: 'gap',
    file: paths.identifiedGaps,
  }));
  const actions = readOpenRows(paths.manualActions, /^(action\s*id|id)$/i).map((item) => ({
    ...item,
    kind: 'manual-action',
    file: paths.manualActions,
  }));
  return { gaps, actions };
}

module.exports = { readInbox, readOpenRows, isPlaceholderId, CLOSED_STATUS };

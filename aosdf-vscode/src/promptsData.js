'use strict';

// Reads implementation_prompts/README.md's Log table directly (aosdf-mcp exposes
// no tool for it at all — it's populated by execution_agent.md/superman_agent.md,
// E5-T1, not by any MCP tool). Same discipline as inboxData.js: no caching, the
// file stays the only record, re-read on every call.

const fs = require('fs');
const path = require('path');
const { resolvePaths } = require('../../aosdf-mcp/src/config');
const { findTables } = require('../../aosdf-mcp/src/markdown-table');

const EXECUTED_STATUS = /^executed\b/i;

// Rows whose Status doesn't start with "Executed" — i.e. still `Pending Approval`
// (or a project-specific variant of it). A row missing a Status cell entirely is
// treated as pending rather than silently dropped.
function readPendingPrompts(documentsRoot) {
  const paths = resolvePaths(documentsRoot);
  const indexPath = paths.implementationPromptsIndex;
  if (!fs.existsSync(indexPath)) return [];

  const content = fs.readFileSync(indexPath, 'utf8');
  const lines = content.split('\n');
  const tables = findTables(lines);
  if (tables.length === 0) return [];

  const table = tables[0];
  const fileIdx = table.header.findIndex((h) => /^prompt\s*file$/i.test(h.trim()));
  const taskIdx = table.header.findIndex((h) => /^task$/i.test(h.trim()));
  const statusIdx = table.header.findIndex((h) => /^status$/i.test(h.trim()));
  if (fileIdx === -1) return [];

  const promptsDir = path.dirname(indexPath);
  const pending = [];

  table.rows.forEach((row, rowIdx) => {
    const fileName = (row[fileIdx] || '').trim();
    if (!fileName) return;
    const status = statusIdx !== -1 ? (row[statusIdx] || '').trim() : '';
    if (EXECUTED_STATUS.test(status)) return;
    pending.push({
      fileName,
      task: taskIdx !== -1 ? (row[taskIdx] || '').trim() : '',
      status: status || 'Pending Approval',
      promptPath: path.join(promptsDir, fileName),
      line: table.sepLineIdx + 1 + rowIdx,
      indexPath,
    });
  });

  return pending;
}

module.exports = { readPendingPrompts, EXECUTED_STATUS };

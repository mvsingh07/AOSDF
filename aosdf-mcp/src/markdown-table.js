'use strict';

// Implements AOSDF's Document Formatting Standard (manual.md, framework.md):
//   1. Separator dashes match the widest value in each column.
//   2. Data cells are padded with trailing spaces to fill column width.
// Every tool that writes back to a markdown file goes through renderTable()
// so no write ever produces a table that violates the standard.

function splitRow(line) {
  let trimmed = line.trim();
  if (trimmed.startsWith('|')) trimmed = trimmed.slice(1);
  if (trimmed.endsWith('|')) trimmed = trimmed.slice(0, -1);
  // Split on unescaped pipes only — a literal '|' inside a cell must be written as '\|'
  // (see sanitizeCell) or it would otherwise be mistaken for a column boundary and shift
  // every later cell in the row one column to the right.
  return trimmed
    .split(/(?<!\\)\|/)
    .map((cell) => cell.trim().replace(/\\\|/g, '|'));
}

// Makes a value safe to place inside a single markdown table cell: escapes literal '|'
// characters (which would otherwise be parsed as a column boundary on the next read) and
// collapses newlines to a space (a raw newline would break out of the row entirely).
function sanitizeCell(value) {
  return String(value == null ? '' : value)
    .replace(/\r?\n/g, ' ')
    .replace(/\|/g, '\\|');
}

function isSeparatorLine(line) {
  const trimmed = line.trim();
  if (!trimmed.startsWith('|')) return false;
  return /^\|?[\s:|-]+\|?$/.test(trimmed) && trimmed.includes('-');
}

// Scans `lines` (an array, one entry per source line) for every markdown
// table and returns their location + parsed content. A table is any run of
// lines starting with '|' whose second line is a separator row.
function findTables(lines) {
  const tables = [];
  let i = 0;
  while (i < lines.length) {
    if (
      lines[i].trim().startsWith('|') &&
      i + 1 < lines.length &&
      isSeparatorLine(lines[i + 1])
    ) {
      const headerLineIdx = i;
      const sepLineIdx = i + 1;
      const header = splitRow(lines[headerLineIdx]);
      let j = sepLineIdx + 1;
      const rows = [];
      while (j < lines.length && lines[j].trim().startsWith('|')) {
        rows.push(splitRow(lines[j]));
        j++;
      }
      tables.push({ headerLineIdx, sepLineIdx, header, rows, endLineIdx: j });
      i = j;
    } else {
      i++;
    }
  }
  return tables;
}

function colWidths(header, rows) {
  const n = header.length;
  const widths = new Array(n).fill(0);
  for (let c = 0; c < n; c++) widths[c] = (header[c] || '').length;
  for (const row of rows) {
    for (let c = 0; c < n; c++) {
      const v = row[c] || '';
      if (v.length > widths[c]) widths[c] = v.length;
    }
  }
  return widths;
}

function renderRow(cells, widths) {
  const padded = widths.map((w, idx) => (cells[idx] || '').padEnd(w));
  return '| ' + padded.join(' | ') + ' |';
}

function renderSeparator(widths) {
  return '| ' + widths.map((w) => '-'.repeat(Math.max(w, 1))).join(' | ') + ' |';
}

// Renders a full table (header + rows) as an array of formatted lines. Every cell is run
// through sanitizeCell() first so a value containing '|' or a newline can never corrupt the
// table structure on the next parse — this is the only path tools use to write a table, so
// this guarantee applies to every write regardless of which tool produced the value.
function renderTable(header, rows) {
  const safeHeader = header.map(sanitizeCell);
  const safeRows = rows.map((row) => row.map(sanitizeCell));
  const widths = colWidths(safeHeader, safeRows);
  const lines = [renderRow(safeHeader, widths), renderSeparator(widths)];
  for (const row of safeRows) lines.push(renderRow(row, widths));
  return lines;
}

// Finds the nearest markdown heading (e.g. "## Next Action") at or above
// `lineIdx`, at or above the given minimum '#' level (1 = any heading).
function precedingHeading(lines, lineIdx) {
  for (let i = lineIdx; i >= 0; i--) {
    const m = lines[i].match(/^(#{1,6})\s+(.*)$/);
    if (m) return { level: m[1].length, text: m[2].trim(), lineIdx: i };
  }
  return null;
}

// Replaces one table's line range in `lines` with a freshly formatted
// render of (newHeader, newRows). Does not touch any other line.
function replaceTableRows(lines, table, newHeader, newRows) {
  const rendered = renderTable(newHeader, newRows);
  return [...lines.slice(0, table.headerLineIdx), ...rendered, ...lines.slice(table.endLineIdx)];
}

// Applies several table replacements to the same `lines` array in one pass.
// `edits` is [{ table, header, rows }]. Safe regardless of input order —
// internally applies bottom-most table first so earlier line indices never
// shift out from under a not-yet-applied edit.
function replaceManyTables(lines, edits) {
  const sorted = [...edits].sort((a, b) => b.table.headerLineIdx - a.table.headerLineIdx);
  let result = lines;
  for (const edit of sorted) {
    result = replaceTableRows(result, edit.table, edit.header, edit.rows);
  }
  return result;
}

module.exports = {
  splitRow,
  isSeparatorLine,
  findTables,
  colWidths,
  renderRow,
  renderSeparator,
  renderTable,
  sanitizeCell,
  precedingHeading,
  replaceTableRows,
  replaceManyTables,
};

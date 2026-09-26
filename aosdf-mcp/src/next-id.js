'use strict';

// Given existing IDs like ["GAP-001", "GAP-002"] or ["MA-1", "MA-2", "MA-4"], returns the
// next sequential ID in the same style — same zero-padding width as the highest existing ID,
// or 3-digit padding (matching AOSDF's canonical templates.md example) if none exist yet.
function nextSequentialId(existingIds, prefix, defaultWidth = 3) {
  const pattern = new RegExp(`^${prefix}-(\\d+)$`, 'i');
  let maxNum = 0;
  let width = 0;
  for (const id of existingIds) {
    const m = String(id).trim().match(pattern);
    if (m) {
      const num = parseInt(m[1], 10);
      if (num > maxNum) {
        maxNum = num;
        width = m[1].length;
      }
    }
  }
  const w = width || defaultWidth;
  return `${prefix}-${String(maxNum + 1).padStart(w, '0')}`;
}

// Collects every value found under a matching column across ALL of a file's tables, not just
// the one a tool is about to write to. An allocator that only scanned the "current" table (e.g.
// just the Pending table) could hand out an ID already used by a row sitting in a Completed or
// Resolved table elsewhere in the same file, since it never saw that table's IDs at all.
function collectIds(tables, idColPattern) {
  const ids = [];
  for (const table of tables) {
    const idIdx = table.header.findIndex((h) => idColPattern.test(h.trim()));
    if (idIdx === -1) continue;
    for (const row of table.rows) {
      const v = (row[idIdx] || '').trim();
      if (v) ids.push(v);
    }
  }
  return ids;
}

module.exports = { nextSequentialId, collectIds };

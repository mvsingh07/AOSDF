'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Splits on '\n' and remembers whether the file ended with a trailing
// newline, so writeLines() can reproduce it exactly — a write that silently
// added or dropped the final newline is exactly the kind of incidental diff
// noise this tool must never introduce into a file three other agents read.
function readLines(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const trailingNewline = content.endsWith('\n');
  const body = trailingNewline ? content.slice(0, -1) : content;
  return { lines: body.split('\n'), trailingNewline };
}

// Writes via a same-directory temp file + atomic rename instead of a direct writeFileSync,
// so a process interrupted mid-write (or a concurrent writer) can never leave the target file
// half-written or torn — readers always see either the old content or the fully-new content.
// rename() is atomic only within the same filesystem, hence the temp file living next to the
// target rather than in the OS temp dir. This does not add cross-process locking — it only
// removes the "partial write" failure mode of a single writeFileSync call.
function writeLines(filePath, lines, trailingNewline) {
  const content = lines.join('\n') + (trailingNewline ? '\n' : '');
  const dir = path.dirname(filePath);
  const tmpPath = path.join(dir, `.${path.basename(filePath)}.${process.pid}-${crypto.randomBytes(4).toString('hex')}.tmp`);
  fs.writeFileSync(tmpPath, content, 'utf8');
  fs.renameSync(tmpPath, filePath);
}

module.exports = { readLines, writeLines };

'use strict';

const fs = require('fs');

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

function writeLines(filePath, lines, trailingNewline) {
  const content = lines.join('\n') + (trailingNewline ? '\n' : '');
  fs.writeFileSync(filePath, content, 'utf8');
}

module.exports = { readLines, writeLines };

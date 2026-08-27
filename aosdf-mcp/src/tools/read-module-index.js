'use strict';

const fs = require('fs');
const { findTables } = require('../markdown-table');

const schema = {
  name: 'aosdf_read_module_index',
  description:
    "Parses 03_System_Design/README.md and returns its module index table (the NNN_<name>_module " +
    "registry architect_agent claims the next free number from) as structured rows, plus the " +
    "raw file content. Returns an empty rows array if no table exists yet (a fresh project).",
  inputSchema: {
    type: 'object',
    properties: {},
    additionalProperties: false,
  },
};

function run(_args, paths) {
  const content = fs.readFileSync(paths.moduleIndex, 'utf8');
  const lines = content.split('\n');
  const tables = findTables(lines);

  if (tables.length === 0) {
    return { path: paths.moduleIndex, header: [], rows: [], raw: content };
  }

  const table = tables[0];
  return {
    path: paths.moduleIndex,
    header: table.header,
    rows: table.rows.map((row) => Object.fromEntries(table.header.map((h, i) => [h, (row[i] || '').trim()]))),
    raw: content,
  };
}

module.exports = { schema, run };

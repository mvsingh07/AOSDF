#!/usr/bin/env node
'use strict';

// [v3.0, E6-T1] CLI wrapper around lint.js. Zero runtime dependencies
// (Principle 30) — argument parsing and output are hand-rolled.
//
// Usage:
//   node src/lint-cli.js <root> [--fix] [--quiet]
//
// Exit codes: 0 = clean (or --fix applied and nothing remains non-compliant
// after fixing, which is always true since fixContent() is exhaustive for
// Rules 1-2). 1 = violations found and --fix was not passed. 2 = usage error.

const path = require('path');
const { lintTree, fixTree } = require('./lint');

function main(argv) {
  const args = argv.slice(2);
  const positional = args.filter((a) => !a.startsWith('--'));
  const fix = args.includes('--fix');
  const quiet = args.includes('--quiet');

  if (positional.length !== 1) {
    process.stderr.write('Usage: aosdf-lint <root> [--fix] [--quiet]\n');
    return 2;
  }

  const root = path.resolve(positional[0]);

  if (fix) {
    const changed = fixTree(root);
    if (!quiet) {
      if (changed.length === 0) {
        console.log('aosdf-lint: nothing to fix, already compliant.');
      } else {
        console.log(`aosdf-lint: fixed ${changed.length} file(s):`);
        for (const file of changed) console.log(`  ${path.relative(root, file)}`);
      }
    }
    return 0;
  }

  const report = lintTree(root);
  if (report.length === 0) {
    if (!quiet) console.log('aosdf-lint: clean — every table is Document Formatting Standard compliant.');
    return 0;
  }

  if (!quiet) {
    let totalViolations = 0;
    for (const { file, violations } of report) {
      for (const v of violations) {
        totalViolations++;
        console.log(`${path.relative(root, file)}:${v.line}: table is not Document Formatting Standard compliant (Rule 1/2)`);
      }
    }
    console.log(`\naosdf-lint: ${totalViolations} violation(s) across ${report.length} file(s). Run with --fix to correct them.`);
  }
  return 1;
}

if (require.main === module) {
  process.exit(main(process.argv));
}

module.exports = { main };

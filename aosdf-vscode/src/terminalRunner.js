'use strict';

// E5-T1's "invoke from the command surface" / "approve inline" / "trigger tracker
// sync" all reduce to the same primitive: reveal a named integrated terminal and
// type text into it. This performs no file write of its own — whatever actually
// changes on disk happens inside the Claude Code session running in that terminal,
// through its own agents' normal Permissions, exactly as if the human had typed
// the same text by hand. That's what keeps this Principle-26-safe: the extension
// never bypasses aosdf-mcp (or an agent's own file-write path) with a direct write.

const vscode = require('vscode');

const TERMINAL_NAME = 'AOSDF';

// [v3.0, E6-T2] `folder` is optional — omitting it reproduces the original
// single-workspace behavior exactly (one terminal named 'AOSDF', cwd left to
// VS Code's own default). Only multi-root callers pass a folder, so a
// single-workspace project never sees a naming/cwd change from this.
function getOrCreateTerminal(folder) {
  const name = folder ? `AOSDF: ${folder.name}` : TERMINAL_NAME;
  const existing = vscode.window.terminals.find((t) => t.name === name);
  if (existing) return existing;
  return folder ? vscode.window.createTerminal({ name, cwd: folder.uri }) : vscode.window.createTerminal(name);
}

function sendToTerminal(text, folder) {
  const terminal = getOrCreateTerminal(folder);
  terminal.show();
  terminal.sendText(text, true);
}

module.exports = { sendToTerminal, TERMINAL_NAME };

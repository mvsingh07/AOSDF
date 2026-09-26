#!/usr/bin/env node
'use strict';

// aosdf-mcp — an MCP server exposing exactly six read/write tools over AOSDF's own markdown
// files (aosdf_expansion_scope.md Sec 4.2, SR-4). Every tool reads or writes a file that is
// already authoritative on disk; this process holds no state of its own and caches nothing
// across calls (Principle 26) — restart it any time with zero loss.
//
// Transport: MCP's stdio transport (session-scoped, one process per editor/CLI session,
// per infra_architecture.md). Messages are newline-delimited JSON-RPC 2.0, per the MCP spec.
// Implemented by hand, with no runtime dependencies, so this package stays consistent with
// AOSDF's own zero-dependency discipline (Principle 30) and never blocks on `npm install`
// reaching a registry from a sandboxed or offline session.

const readline = require('readline');
const { resolveDocsRoot, resolvePaths } = require('./config');

const readStatus = require('./tools/read-status');
const nextPlannedTask = require('./tools/next-planned-task');
const updateTaskStatus = require('./tools/update-task-status');
const logGap = require('./tools/log-gap');
const logManualAction = require('./tools/log-manual-action');
const readModuleIndex = require('./tools/read-module-index');

const TOOLS = [readStatus, nextPlannedTask, updateTaskStatus, logGap, logManualAction, readModuleIndex];
const SERVER_NAME = 'aosdf-mcp';
const SERVER_VERSION = require('../package.json').version;

function send(message) {
  process.stdout.write(JSON.stringify(message) + '\n');
}

function sendResult(id, result) {
  send({ jsonrpc: '2.0', id, result });
}

function sendError(id, code, message) {
  send({ jsonrpc: '2.0', id, error: { code, message } });
}

function handleInitialize(id) {
  sendResult(id, {
    protocolVersion: '2024-11-05',
    capabilities: { tools: {} },
    serverInfo: { name: SERVER_NAME, version: SERVER_VERSION },
  });
}

function handleToolsList(id) {
  sendResult(id, { tools: TOOLS.map((t) => t.schema) });
}

// Checks `args` against the tool's own declared JSON-schema `inputSchema` before the tool ever
// runs: every `required` property must be present, every property present must match its
// declared `type`, and if the schema says `additionalProperties: false` no unknown property may
// be passed. This is intentionally a narrow structural check (not a full JSON-schema
// implementation) — it exists so a malformed call fails fast with a clear message instead of a
// tool silently writing whatever it was given, which is how e.g. an arbitrary task status used
// to reach disk unchecked.
function validateAgainstSchema(inputSchema, args) {
  if (!inputSchema || typeof inputSchema !== 'object') return null;
  const { properties = {}, required = [], additionalProperties } = inputSchema;

  for (const key of required) {
    if (!(key in args) || args[key] === undefined || args[key] === null || args[key] === '') {
      return `Missing required property '${key}'.`;
    }
  }

  if (additionalProperties === false) {
    for (const key of Object.keys(args)) {
      if (!(key in properties)) return `Unknown property '${key}' is not accepted by this tool.`;
    }
  }

  for (const [key, value] of Object.entries(args)) {
    const propSchema = properties[key];
    if (!propSchema || value === undefined) continue;
    const expected = propSchema.type;
    if (!expected) continue;
    const actual = Array.isArray(value) ? 'array' : typeof value;
    if (actual !== expected) {
      return `Property '${key}' must be of type '${expected}', got '${actual}'.`;
    }
  }

  return null;
}

function handleToolsCall(id, params, paths) {
  const { name, arguments: args = {} } = params || {};
  const tool = TOOLS.find((t) => t.schema.name === name);
  if (!tool) {
    sendError(id, -32602, `Unknown tool: ${name}`);
    return;
  }
  const validationError = validateAgainstSchema(tool.schema.inputSchema, args);
  if (validationError) {
    sendResult(id, { content: [{ type: 'text', text: validationError }], isError: true });
    return;
  }
  try {
    const result = tool.run(args, paths);
    sendResult(id, { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] });
  } catch (err) {
    // Tool-level failures (bad ID, missing file, bad args) are reported as a
    // successful JSON-RPC response with isError: true, per the MCP spec —
    // a JSON-RPC error is reserved for protocol-level problems.
    sendResult(id, { content: [{ type: 'text', text: err.message }], isError: true });
  }
}

function main() {
  const root = resolveDocsRoot();
  const paths = resolvePaths(root);

  const rl = readline.createInterface({ input: process.stdin, terminal: false });

  rl.on('line', (line) => {
    const trimmed = line.trim();
    if (!trimmed) return;

    let message;
    try {
      message = JSON.parse(trimmed);
    } catch {
      return; // Not a valid JSON-RPC frame — nothing we can address a response to.
    }

    const { id, method, params } = message;

    switch (method) {
      case 'initialize':
        handleInitialize(id);
        break;
      case 'notifications/initialized':
        break; // Notification — no response expected.
      case 'tools/list':
        handleToolsList(id);
        break;
      case 'tools/call':
        handleToolsCall(id, params, paths);
        break;
      case 'ping':
        sendResult(id, {});
        break;
      default:
        if (id !== undefined) sendError(id, -32601, `Method not found: ${method}`);
    }
  });
}

if (require.main === module) {
  main();
}

module.exports = { TOOLS, validateAgainstSchema };

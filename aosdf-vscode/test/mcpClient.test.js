'use strict';

// Integration test: spawns the real aosdf-mcp server (E2-T1) as a subprocess
// against its own fixture docs root, exactly as the extension does against a
// real project. Verifies the client's JSON-RPC framing round-trips real tool
// calls, not just mocked ones.

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');
const { McpClient } = require('../src/mcpClient');

const SERVER_PATH = path.join(__dirname, '..', '..', 'aosdf-mcp', 'src', 'index.js');
const FIXTURES = path.join(__dirname, '..', '..', 'aosdf-mcp', 'test', 'fixtures');

test('McpClient initializes and calls aosdf_read_status against the real server', async () => {
  const client = new McpClient(SERVER_PATH, { AOSDF_DOCS_ROOT: FIXTURES });
  try {
    const init = await client.initialize();
    assert.equal(init.serverInfo.name, 'aosdf-mcp');
    const status = await client.callTool('aosdf_read_status');
    assert.equal(status.currentState, 'PLANNING');
  } finally {
    client.stop();
  }
});

test('McpClient calls aosdf_next_planned_task and gets the fixture\'s Planned task', async () => {
  const client = new McpClient(SERVER_PATH, { AOSDF_DOCS_ROOT: FIXTURES });
  try {
    await client.initialize();
    const task = await client.callTool('aosdf_next_planned_task');
    assert.equal(task.taskId, 'E2-T1');
  } finally {
    client.stop();
  }
});

test('McpClient surfaces a tool-level error (isError) as a rejected promise', async () => {
  const client = new McpClient(SERVER_PATH, { AOSDF_DOCS_ROOT: FIXTURES });
  try {
    await client.initialize();
    await assert.rejects(() => client.callTool('aosdf_update_task_status', { id: 'NOPE-T1', status: 'Done' }));
  } finally {
    client.stop();
  }
});

test('multiple calls on one client do not cross-respond (ids stay matched)', async () => {
  const client = new McpClient(SERVER_PATH, { AOSDF_DOCS_ROOT: FIXTURES });
  try {
    await client.initialize();
    const [status, task] = await Promise.all([
      client.callTool('aosdf_read_status'),
      client.callTool('aosdf_next_planned_task'),
    ]);
    assert.equal(status.currentState, 'PLANNING');
    assert.equal(task.taskId, 'E2-T1');
  } finally {
    client.stop();
  }
});

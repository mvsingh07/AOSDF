'use strict';

// A minimal MCP stdio client: spawns aosdf-mcp (E2-T1) as a child process and
// speaks the same newline-delimited JSON-RPC 2.0 protocol its own src/index.js
// implements. No caching of tool results across calls — every call is a fresh
// round trip to the server, which itself re-reads the underlying file on every
// call (Principle 26). Zero runtime dependencies, matching the rest of AOSDF's
// JS tooling (Principle 30).

const { spawn } = require('child_process');
const readline = require('readline');

class McpClient {
  constructor(serverPath, env = {}) {
    this.serverPath = serverPath;
    this.env = env;
    this.child = null;
    this.rl = null;
    this.nextId = 1;
    this.pending = new Map();
  }

  _ensureStarted() {
    if (this.child) return;
    this.child = spawn(process.execPath, [this.serverPath], {
      env: { ...process.env, ...this.env },
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    this.rl = readline.createInterface({ input: this.child.stdout, terminal: false });
    this.rl.on('line', (line) => this._handleLine(line));
    this.child.on('exit', () => this._rejectAllPending(new Error('aosdf-mcp server exited')));
    this.child.on('error', (err) => this._rejectAllPending(err));
  }

  _handleLine(line) {
    const trimmed = line.trim();
    if (!trimmed) return;
    let message;
    try {
      message = JSON.parse(trimmed);
    } catch {
      return;
    }
    const { id, result, error } = message;
    if (id === undefined || !this.pending.has(id)) return;
    const { resolve, reject } = this.pending.get(id);
    this.pending.delete(id);
    if (error) reject(new Error(error.message));
    else resolve(result);
  }

  _rejectAllPending(err) {
    for (const { reject } of this.pending.values()) reject(err);
    this.pending.clear();
  }

  _send(method, params) {
    this._ensureStarted();
    const id = this.nextId++;
    const payload = { jsonrpc: '2.0', id, method, params };
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.child.stdin.write(JSON.stringify(payload) + '\n');
    });
  }

  initialize() {
    return this._send('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'aosdf-vscode', version: '0.1.0' },
    });
  }

  async callTool(name, args = {}) {
    const result = await this._send('tools/call', { name, arguments: args });
    const text = result && result.content && result.content[0] && result.content[0].text;
    const parsed = text ? JSON.parse(text) : null;
    if (result && result.isError) {
      throw new Error(typeof parsed === 'string' ? parsed : text);
    }
    return parsed;
  }

  stop() {
    if (this.rl) {
      this.rl.close();
      this.rl = null;
    }
    if (this.child) {
      this.child.kill();
      this.child = null;
    }
    this._rejectAllPending(new Error('client stopped'));
  }
}

module.exports = { McpClient };

'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const { readLastUsage, totalContextTokens, evaluate } = require('../session-context-gate');

const HOOK_PATH = path.join(__dirname, '..', 'session-context-gate.js');

function writeTranscript(entries) {
  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'gate-test-')), 'transcript.jsonl');
  fs.writeFileSync(file, entries.map((e) => JSON.stringify(e)).join('\n') + '\n');
  return file;
}

function assistantEntry(usage) {
  return { type: 'assistant', message: { role: 'assistant', content: [], usage } };
}

test('readLastUsage finds the most recent usage entry, ignoring earlier ones', () => {
  const file = writeTranscript([
    assistantEntry({ input_tokens: 1000, output_tokens: 50 }),
    { type: 'user', message: { role: 'user', content: 'hi' } },
    assistantEntry({ input_tokens: 5000, output_tokens: 200, cache_read_input_tokens: 1000 }),
  ]);
  const usage = readLastUsage(file);
  assert.equal(usage.input_tokens, 5000);
  assert.equal(usage.cache_read_input_tokens, 1000);
});

test('readLastUsage returns null for a missing file', () => {
  assert.equal(readLastUsage('/nonexistent/path/transcript.jsonl'), null);
});

test('readLastUsage tolerates malformed lines mixed with valid ones', () => {
  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'gate-test-')), 'transcript.jsonl');
  fs.writeFileSync(file, 'not json\n' + JSON.stringify(assistantEntry({ input_tokens: 42 })) + '\n{"broken"\n');
  const usage = readLastUsage(file);
  assert.equal(usage.input_tokens, 42);
});

test('totalContextTokens sums input + cache creation + cache read', () => {
  const total = totalContextTokens({
    input_tokens: 100,
    cache_creation_input_tokens: 50,
    cache_read_input_tokens: 850,
  });
  assert.equal(total, 1000);
});

test('evaluate does not block under threshold', () => {
  const file = writeTranscript([assistantEntry({ input_tokens: 50000 })]); // 25% of 200k default
  const result = evaluate(file, {});
  assert.equal(result.block, false);
});

test('evaluate blocks at/above the 60% default threshold', () => {
  const file = writeTranscript([assistantEntry({ input_tokens: 130000 })]); // 65% of 200k default
  const result = evaluate(file, {});
  assert.equal(result.block, true);
  assert.match(result.reason, /Insufficient context remaining/);
  assert.match(result.reason, /65%/);
});

test('evaluate respects AOSDF_CONTEXT_WINDOW and AOSDF_CONTEXT_THRESHOLD overrides', () => {
  const file = writeTranscript([assistantEntry({ input_tokens: 400000 })]);
  const env = { AOSDF_CONTEXT_WINDOW: '1000000', AOSDF_CONTEXT_THRESHOLD: '0.5' };
  const result = evaluate(file, env);
  assert.equal(result.block, false); // 400k / 1M = 40%, under the 50% override
});

test('evaluate fails open (does not block) when no usage data is found', () => {
  const file = writeTranscript([{ type: 'user', message: { role: 'user', content: 'hi' } }]);
  const result = evaluate(file, {});
  assert.equal(result.block, false);
  assert.equal(result.reason, 'no-usage-data');
});

test('evaluate fails open when the transcript file does not exist', () => {
  const result = evaluate('/nonexistent/transcript.jsonl', {});
  assert.equal(result.block, false);
});

test('end-to-end: the hook process blocks via stdin/stdout, matching PreToolUse JSON schema', () => {
  const file = writeTranscript([assistantEntry({ input_tokens: 150000 })]); // 75% of default 200k
  const input = JSON.stringify({
    session_id: 'test',
    transcript_path: file,
    cwd: '/tmp',
    hook_event_name: 'PreToolUse',
    tool_name: 'Task',
    tool_input: {},
  });
  const result = spawnSync('node', [HOOK_PATH], { input, encoding: 'utf8' });
  assert.equal(result.status, 0);
  const output = JSON.parse(result.stdout);
  assert.equal(output.hookSpecificOutput.hookEventName, 'PreToolUse');
  assert.equal(output.hookSpecificOutput.permissionDecision, 'deny');
});

test('end-to-end: the hook process allows silently (no stdout) when well under threshold', () => {
  const file = writeTranscript([assistantEntry({ input_tokens: 10000 })]); // 5% of default 200k
  const input = JSON.stringify({
    session_id: 'test',
    transcript_path: file,
    hook_event_name: 'PreToolUse',
    tool_name: 'Agent',
    tool_input: {},
  });
  const result = spawnSync('node', [HOOK_PATH], { input, encoding: 'utf8' });
  assert.equal(result.status, 0);
  assert.equal(result.stdout.trim(), '');
});

test('end-to-end: malformed stdin fails open with exit 0 and no output', () => {
  const result = spawnSync('node', [HOOK_PATH], { input: 'not json at all', encoding: 'utf8' });
  assert.equal(result.status, 0);
  assert.equal(result.stdout.trim(), '');
});

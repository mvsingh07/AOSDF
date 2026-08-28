#!/usr/bin/env node
'use strict';

// session-context-gate — E3-T2, enforcing Principle 27 ("Session context rules are enforced,
// not advisory, where tooling allows"). Turns manual.md's Session Context Management Rule 2
// ("do not start a task you cannot finish" / "never exceed 60% context usage before starting a
// new task") from an honor-system instruction into a real PreToolUse gate on the tool that
// actually starts a task: Task/Agent (see .claude/settings.json's PreToolUse matcher).
//
// Honest limits, stated up front (framework.md documents these too):
//   - Claude Code's hook input carries no direct token-usage or context-percentage field
//     (confirmed against the current hooks docs). This script estimates usage itself by reading
//     the transcript JSONL at transcript_path and taking the most recent turn's reported
//     usage.{input_tokens,cache_creation_input_tokens,cache_read_input_tokens} — the same numbers
//     the Anthropic API returns for that turn's request.
//   - transcript_path is written asynchronously and can lag slightly behind the current turn.
//   - The hook has no reliable way to know which model (and therefore which context window size)
//     is active — SessionStart's optional model field isn't guaranteed present. AOSDF_CONTEXT_WINDOW
//     lets a human set the real number for their model; the default (200000) is a conservative
//     placeholder, not a claim about any specific model.
//   - On any parse failure or missing data, this fails OPEN (allows the call) rather than blocking
//     on a guess — a false "safe to proceed" is recoverable, a spurious block on every session start
//     is not.

const fs = require('fs');

const DEFAULT_MAX_CONTEXT = 200000;
const DEFAULT_THRESHOLD = 0.6; // manual.md Rule 1: "Never exceed 60% context usage before starting a new task."

function readLastUsage(transcriptPath) {
  let content;
  try {
    content = fs.readFileSync(transcriptPath, 'utf8');
  } catch {
    return null;
  }

  const lines = content.split('\n');
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim();
    if (!line) continue;
    let entry;
    try {
      entry = JSON.parse(line);
    } catch {
      continue;
    }
    const usage = entry && entry.message && entry.message.usage;
    if (usage && typeof usage.input_tokens === 'number') {
      return usage;
    }
  }
  return null;
}

function totalContextTokens(usage) {
  return (
    (usage.input_tokens || 0) +
    (usage.cache_creation_input_tokens || 0) +
    (usage.cache_read_input_tokens || 0)
  );
}

function evaluate(transcriptPath, env = process.env) {
  const usage = readLastUsage(transcriptPath);
  if (!usage) {
    return { block: false, reason: 'no-usage-data' };
  }

  const maxContext = Number(env.AOSDF_CONTEXT_WINDOW) || DEFAULT_MAX_CONTEXT;
  const threshold = Number(env.AOSDF_CONTEXT_THRESHOLD) || DEFAULT_THRESHOLD;
  const used = totalContextTokens(usage);
  const fraction = used / maxContext;

  if (fraction >= threshold) {
    const pct = Math.round(fraction * 100);
    const thresholdPct = Math.round(threshold * 100);
    return {
      block: true,
      reason:
        `Insufficient context remaining to start this task safely (~${pct}% of the assumed ` +
        `${maxContext}-token context window used, AOSDF's threshold is ${thresholdPct}%). ` +
        `Please compact the session and re-invoke the Commander (manual.md Session Context ` +
        `Management Rule 2, enforced here per Principle 27). If ${maxContext} tokens is wrong for ` +
        `the active model, set AOSDF_CONTEXT_WINDOW to the correct max.`,
    };
  }

  return { block: false, reason: 'under-threshold', fraction };
}

function main() {
  let raw = '';
  process.stdin.on('data', (chunk) => {
    raw += chunk;
  });
  process.stdin.on('end', () => {
    let input;
    try {
      input = JSON.parse(raw);
    } catch {
      process.exit(0); // Can't parse the hook input — fail open.
    }

    const transcriptPath = input && input.transcript_path;
    if (!transcriptPath) {
      process.exit(0);
    }

    const result = evaluate(transcriptPath);
    if (result.block) {
      process.stdout.write(
        JSON.stringify({
          hookSpecificOutput: {
            hookEventName: 'PreToolUse',
            permissionDecision: 'deny',
            permissionDecisionReason: result.reason,
          },
        })
      );
    }
    process.exit(0);
  });
}

if (require.main === module) {
  main();
}

module.exports = { readLastUsage, totalContextTokens, evaluate, DEFAULT_MAX_CONTEXT, DEFAULT_THRESHOLD };

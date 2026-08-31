'use strict';

// Pure formatting from aosdf_read_status / aosdf_next_planned_task results to
// the status bar chip's text and tooltip. Kept dependency-free from vscode so
// it's directly unit-testable (E4-T1).

function formatStatusBarText(status, nextTask) {
  const state = (status && status.currentState) || 'UNKNOWN';
  if (nextTask && nextTask.taskId) {
    return `AOSDF: ${state} — ${nextTask.taskId}`;
  }
  return `AOSDF: ${state}`;
}

function formatTooltip(status, nextTask) {
  const lines = [];
  lines.push(`**Current State:** ${(status && status.currentState) || 'UNKNOWN'}`);
  if (nextTask && nextTask.taskId) {
    lines.push(`**Next Planned Task:** ${nextTask.taskId} — ${nextTask.task || ''}`);
    if (nextTask.phaseHeading) lines.push(`**Phase:** ${nextTask.phaseHeading}`);
  } else {
    lines.push('**Next Planned Task:** none currently `Planned`');
  }
  if (status && status.nextAction) {
    lines.push('', '**Next Action:**', status.nextAction);
  }
  return lines.join('\n');
}

module.exports = { formatStatusBarText, formatTooltip };

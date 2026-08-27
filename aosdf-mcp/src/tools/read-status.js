'use strict';

const fs = require('fs');

const schema = {
  name: 'aosdf_read_status',
  description:
    "Reads project_status.md and returns the project's current state (SETUP / PLANNING / " +
    'READY / IN_PROGRESS / BLOCKED / COMPLETE) plus its Next Action section, so an agent or ' +
    'the editor status bar chip never has to re-derive readiness by hand.',
  inputSchema: {
    type: 'object',
    properties: {},
    additionalProperties: false,
  },
};

function run(_args, paths) {
  const content = fs.readFileSync(paths.projectStatus, 'utf8');
  const stateMatch = content.match(/\*\*Current State:\*\*\s*([A-Z_]+)/);
  const nextActionMatch = content.match(/^##\s*Next Action\s*\n+([\s\S]*?)(?:\n##\s|\n---|$)/m);
  return {
    path: paths.projectStatus,
    currentState: stateMatch ? stateMatch[1] : null,
    nextAction: nextActionMatch ? nextActionMatch[1].trim() : null,
    raw: content,
  };
}

module.exports = { schema, run };

'use strict';

const path = require('path');

// Every path below can be overridden individually via env var — this is how
// a project that documents a deviation (e.g. this meta-project's own
// manual_actions.md living at its docs root instead of under
// documents/12_Manual_Actions/actions.md) stays servable without forking
// the tool. AOSDF_DOCS_ROOT itself must always point at a project's
// `{project_name}-Documents/docs/` folder.
function resolveDocsRoot() {
  const root = process.env.AOSDF_DOCS_ROOT;
  if (!root) {
    throw new Error(
      "AOSDF_DOCS_ROOT is not set — point it at the '{project_name}-Documents/docs/' " +
        'folder this server should read and write.'
    );
  }
  return path.resolve(root);
}

function resolvePaths(root) {
  return {
    projectStatus:
      process.env.AOSDF_PROJECT_STATUS_PATH || path.join(root, 'project_status.md'),
    executionPlan:
      process.env.AOSDF_EXECUTION_PLAN_PATH ||
      path.join(root, 'documents', '06_Execution_Plan', 'execution_plan.md'),
    identifiedGaps:
      process.env.AOSDF_IDENTIFIED_GAPS_PATH || path.join(root, 'identified_gaps.md'),
    manualActions:
      process.env.AOSDF_MANUAL_ACTIONS_PATH ||
      path.join(root, 'documents', '12_Manual_Actions', 'actions.md'),
    moduleIndex:
      process.env.AOSDF_MODULE_INDEX_PATH ||
      path.join(root, 'documents', '03_System_Design', 'README.md'),
    implementationPromptsIndex:
      process.env.AOSDF_IMPLEMENTATION_PROMPTS_PATH ||
      path.join(root, 'documents', '05_AI_Agent_System', 'implementation_prompts', 'README.md'),
  };
}

module.exports = { resolveDocsRoot, resolvePaths };

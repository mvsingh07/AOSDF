'use strict';

// AOSDF for VSCode — E4-T1/E4-T2 (read-only), E5-T1 (write actions), E6-T2
// (multi-workspace). A thin shell: all real logic already lives in aosdf-mcp
// (E2-T1, spoken to over its own stdio JSON-RPC protocol via mcpClient.js)
// or in direct, uncached reads of the same markdown files aosdf-mcp itself
// reads (inboxData.js) — never a second source of truth (Principle 26).
// Unlike .claude/ and .mcp.json, this extension itself is NOT copied into
// {project_name}/ (see framework.md § Editor Integration MVP, "Where It
// Lives") — only {project_name}/.vscode/settings.json is written, by
// workflow_initiator Step 8, so a developer's F5 run of this extension
// picks up the right workspace automatically.

const vscode = require('vscode');
const path = require('path');
const fs = require('fs');
const { McpClient } = require('./mcpClient');
const { formatStatusBarText, formatTooltip } = require('./statusFormatter');
const { InboxProvider } = require('./inboxProvider');
const { sendToTerminal } = require('./terminalRunner');

// [v2.5, E5-T1] The 7 slash commands E3-T1 wired in .claude/commands/*.md — offered
// here as a QuickPick so a human doesn't have to remember/retype them. Selecting one
// only sends its text into a terminal (see terminalRunner.js); nothing here invokes
// an agent directly or writes any AOSDF file itself.
const SLASH_COMMANDS = [
  { label: '/aosdf-init', description: 'workflow-initiator' },
  { label: '/aosdf-plan', description: 'captain-agent' },
  { label: '/aosdf-next', description: 'commander-agent (session start)' },
  { label: '/aosdf-addendum', description: 'addendum-agent', needsArg: 'Path to the addendum doc' },
  { label: '/aosdf-research', description: 'research-and-refine-agent', needsArg: 'Path to task.md' },
  { label: '/aosdf-sync', description: "tracker-sync-agent, Export Mode ('Tracker: sync')" },
  { label: '/aosdf-import', description: "tracker-sync-agent, Import Mode ('Tracker: import <ref>')", needsArg: 'Reference to import' },
];

// [v3.0, E6-T2] Multi-workspace support (OD-4's deferred item). One aosdf-mcp
// client per open workspace folder, keyed by folder.uri.toString() — each
// folder can point at a different {project_name}-Documents/docs, so nothing
// here may assume folders[0] is the only project. The status bar chip stays
// a single item (one chip, not one per folder) and shows whichever folder
// currently "has focus" (see activeFolder()); the Inbox view shows every
// folder at once (inboxProvider.js). With exactly one folder open, every
// function below reduces to its original E4-T1 single-workspace behavior.
const folderClients = new Map();
let statusBarItem = null;
let inboxProvider = null;

function getWorkspaceFolders() {
  return vscode.workspace.workspaceFolders || [];
}

// The folder whose data the status bar chip currently reflects: the folder
// containing the active editor's document, or the first folder otherwise.
function activeFolder() {
  const folders = getWorkspaceFolders();
  if (folders.length === 0) return null;
  const editor = vscode.window.activeTextEditor;
  if (editor) {
    const owning = vscode.workspace.getWorkspaceFolder(editor.document.uri);
    if (owning) return owning;
  }
  return folders[0];
}

function getConfig(folder) {
  return vscode.workspace.getConfiguration('aosdf', folder ? folder.uri : undefined);
}

function resolveFolderPath(folder, relativeOrAbsolute) {
  if (!folder) return null;
  return path.resolve(folder.uri.fsPath, relativeOrAbsolute);
}

function getDocumentsRootForFolder(folder) {
  const configured = getConfig(folder).get('documentsRoot');
  if (!configured) return null;
  return resolveFolderPath(folder, configured);
}

function getMcpServerPathForFolder(folder) {
  const configured = getConfig(folder).get('mcpServerPath');
  if (!configured) return null;
  return resolveFolderPath(folder, configured);
}

function getClientForFolder(folder, serverPath, documentsRoot) {
  const key = folder.uri.toString();
  let entry = folderClients.get(key);
  if (!entry) {
    entry = new McpClient(serverPath, { AOSDF_DOCS_ROOT: documentsRoot });
    folderClients.set(key, entry);
  }
  return entry;
}

function restartClientForFolder(folder) {
  const key = folder.uri.toString();
  const entry = folderClients.get(key);
  if (entry) {
    entry.stop();
    folderClients.delete(key);
  }
}

function restartAllClients() {
  for (const entry of folderClients.values()) entry.stop();
  folderClients.clear();
}

async function refreshStatusBar() {
  const folders = getWorkspaceFolders();
  if (folders.length === 0) {
    statusBarItem.text = 'AOSDF: no workspace folder open';
    statusBarItem.tooltip = 'Open a folder to see AOSDF project status.';
    statusBarItem.show();
    return;
  }

  const folder = activeFolder();
  const label = folders.length > 1 ? `[${folder.name}] ` : '';

  const documentsRoot = getDocumentsRootForFolder(folder);
  if (!documentsRoot) {
    statusBarItem.text = `${label}AOSDF: not configured`;
    statusBarItem.tooltip = "Set aosdf.documentsRoot to this product's '{project_name}-Documents/docs' folder.";
    statusBarItem.show();
    return;
  }

  const serverPath = getMcpServerPathForFolder(folder);
  if (!serverPath || !fs.existsSync(serverPath)) {
    statusBarItem.text = `${label}AOSDF: mcp server not found`;
    statusBarItem.tooltip = `Expected aosdf-mcp at ${serverPath}. Set aosdf.mcpServerPath.`;
    statusBarItem.show();
    return;
  }

  try {
    const client = getClientForFolder(folder, serverPath, documentsRoot);
    if (!client.initialized) {
      await client.initialize();
      client.initialized = true;
    }
    const [status, nextTask] = await Promise.all([
      client.callTool('aosdf_read_status'),
      client.callTool('aosdf_next_planned_task'),
    ]);
    statusBarItem.text = label + formatStatusBarText(status, nextTask);
    statusBarItem.tooltip = new vscode.MarkdownString(formatTooltip(status, nextTask));
    statusBarItem.show();
  } catch (err) {
    statusBarItem.text = `${label}AOSDF: error`;
    statusBarItem.tooltip = err.message;
    statusBarItem.show();
  }
}

function activate(context) {
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  statusBarItem.command = 'aosdf.openProjectStatus';
  context.subscriptions.push(statusBarItem);

  inboxProvider = new InboxProvider(getWorkspaceFolders, getDocumentsRootForFolder);
  const treeView = vscode.window.createTreeView('aosdf.inbox', { treeDataProvider: inboxProvider });
  context.subscriptions.push(treeView);

  // [v3.0, E6-T2] Only prompts for a folder when more than one is open —
  // with a single folder this is skipped entirely, so single-workspace
  // command behavior is byte-for-byte what E5-T1 shipped.
  async function pickFolderIfNeeded() {
    const folders = getWorkspaceFolders();
    if (folders.length <= 1) return folders[0];
    const picked = await vscode.window.showQuickPick(
      folders.map((f) => ({ label: f.name, folder: f })),
      { placeHolder: 'Which AOSDF workspace folder?' }
    );
    return picked ? picked.folder : undefined;
  }

  context.subscriptions.push(
    vscode.commands.registerCommand('aosdf.refresh', () => {
      restartAllClients();
      refreshStatusBar();
      inboxProvider.refresh();
    }),

    vscode.commands.registerCommand('aosdf.openProjectStatus', () => {
      const folder = activeFolder();
      const root = folder ? getDocumentsRootForFolder(folder) : null;
      if (!root) {
        vscode.window.showWarningMessage('Set aosdf.documentsRoot first.');
        return;
      }
      vscode.window.showTextDocument(vscode.Uri.file(path.join(root, 'project_status.md')));
    }),

    // [v3.0, L4-T1] Thin wrapper around 'Learn: open' — the Learning Roadmap's
    // render/index.html always lives inside documentsRoot (unlike the Project
    // Docs Site, which sits outside docs/ as a sibling), so its path is derived
    // rather than needing its own setting.
    vscode.commands.registerCommand('aosdf.openLearningRoadmap', () => {
      const folder = activeFolder();
      const root = folder ? getDocumentsRootForFolder(folder) : null;
      const sitePath = root
        ? path.join(root, 'documents', '16_Learning_Roadmap', 'render', 'index.html')
        : null;
      if (!sitePath || !fs.existsSync(sitePath)) {
        vscode.window.showWarningMessage(
          `Learning Roadmap not found at ${sitePath || '(unset)'}. Run concept_indexer_agent's 'Learn: rebuild' first, or set aosdf.documentsRoot.`
        );
        return;
      }
      vscode.env.openExternal(vscode.Uri.file(sitePath));
    }),

    vscode.commands.registerCommand('aosdf.openInboxItem', (file, line) => {
      vscode.window.showTextDocument(vscode.Uri.file(file), {
        selection: new vscode.Range(line, 0, line, 0),
      });
    }),

    vscode.commands.registerCommand('aosdf.openProjectDocs', () => {
      const folder = activeFolder();
      const configured = folder ? getConfig(folder).get('projectDocsSitePath') : null;
      const sitePath = configured ? resolveFolderPath(folder, configured) : null;
      if (!sitePath || !fs.existsSync(sitePath)) {
        vscode.window.showWarningMessage(
          `Project Docs Site not found at ${sitePath || '(unset)'}. Run docs_site_agent's 'Project Docs: build' first, or set aosdf.projectDocsSitePath.`
        );
        return;
      }
      vscode.env.openExternal(vscode.Uri.file(sitePath));
    }),

    vscode.workspace.onDidChangeConfiguration((event) => {
      let affected = false;
      for (const folder of getWorkspaceFolders()) {
        if (event.affectsConfiguration('aosdf', folder.uri)) {
          restartClientForFolder(folder);
          affected = true;
        }
      }
      if (affected) {
        refreshStatusBar();
        inboxProvider.refresh();
      }
    }),

    vscode.window.onDidChangeActiveTextEditor(() => refreshStatusBar()),

    vscode.workspace.onDidChangeWorkspaceFolders((event) => {
      for (const folder of event.removed) restartClientForFolder(folder);
      refreshStatusBar();
      inboxProvider.refresh();
    }),

    // [v2.5, E5-T1; v3.0, E6-T2 folder-aware] Write actions — all three reduce
    // to "type this text into a terminal." No command here writes an AOSDF
    // file directly; whatever changes on disk happens inside the Claude Code
    // session running in that terminal.
    vscode.commands.registerCommand('aosdf.runAgentCommand', async () => {
      const folder = await pickFolderIfNeeded();
      if (!folder) return;
      const picked = await vscode.window.showQuickPick(SLASH_COMMANDS, {
        placeHolder: 'Which AOSDF command?',
      });
      if (!picked) return;
      let text = picked.label;
      if (picked.needsArg) {
        const arg = await vscode.window.showInputBox({ prompt: picked.needsArg });
        if (arg === undefined) return;
        text = `${picked.label} ${arg}`;
      }
      sendToTerminal(text, getWorkspaceFolders().length > 1 ? folder : undefined);
    }),

    vscode.commands.registerCommand('aosdf.triggerTrackerSync', async () => {
      const folder = await pickFolderIfNeeded();
      if (!folder) return;
      sendToTerminal('/aosdf-sync', getWorkspaceFolders().length > 1 ? folder : undefined);
    }),

    vscode.commands.registerCommand('aosdf.approvePromptItem', async (item) => {
      if (item && item.aosdfPromptPath && fs.existsSync(item.aosdfPromptPath)) {
        await vscode.window.showTextDocument(vscode.Uri.file(item.aosdfPromptPath));
      }
      const folder = item && item.aosdfFolder;
      sendToTerminal('Approve to execute', getWorkspaceFolders().length > 1 ? folder : undefined);
    })
  );

  for (const glob of [
    '**/project_status.md',
    '**/identified_gaps.md',
    '**/manual_actions.md',
    '**/actions.md',
    '**/implementation_prompts/README.md',
  ]) {
    const watcher = vscode.workspace.createFileSystemWatcher(glob);
    const onChange = () => {
      refreshStatusBar();
      inboxProvider.refresh();
    };
    watcher.onDidChange(onChange);
    watcher.onDidCreate(onChange);
    watcher.onDidDelete(onChange);
    context.subscriptions.push(watcher);
  }

  refreshStatusBar();
}

function deactivate() {
  restartAllClients();
}

module.exports = { activate, deactivate };

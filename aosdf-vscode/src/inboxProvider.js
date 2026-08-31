'use strict';

const vscode = require('vscode');
const { readInbox } = require('./inboxData');
const { readPendingPrompts } = require('./promptsData');

// TreeDataProvider for the "Gaps & Manual Actions" view. Flat, two-section
// list (Gaps, then Manual Actions) rather than a real tree — there's no
// hierarchy to a row beyond the file it came from, and a flat list keeps
// this a thin shell over inboxData.js's parsing, not a second implementation
// of it.
//
// [v3.0, E6-T2] Multi-workspace: iterates every open workspace folder rather
// than assuming one. With exactly one folder this produces the identical
// flat list E4-T1 always has (no section-label prefix) — multi-root is the
// only case that adds a `[folderName] ` prefix per section, keeping this
// still a flat list rather than a new tree level, consistent with the
// existing design. Each entry/prompt item is stamped with `aosdfFolder` so
// write-action commands (E5-T1) know which folder's terminal to target.
class InboxProvider {
  constructor(getWorkspaceFolders, getDocumentsRootForFolder) {
    this.getWorkspaceFolders = getWorkspaceFolders;
    this.getDocumentsRootForFolder = getDocumentsRootForFolder;
    this._onDidChangeTreeData = new vscode.EventEmitter();
    this.onDidChangeTreeData = this._onDidChangeTreeData.event;
  }

  refresh() {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element) {
    return element;
  }

  getChildren(element) {
    if (element) return [];

    const folders = this.getWorkspaceFolders() || [];
    if (folders.length === 0) {
      return [this._leaf('No workspace folder is open.')];
    }
    const multi = folders.length > 1;

    const items = [];
    for (const folder of folders) {
      const prefix = multi ? `[${folder.name}] ` : '';
      const root = this.getDocumentsRootForFolder(folder);
      if (!root) {
        items.push(this._leaf(`${prefix}Set aosdf.documentsRoot to see gaps and manual actions.`));
        continue;
      }

      let inbox;
      let prompts;
      try {
        inbox = readInbox(root);
        prompts = readPendingPrompts(root);
      } catch (err) {
        items.push(this._leaf(`${prefix}Failed to read inbox: ${err.message}`));
        continue;
      }

      items.push(this._section(`${prefix}Gaps (${inbox.gaps.length})`));
      for (const gap of inbox.gaps) items.push(this._item(gap, folder));
      items.push(this._section(`${prefix}Manual Actions (${inbox.actions.length})`));
      for (const action of inbox.actions) items.push(this._item(action, folder));
      items.push(this._section(`${prefix}Implementation Prompts Awaiting Approval (${prompts.length})`));
      for (const prompt of prompts) items.push(this._promptItem(prompt, folder));
    }
    return items;
  }

  _section(label) {
    const item = new vscode.TreeItem(label, vscode.TreeItemCollapsibleState.None);
    item.contextValue = 'aosdf.section';
    return item;
  }

  _leaf(label) {
    return new vscode.TreeItem(label, vscode.TreeItemCollapsibleState.None);
  }

  _item(entry, folder) {
    const item = new vscode.TreeItem(`${entry.id} — ${entry.status}`, vscode.TreeItemCollapsibleState.None);
    item.description = entry.description;
    item.tooltip = entry.description;
    item.contextValue = `aosdf.${entry.kind}`;
    item.aosdfFolder = folder;
    item.command = {
      command: 'aosdf.openInboxItem',
      title: 'Open',
      arguments: [entry.file, entry.line],
    };
    return item;
  }

  _promptItem(prompt, folder) {
    const item = new vscode.TreeItem(`${prompt.task || prompt.fileName} — ${prompt.status}`, vscode.TreeItemCollapsibleState.None);
    item.description = prompt.fileName;
    item.tooltip = 'Click to open the prompt file and review it before approving.';
    item.contextValue = 'aosdf.prompt';
    item.aosdfPromptPath = prompt.promptPath;
    item.aosdfFolder = folder;
    item.command = {
      command: 'aosdf.openInboxItem',
      title: 'Open',
      arguments: [prompt.promptPath, 0],
    };
    return item;
  }
}

module.exports = { InboxProvider };

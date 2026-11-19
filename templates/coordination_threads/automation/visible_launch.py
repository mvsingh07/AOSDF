#!/usr/bin/env python3
"""Visible-terminal launcher (founder direction 2026-10-23).

Every worker the coordinator dispatches — Claude or Codex — must open in its OWN
visible macOS Terminal window that the founder can watch, not a hidden background
process. This module is the single, executor-agnostic mechanism for that.

What it does NOT do: it does not decide WHETHER a launch is allowed. That stays with
the caller's gate (supervisor dispatch stage>=2 + explicit authorization, or a
founder-authorized pilot). Called with `dry_run=True` it opens nothing and returns the
exact script + AppleScript that WOULD run, so a launch can always be previewed first.

macOS only (osascript + Terminal.app). Stdlib only.
"""
from __future__ import annotations
import json, os, shlex, subprocess, datetime
from pathlib import Path

CAFFEINATE = "/usr/bin/caffeinate"
TEE = "/usr/bin/tee"
SCRIPT = "/usr/bin/script"

# Profile-selecting variables carried from the coordinator into the worker window.
# Terminal.app's `do script` starts a fresh login shell that does NOT inherit the
# launching process's environment, so without this a worker silently falls back to
# the default profile (~/.claude, ~/.codex) instead of the coordinator's (e.g.
# ~/.claude-vu08). Paths only — never tokens or keys.
PROFILE_ENV_VARS = ("CLAUDE_CONFIG_DIR", "CODEX_HOME")


def profile_env(environ=None) -> dict[str, str]:
    """The coordinator's profile-selecting variables that are set (non-empty)."""
    environ = os.environ if environ is None else environ
    return {k: environ[k] for k in PROFILE_ENV_VARS if environ.get(k)}

# The read-only, all-tools-disabled codex flag set proven by the 2026-10-22 pilot.
# The caller owns the actual worker scope; these are the safe defaults.
CODEX_DISABLES = [
    "shell_tool", "unified_exec", "hooks", "plugins", "apps",
    "browser_use", "computer_use", "image_generation",
    "skill_search", "skill_mcp_dependency_install",
]


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def codex_argv(cd: Path, *, output_schema: Path | None = None,
               output_last: Path | None = None, sandbox: str = "read-only",
               codex_bin: str = "codex", disables=None) -> list[str]:
    """Argv for a Codex worker. Reads the prompt from stdin ('-'); caller pipes it in."""
    argv = [codex_bin, "exec", "--ignore-user-config", "--sandbox", sandbox,
            "-c", 'approval_policy="never"', "-c", 'web_search="disabled"',
            "--skip-git-repo-check", "--json", "--color", "never", "--cd", str(cd)]
    if output_schema is not None:
        argv += ["--output-schema", str(output_schema)]
    if output_last is not None:
        argv += ["--output-last-message", str(output_last)]
    for d in (disables if disables is not None else CODEX_DISABLES):
        argv += ["--disable", d]
    argv.append("-")
    return argv


def codex_interactive_argv(cd: Path, prompt: str, *, codex_bin: str = "codex",
                           yolo: bool = False, model: str | None = None,
                           extra: list[str] | None = None) -> list[str]:
    """Argv for an INTERACTIVE Codex worker (its TUI). The prompt is the initial positional
    instruction and the worker writes its own files.

    `yolo=True` adds `--yolo` (bypass approvals + sandbox) so the worker runs unattended like a
    `codex --yolo` coordinator — the founder watches the live window instead of approving each step.
    `yolo=False` leaves Codex's own interactive approval UX in place (founder approves each action).
    """
    argv = [codex_bin]
    if yolo:
        argv.append("--yolo")
    if model:
        argv += ["--model", model]
    argv += ["--cd", str(cd)]
    if extra:
        argv += list(extra)
    argv.append(prompt)
    return argv


def claude_argv(cd: Path, prompt: str, *, resume: str | None = None,
                permission_mode: str | None = None, skip_permissions: bool = False,
                model: str | None = None, claude_bin: str = "claude",
                extra: list[str] | None = None) -> list[str]:
    """Argv for a Claude worker in a visible, interactive session.

    `resume` continues a prior session id (never a placeholder — pass a real id or omit it for a
    fresh session). `permission_mode` ('plan' read-only, 'acceptEdits', …) is left to the caller.
    `skip_permissions=True` adds `--dangerously-skip-permissions` so the worker runs unattended like
    a `claude --dangerously-skip-permissions` coordinator — the founder watches the live window.
    """
    argv = [claude_bin, "--add-dir", str(cd)]
    if model:
        argv += ["--model", model]
    if resume:
        argv += ["--resume", resume]
    if skip_permissions:
        argv.append("--dangerously-skip-permissions")
    elif permission_mode:
        argv += ["--permission-mode", permission_mode]
    if extra:
        argv += list(extra)
    argv.append(prompt)
    return argv


def build_launch_script(run_dir: Path, argv: list[str], *, log_name: str = "terminal.log",
                        stdin_file: Path | None = None, record_pid: bool = False,
                        env: dict[str, str] | None = None) -> Path:
    """Write launch-visible.sh with PTY logging for interactive workers.

    `stdin_file` (used for Codex, whose prompt is read from stdin via the trailing '-')
    is redirected into the command before the tee pipe.
    `env` defaults to `profile_env()` — the coordinator's CLAUDE_CONFIG_DIR / CODEX_HOME —
    and is exported in the script so the worker uses the same Claude/Codex profile.
    """
    log_path = run_dir / log_name
    command = " ".join(shlex.quote(a) for a in argv)
    if stdin_file is None:
        # Interactive TUIs require a terminal on stdin/stdout. script supplies a
        # PTY and records output without enabling keystroke/input recording.
        invocation = (f"exec {shlex.quote(CAFFEINATE)} -i {shlex.quote(SCRIPT)} "
                      f"-q -F {shlex.quote(str(log_path))} {command}\n")
    else:
        invocation = (f"{shlex.quote(CAFFEINATE)} -i {command}"
                      f" < {shlex.quote(str(stdin_file))}"
                      f" 2>&1 | {shlex.quote(TEE)} {shlex.quote(str(log_path))}\n")
    pid_line = (f"printf '%s\\n' \"$$\" > {shlex.quote(str(run_dir / 'coordinator.pid'))}\n"
                if record_pid else "")
    # PROFILE SWITCH: keep exactly one of these lines active.
    # (1) Same profile as the coordinator that launches the worker (default):
    # env_vars = profile_env() if env is None else env
    # (2) A fixed, different Claude profile (edit the path; use {} for the default ~/.claude):
    env_vars = profile_env() if env is None else env
    env_lines = "".join(f"export {k}={shlex.quote(v)}\n" for k, v in env_vars.items())
    body = ("#!/bin/bash\nset -o pipefail\n" + env_lines +
            f"cd {shlex.quote(str(run_dir))}\n" + pid_line + invocation)
    script = run_dir / "launch-visible.sh"
    script.write_text(body, encoding="utf-8")
    script.chmod(0o755)
    return script


def _osascript_text(script: Path, title: str) -> str:
    command = json.dumps("bash " + shlex.quote(str(script)), ensure_ascii=False)
    return (
        'tell application "Terminal"\n'
        "    activate\n"
        f'    do script {command}\n'
        "    delay 0.3\n"
        f'    set custom title of front window to {json.dumps(title, ensure_ascii=False)}\n'
        "    return id of front window\n"
        "end tell\n"
    )


def write_view(run_dir: Path, title: str, executor: str) -> Path:
    view = run_dir / "VIEW.md"
    view.write_text(
        f"# Visible worker — {executor}\n\n"
        f"A dedicated macOS Terminal window titled \"{title}\" runs `launch-visible.sh`.\n"
        "`terminal.log` mirrors everything shown in that window.\n\n"
        "**Safe stop:** Ctrl+C in that Terminal window (the worker finishes its current\n"
        "write and exits cleanly; the fence makes a late completion impossible). Do NOT\n"
        "re-run `launch-visible.sh` — `.launcher-once` prevents a duplicate launch.\n\n"
        "The worker runs ONE bounded task, then exits; it never picks its own next task.\n",
        encoding="utf-8",
    )
    return view


def launch_visible(run_dir: Path, executor: str, argv: list[str], *, title: str,
                   dry_run: bool = False, stdin_file: Path | None = None,
                   record_pid: bool = False) -> dict:
    """Open (or, with dry_run, preview) a visible Terminal window running argv.

    Returns a record with the script path, the AppleScript, and — on a real launch —
    the opened window id. Enforces a per-run `.launcher-once` guard against duplicates.
    """
    if not dry_run:
        return {"refused": "inactive reusable template: real launches require project implementation"}
    run_dir.mkdir(parents=True, exist_ok=True)
    once = run_dir / ".launcher-once"
    script = build_launch_script(run_dir, argv, stdin_file=stdin_file, record_pid=record_pid)
    write_view(run_dir, title, executor)
    osa = _osascript_text(script, title)
    record = {
        "created_utc": _utc(),
        "executor": executor,
        "title": title,
        "script": str(script),
        "command": argv,
        "applescript": osa,
        "dry_run": dry_run,
        "window_id": None,
    }

    if dry_run:
        record["note"] = "PREVIEW ONLY — no window opened, no worker launched."
        (run_dir / "launch.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return record

    if once.exists():
        record["refused"] = "already launched (.launcher-once present); will not double-launch."
        return record

    proc = subprocess.run(["osascript", "-e", osa], capture_output=True, text=True)
    if proc.returncode != 0:
        record["error"] = proc.stderr.strip()
        return record
    win = proc.stdout.strip()
    record["window_id"] = win
    once.write_text("", encoding="utf-8")
    (run_dir / "terminal-window.json").write_text(
        json.dumps({"window_id": win, "title": title}, indent=2) + "\n", encoding="utf-8")
    (run_dir / "launch.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record

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
import json, os, shlex, subprocess, datetime, uuid, fcntl
from pathlib import Path

CAFFEINATE = "/usr/bin/caffeinate"
TEE = "/usr/bin/tee"
SCRIPT = "/usr/bin/script"

# Profile-selecting variables carried from the coordinator into the worker window.
# Terminal.app's `do script` starts a fresh login shell that does NOT inherit the
# launching process's environment, so without this a worker silently falls back to
# the default profile (~/.claude, ~/.codex) instead of the coordinator's (e.g.
# ~/.claude-alternate). Paths only — never tokens or keys.
PROFILE_ENV_VARS = ("CLAUDE_CONFIG_DIR", "CODEX_HOME")

# =================== EDIT EXECUTION / PROFILE CHOICES HERE ===================
# Keep ONE executor assignment uncommented. None uses the dispatcher's choice.
# Normal fresh workers/coordinators/architects build the selected CLI command.
# Restricted legacy launch formats refuse incompatible switches rather than
# weaken their permissions. Reload the launcher after editing these settings.
EXECUTOR_OVERRIDE = None
# EXECUTOR_OVERRIDE = "claude"
# EXECUTOR_OVERRIDE = "codex"

# Keep ONE uncommented assignment per CLI. None keeps per-call/inherited settings.
# An explicit choice here wins over a caller's profile setting for that CLI.
# The actual selected CLI uses its own profile below. When switching engines,
# an incompatible caller model is omitted, using the destination CLI's default.
# Existing sessions keep their profiles. Paths only; never put keys/tokens here.
CLAUDE_PROFILE_DIR = None
# CLAUDE_PROFILE_DIR = Path.home() / ".claude"
# CLAUDE_PROFILE_DIR = Path.home() / ".claude-alternate"
# CLAUDE_PROFILE_DIR = Path.home() / ".claude-secondary"
# CLAUDE_PROFILE_DIR = Path.home() / ".claude-team"

CODEX_PROFILE_DIR = None
# CODEX_PROFILE_DIR = Path.home() / ".codex"
# CODEX_PROFILE_DIR = Path.home() / ".codex-work"  # must already exist
# ============================================================================

# Explicitly selectable alternative; inheritance remains the default. Paths only.
CLAUDE_PROFILES = {"alternate": str(Path.home() / ".claude-alternate")}


def execution_choice(requested: str, model: str | None = None, *, resume=None):
    """Select a fresh engine without transferring the other engine's model."""
    if EXECUTOR_OVERRIDE not in (None, "claude", "codex"):
        raise ValueError('EXECUTOR_OVERRIDE must be None, "claude" or "codex"')
    if requested not in ("claude", "codex"):
        raise ValueError("unsupported requested executor")
    if EXECUTOR_OVERRIDE is not None and resume:
        raise ValueError("executor override requires a fresh session")
    selected = EXECUTOR_OVERRIDE or requested
    return selected, model if selected == requested else None


def profile_env(environ=None) -> dict[str, str]:
    """The coordinator's profile-selecting variables that are set (non-empty)."""
    environ = os.environ if environ is None else environ
    return {k: environ[k] for k in PROFILE_ENV_VARS if environ.get(k)}


def _resumes_session(executor: str, argv: list[str]) -> bool:
    if executor.startswith("claude"):
        for arg in argv:
            if arg == "--":
                break
            if arg in ("--resume", "--continue", "-r", "-c", "--fork-session") or arg.startswith(("--resume=", "--continue=")):
                return True
        return False
    args = argv[1:] if argv and not argv[0].startswith("-") and argv[0] not in ("exec", "e", "resume", "fork") else argv
    # Only inspect Codex command positions. Config/model/prompt values can contain
    # "resume" without requesting a resume; in particular -c is Codex CONFIG.
    value_options = {"-c", "--config", "-m", "--model", "-p", "--profile", "-s", "--sandbox",
                     "-a", "--ask-for-approval", "-C", "--cd", "--add-dir", "--enable", "--disable",
                     "-i", "--image", "--output-schema", "-o", "--output-last-message", "--color"}
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            return False
        if arg in ("--resume", "--continue") or arg.startswith(("--resume=", "--continue=")):
            return True
        if arg in value_options:
            index += 2
        elif arg.startswith("-"):
            index += 1
        elif arg in ("resume", "fork"):
            return True
        elif arg in ("exec", "e"):
            index += 1
        else:
            return False
    return False


def launch_profile(executor: str, argv: list[str], claude_profile_dir=None, *, codex_profile_dir=None):
    """Resolve source selection, then per-call override, then inherited directories."""
    env = profile_env()
    if claude_profile_dir is not None and not executor.startswith("claude"):
        raise ValueError("Claude profile override requires a Claude executor")
    if codex_profile_dir is not None and not executor.startswith("codex"):
        raise ValueError("Codex profile override requires a Codex executor")
    if executor.startswith("claude"):
        selected = CLAUDE_PROFILE_DIR if CLAUDE_PROFILE_DIR is not None else claude_profile_dir
        variable = "CLAUDE_CONFIG_DIR"
    elif executor.startswith("codex"):
        selected = CODEX_PROFILE_DIR if CODEX_PROFILE_DIR is not None else codex_profile_dir
        variable = "CODEX_HOME"
    else:
        selected = None
    if selected is not None:
        if _resumes_session(executor, argv):
            raise ValueError("profile override requires a fresh session")
        path = Path(selected)
        if not path.is_absolute() or not path.is_dir():
            raise ValueError("profile must be an existing absolute directory")
        env[variable] = str(path.resolve())
    return env

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


def codex_headless_argv(cd: Path, prompt: str, *, full_auto: bool = False,
                        model: str | None = None, codex_bin: str = "codex") -> list[str]:
    """Bounded noninteractive role turn; bypass only if the caller already permits it."""
    argv = [codex_bin, "exec", "--skip-git-repo-check", "--cd", str(cd)]
    if full_auto:
        argv.append("--dangerously-bypass-approvals-and-sandbox")
    if model:
        argv += ["--model", model]
    return argv + ["--", prompt]


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
    env_vars = profile_env() if env is None else env
    if set(env_vars) - set(PROFILE_ENV_VARS):
        raise ValueError("only profile directory variables may be exported")
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
    if view.exists():
        return view
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    header = {"title": f"Visible session — {executor}", "type": "guide", "tags": [],
              "created": today, "updated": today, "sources": [],
              "document_schema": "aosdf-doc/v1",
              "id": "visible-session:doc:" + str(uuid.uuid5(uuid.NAMESPACE_URL, str(view.resolve()))),
              "summary": "Visible session launch, log and stop instructions.", "entities": []}
    # JSON scalars/lists are valid YAML; keep the launcher stdlib-only.
    frontmatter = "---\n" + "".join(f"{k}: {json.dumps(v, ensure_ascii=False)}\n"
                                         for k, v in header.items()) + "---\n"
    view.write_text(
        frontmatter + f"# Visible session — {executor}\n\n"
        f"A dedicated macOS Terminal window titled \"{title}\" runs `launch-visible.sh`.\n"
        "`terminal.log` mirrors everything shown in that window.\n\n"
        "**Stop:** Ctrl+C interrupts the session; inspect its claim/result before recovery.\n"
        "The launcher refuses a second launch of this run. Do not execute the shell script\n"
        "directly: that would bypass the launcher guard.\n\n"
        "Task ownership and authorization remain with the calling dispatcher.\n",
        encoding="utf-8",
    )
    return view


def launch_visible(run_dir: Path, executor: str, argv: list[str], *, title: str,
                   dry_run: bool = False, stdin_file: Path | None = None,
                   record_pid: bool = False, claude_profile_dir: str | None = None,
                   codex_profile_dir: str | None = None,
                   requested_executor: str | None = None) -> dict:
    """Open (or, with dry_run, preview) a visible Terminal window running argv.

    Returns a record with the script path, the AppleScript, and — on a real launch —
    the opened window id. Enforces a per-run `.launcher-once` guard against duplicates.
    """
    if EXECUTOR_OVERRIDE is not None:
        selected, _ = execution_choice(executor.split("-", 1)[0])
        if not executor.startswith(selected):
            raise ValueError("caller built a different executor; this launch format cannot apply EXECUTOR_OVERRIDE safely")
        if _resumes_session(executor, argv):
            raise ValueError("executor override requires a fresh session")
    env = launch_profile(executor, argv, claude_profile_dir, codex_profile_dir=codex_profile_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / ".visible-launch.lock").open("a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        return _launch_locked(run_dir, executor, argv, title=title, dry_run=dry_run,
                              stdin_file=stdin_file, record_pid=record_pid, env=env,
                              requested_executor=requested_executor or executor)


def _launch_locked(run_dir, executor, argv, *, title, dry_run, stdin_file, record_pid, env, requested_executor):
    once = run_dir / ".launcher-once"
    if once.exists():
        return {"refused": "already launched/reserved (.launcher-once present)",
                "window_id": None, "dry_run": dry_run}
    script = build_launch_script(run_dir, argv, stdin_file=stdin_file, record_pid=record_pid, env=env)
    write_view(run_dir, title, executor)
    osa = _osascript_text(script, title)
    record = {
        "created_utc": _utc(),
        "executor": executor,
        "requested_executor": requested_executor,
        "title": title,
        "script": str(script),
        "command": argv,
        "applescript": osa,
        "dry_run": dry_run,
        "window_id": None,
        "profile_env": env,
    }

    if dry_run:
        record["note"] = "PREVIEW ONLY — no window opened, no worker launched."
        (run_dir / "launch.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return record

    # A failed/ambiguous Terminal call also consumes the reservation: never retry blindly.
    once.write_text(_utc() + "\n", encoding="utf-8")
    (run_dir / "launch.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    proc = subprocess.run(["osascript", "-e", osa], capture_output=True, text=True)
    if proc.returncode != 0:
        record["error"] = proc.stderr.strip()
        (run_dir / "launch.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return record
    win = proc.stdout.strip()
    record["window_id"] = win
    (run_dir / "terminal-window.json").write_text(
        json.dumps({"window_id": win, "title": title}, indent=2) + "\n", encoding="utf-8")
    (run_dir / "launch.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record

#!/usr/bin/env python3
"""architect_invoke.py — invoke the Solution Architect to write an ARCHITECT block.

This is roadmap step 2 of the coordinator<->architect channel (see
`coordinator-architect/README.md` "Auto Mode" and the main `README.md` roadmap): the
architect write-back that `architect_bridge.py` *detects-and-triggers* when a coordinator
posts an `AWAITING-ARCHITECT` round. The founder's trigger is exactly that channel write:
one lead coordinator adding its `COORDINATOR -> ARCHITECT` round (status AWAITING-ARCHITECT)
is the event that calls the Solution Architect.

Separation of concerns (same shape as the worker path):
  * visible_launch.py  = the launch MECHANISM (a visible, watchable Terminal window).
  * architect_invoke.py = builds the architect's boot prompt + the launch, dry-run previewable.
  * architect_bridge.py --auto = the GATE that decides WHETHER this may run live.

Like `supervisor.py --dispatch` and `--pilot-real`, the live path is dual-gated and off by
default; `dry_run=True` (the default for preview) opens nothing and returns the exact prompt
and command that WOULD run. This module never writes into the channel itself — only the
launched architect session writes the ARCHITECT block, by hand, under its own role rules.
It grants no authorization: the architect it launches still cannot cross a hard gate
(it ESCALATEs instead). Status authority stays `execution_plan.md`; Thread 1 stays sole writer.

Usage (normally called by architect_bridge, but runnable directly for preview/pilot):
    python3 architect_invoke.py --preview 2            # build+print the prompt/command, launch nothing
    python3 architect_invoke.py --invoke 2             # live launch (refused unless the bridge dual-gate is set)
    python3 architect_invoke.py --preview 2 --model opus
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys

import architect_bridge as _bridge
import visible_launch as _vl
import wave as _wave

HERE = os.path.dirname(os.path.abspath(__file__))
VAR_DIR = os.path.join(HERE, "var")
RUNS_DIR = os.path.join(VAR_DIR, "architect-runs")

# Workspace root (holds AGENTS.md) — up 6 from automation/.
REPO_ROOT = os.path.normpath(os.path.join(HERE, *([os.pardir] * 6)))
# 05_AI_Agent_System dir — up 2 from automation/.
AGENT_SYS_DIR = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir))
# coordination-threads dir — up 1 from automation/ (holds SPRINT-TRACKER.md).
THREADS_DIR = os.path.normpath(os.path.join(HERE, os.pardir))
SPRINT_TRACKER = os.path.join(THREADS_DIR, "SPRINT-TRACKER.md")
# documents/ dir — up 3 from automation/ (holds 06_Execution_Plan/).
DOCS_DOCUMENTS_DIR = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))
EXEC_PLAN = os.path.join(DOCS_DOCUMENTS_DIR, "06_Execution_Plan", "execution_plan.md")

DEFAULT_MODEL = "opus"  # planning/verification role -> frontier model


def _utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _thread_channel_path(thread_n: int) -> str:
    return os.path.join(_bridge.CHANNEL_DIR, f"thread{thread_n}.md")


def owed_round(thread_n: int):
    """Return the thread's latest round dict iff it currently owes the architect, else None."""
    latest = _bridge._latest_round(_thread_channel_path(thread_n))
    return latest if _bridge._owed(latest) else None


def boot_prompt(thread_n: int, round_rec: dict) -> str:
    """The single boot line that points the launched Solution Architect at its files.

    Behaviour lives in the files, not the prompt (founder directive 2026-10-23): the prompt
    only names what to read and the one bounded thing to do.
    """
    agents_md = os.path.join(REPO_ROOT, "AGENTS.md")
    channel_readme = os.path.join(_bridge.CHANNEL_DIR, "README.md")
    role_def = os.path.join(AGENT_SYS_DIR, "agents", "solution_architect_agent.md")
    thread_md = _thread_channel_path(thread_n)
    k = round_rec.get("round")
    checkpoint = round_rec.get("checkpoint")
    wave_text = _wave.boot_addendum(_wave.active_wave())
    return (
        f"You are the Solution Architect for the Example Project coordination system. You were "
        f"auto-invoked because the Thread {thread_n} coordinator opened alignment round {k} "
        f"(checkpoint: {checkpoint}, status AWAITING-ARCHITECT). "
        f"Read, in order: {agents_md}; {role_def}; {channel_readme}; then the open round in "
        f"{thread_md}. Read anything else you need to judge it — the canonical execution_plan.md, "
        f"the milestone acceptance criteria, the governing ADRs, identified_gaps.md, the manual-action "
        f"tracker, live code/contracts/migrations, and the other threads' channel files — you are not "
        f"limited to the channel file. Your remit is narrow: confirm the proposed next scope/partition is "
        f"correct and that tasks are divided across threads with no overlap or conflict. "
        f"If this is a PRE-DISPATCH check (checkpoint 'pre-dispatch': the coordinator names the exact task "
        f"batch and the single worker it is about to launch), your job is specifically to PREVENT "
        f"duplicate or overlapping work: verify every task in the batch is in-scope for this thread's "
        f"sprint, is not already accepted/done, is not already covered by a live worker or the other "
        f"thread, and that the batch is dispatched as ONE worker (not one worker per task). Return ALIGNED "
        f"to authorize that single batched dispatch; REDIRECT to correct it (drop an already-done task, "
        f"merge a needless split, or re-partition an overlap); HOLD/ESCALATE if it cannot proceed. "
        f"Write ONLY the `ARCHITECT -> COORDINATOR` block for round {k} in {thread_md}, set that round's "
        f"machine-comment status token to your verdict (ALIGNED | REDIRECT | HOLD | ESCALATE), and stop. "
        f"Do NOT write code, a worker task.md, execution_plan.md status, or implementation_prompts plans, "
        f"and do NOT cross or grant any hard gate (push/deploy/publish, DNS, live-send, spend, secrets, "
        f"live-data deletion, Class-B/C) — for anything requiring a founder decision, use ESCALATE and name "
        f"exactly what the founder must decide and why. Apply the architect autonomy policy in your role "
        f"definition: decide and proceed within your remit; do not ask routine questions. When the block is "
        f"written, print one line: 'Thread {thread_n} round {k} -> <verdict>'. "
        + _wave.OWNERSHIP_ARCHITECT
        + wave_text
    )


def manual_boot_prompt(topic: str | None) -> str:
    """Boot line for a founder-initiated, interactive architect session (not tied to a round).

    Request (founder 2026-10-28): "a manual thread of the Solution Architect can be called by the
    founder to address changes in model selection or anything required."
    """
    agents_md = os.path.join(REPO_ROOT, "AGENTS.md")
    role_def = os.path.join(AGENT_SYS_DIR, "agents", "solution_architect_agent.md")
    channel_readme = os.path.join(_bridge.CHANNEL_DIR, "README.md")
    focus = (f"The founder wants to discuss: {topic}. " if topic
             else "The founder will tell you what to address (e.g. model selection, a scope or "
                  "partition question, a wave change). ")
    return (
        f"You are the Solution Architect for the Example Project coordination system, launched MANUALLY and "
        f"INTERACTIVELY by the founder (not auto-invoked by a channel round). {focus}"
        f"Read, as needed: {agents_md}; {role_def}; {channel_readme}; and the canonical sources. "
        f"This is a conversation: discuss, decide and act within your remit and the architect autonomy "
        f"policy in your role definition. You MAY update the automation wave (config/wave.json via "
        f"wave.py), the architect/coordinator model choices, and alignment rounds. Do NOT cross or grant "
        f"any hard gate (push/deploy/publish, DNS, live-send, spend, secrets, live-delete, Class-B/C) — "
        f"name those for the founder to decide. "
        + _wave.OWNERSHIP_ARCHITECT
    )


def wave_boot_prompt(wave: dict) -> str:
    """Boot line for a wave BEGIN/CONTINUE launch from initiate_automation.py's single command.

    The founder has just chosen (interactively) to start or continue this wave, so this is a
    founder-initiated launch, not the unattended auto-daemon path. The architect maps the wave's
    sprints to the canonical plan + tracker, confirms partitions, and opens the first alignment
    round per thread so the coordinators can proceed. The wave autonomy (no per-sprint approval)
    is carried by the wave addendum; hard gates still stop it via ESCALATE.
    """
    agents_md = os.path.join(REPO_ROOT, "AGENTS.md")
    role_def = os.path.join(AGENT_SYS_DIR, "agents", "solution_architect_agent.md")
    channel_readme = os.path.join(_bridge.CHANNEL_DIR, "README.md")
    threads = ", ".join(sorted({str(s.get("thread")) for s in wave.get("sprints", [])}))
    return (
        f"You are the Solution Architect for the Example Project coordination system, launched by the founder "
        f"to BEGIN/CONTINUE automation wave {wave.get('wave_id')} ('{wave.get('title','')}'). "
        f"Read, in order: {agents_md}; {role_def}; {channel_readme}; the canonical plan {EXEC_PLAN}; and "
        f"the sprint view {SPRINT_TRACKER}. Also read whatever you need to judge scope — the milestone "
        f"acceptance criteria, governing ADRs, identified_gaps.md, the manual-action tracker, and live "
        f"code/contracts/migrations. "
        f"For each sprint in this wave: map its execution_plan.md tasks onto SPRINT-TRACKER.md and mark "
        f"them 'mapped'; confirm the thread partition (threads {threads}) is correct and non-overlapping. "
        f"Before any coordinator launch, record exact ordered task_ids, scope_review_ref, model_policy, "
        f"target_tier and founder_auth_ref "
        f"and the new opening_round number for each sprint in config/wave.json; set "
        f"verified_by_architect=true only after objective, hold, tier and ownership checks pass. "
        f"For a founder-approved wave only, open the numbered "
        f"bootstrap alignment round (bootstrap:wave:<id>) for each thread's coordinator in "
        f"{os.path.join(_bridge.CHANNEL_DIR, 'thread<N>.md')} (write your ARCHITECT verdict ALIGNED with the "
        f"next bounded scope so the coordinator_trigger can launch it). Advance the wave's sprints without "
        f"returning to the founder between sprints. When a sprint's acceptance passes, mark its tasks "
        f"'completed' in the tracker and reconcile that into execution_plan.md. "
        + _wave.OWNERSHIP_ARCHITECT
        + _wave.boot_addendum(wave)
    )


def invoke_wave(wave: dict, *, dry_run: bool = False, model: str = DEFAULT_MODEL,
                claude_bin: str = "claude") -> dict:
    """Open a visible Solution Architect window to begin/continue a founder-approved wave.

    Founder-initiated from initiate_automation.py (the founder just confirmed at the terminal), so
    it is NOT dual-gated the way the unattended --auto write-back is. Interactive (the founder can
    watch and intervene); the launched architect still cannot cross a hard gate (it ESCALATEs)."""
    from pathlib import Path
    rec = {"created_utc": _utc(), "mode": "wave-begin", "wave_id": wave.get("wave_id"),
           "model": model, "dry_run": dry_run}
    prompt = wave_boot_prompt(wave)
    rec["prompt"] = prompt
    argv = _vl.claude_argv(Path(REPO_ROOT), prompt, model=model, claude_bin=claude_bin)
    run_dir = Path(RUNS_DIR) / "wave" / f"{wave.get('wave_id','wave')}-{_dt.datetime.now().strftime('%Y%m%dT%H%M%S')}"
    title = f"Example Project — Solution Architect — WAVE {wave.get('wave_id','?')} (founder)"
    rec["launch"] = _vl.launch_visible(run_dir, "claude-architect-wave", argv, title=title, dry_run=dry_run)
    return rec


def invoke_manual(topic: str | None = None, *, dry_run: bool = False, model: str = DEFAULT_MODEL,
                  claude_bin: str = "claude") -> dict:
    """Open an interactive Solution Architect window for an ad-hoc founder discussion. Founder-
    initiated and interactive (the founder approves actions in-window), so it is NOT dual-gated the
    way the automatic write-back is."""
    from pathlib import Path
    rec = {"created_utc": _utc(), "mode": "manual", "topic": topic, "model": model, "dry_run": dry_run}
    prompt = manual_boot_prompt(topic)
    rec["prompt"] = prompt
    # Interactive session (no skip-permissions / no plan-lock): the founder drives it.
    argv = _vl.claude_argv(Path(REPO_ROOT), prompt, model=model, claude_bin=claude_bin)
    run_dir = Path(RUNS_DIR) / "manual" / _dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    title = "Example Project — Solution Architect — MANUAL (founder)"
    rec["launch"] = _vl.launch_visible(run_dir, "claude-architect-manual", argv, title=title, dry_run=dry_run)
    return rec


def _run_dir(thread_n: int, round_rec: dict) -> str:
    sig = f"round{round_rec.get('round')}-{round_rec.get('status')}"
    return os.path.join(RUNS_DIR, f"thread{thread_n}", sig)


def invoke(thread_n: int, *, dry_run: bool = True, model: str = DEFAULT_MODEL,
           claude_bin: str = "claude") -> dict:
    """Invoke (or, with dry_run, preview) the Solution Architect for one owed thread round.

    Opens a visible, watchable Terminal window (reusing visible_launch), exactly like a worker,
    so the founder can watch the architect reason and write its block live. Returns a record.
    """
    round_rec = owed_round(thread_n)
    rec = {"created_utc": _utc(), "thread": thread_n, "model": model, "dry_run": dry_run}
    if round_rec is None:
        rec["skipped"] = (f"Thread {thread_n} does not currently owe the architect "
                          f"(latest round is not AWAITING-ARCHITECT). Nothing to invoke.")
        return rec
    rec["round"] = round_rec
    from pathlib import Path
    run_dir = Path(_run_dir(thread_n, round_rec))
    prompt = boot_prompt(thread_n, round_rec)
    rec["prompt"] = prompt
    argv = _vl.claude_argv(
        Path(REPO_ROOT), prompt,
        skip_permissions=True, model=model, claude_bin=claude_bin,
    )
    title = f"Example Project — Solution Architect — thread{thread_n} round{round_rec.get('round')}"
    launch = _vl.launch_visible(run_dir, "claude-architect", argv, title=title, dry_run=dry_run)
    rec["launch"] = launch
    return rec


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Invoke the Solution Architect to write an ARCHITECT block.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--preview", type=int, metavar="THREAD",
                   help="build + print the boot prompt and the command that WOULD launch; launch nothing")
    g.add_argument("--invoke", type=int, metavar="THREAD",
                   help="live launch (refused here unless the bridge dual-gate is set)")
    g.add_argument("--manual", nargs="?", const="", metavar="TOPIC",
                   help="open an INTERACTIVE architect window for a founder discussion (optional topic); "
                        "not gated — founder-initiated")
    p.add_argument("--preview-only", action="store_true", help="with --manual: build but do not open the window")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"claude model (default {DEFAULT_MODEL})")
    args = p.parse_args(argv)

    if args.manual is not None:
        topic = args.manual or None
        rec = invoke_manual(topic, dry_run=args.preview_only, model=args.model)
        print(json.dumps(rec, indent=2))
        return 0

    if args.preview is not None:
        rec = invoke(args.preview, dry_run=True, model=args.model)
        print(json.dumps(rec, indent=2))
        return 0

    # --invoke: live path is gated exactly like the bridge's --auto. Do not fire live from here
    # unless the config gate is set; the bridge is the single place that owns the live decision.
    if not _bridge._auto_enabled():
        print("LIVE invoke REFUSED: the architect auto-write gate is not set.")
        print("  gate 1 (config auto_writeback=authorized): not set")
        print("  Use `--preview` here, or enable via architect_bridge.py --auto once wired+authorized.")
        return 2
    rec = invoke(args.invoke, dry_run=False, model=args.model)
    print(json.dumps(rec, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

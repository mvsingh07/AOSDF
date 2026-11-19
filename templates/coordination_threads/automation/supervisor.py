#!/usr/bin/env python3
"""Dispatcher/supervisor (automation-proposal.md §5,7,10 — Stage 2).

REAL DISPATCH IS HARD-DISABLED. Two things are intentionally separate here:

  * `--dispatch AGENT` previews the REAL launch command and REFUSES. Enabling a real launch
    requires BOTH config `stage` >= 2 AND `--i-have-reviewed-and-authorized-stage2`, and even
    then this skeleton's real path returns STOP — it is NOT wired to a real `codex exec` /
    `claude --resume`. That wiring happens only at the founder-authorized pilot.

  * `--pilot-fake AGENT` runs the full Stage-2 loop through the VALIDATED components
    (dispatch_core, ownership, scope, authz, result, consume, retry) using a FAKE worker in
    an isolated sandbox. No real model, no shared app, no live operation, and it never touches
    the live thread folders. This is the review's step-1 "fake worker executables and temporary
    repos" validation.
"""
from __future__ import annotations
import argparse, json, shutil, sys, tempfile, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dispatch_core          # noqa: E402
import ownership              # noqa: E402
import scope as scope_mod     # noqa: E402
import authz                  # noqa: E402
import result as result_mod   # noqa: E402
import consume                # noqa: E402
import retry as retry_mod     # noqa: E402
import fakeworker             # noqa: E402
import watchdog               # noqa: E402
import baseline as baseline_mod  # noqa: E402
import visible_launch as vlaunch  # noqa: E402
import sprint                      # noqa: E402


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _find_agent(config: dict, agent_name: str):
    for thread in config.get("threads", []):
        for ag in thread.get("agents", []):
            if ag["agent"] == agent_name:
                return dict(ag, thread=thread["thread"])
    return None


def would_launch(agent: dict, folder: Path) -> str:
    """The REAL launch command shape per executor (NEVER executed here)."""
    if agent.get("model") == "codex":
        return (f"codex exec --cd <repo> \"Read AGENTS.md, coordination-threads/README.md and this "
                f"agent's {folder}/context.md + task.md; follow AOSDF Strategy B; do not pick your own "
                f"next task.\"")
    return (f"claude --resume <session-id> \"Read AGENTS.md + {folder}/context.md + task.md; follow "
            f"AOSDF Strategy B; do not pick your own next task, review another worker, push, deploy, or "
            f"run a live action.\"")


def _worker_prompt(folder: Path) -> str:
    """The bounded worker boot instruction — one line, identical for both executors.

    The full instructions live in coordination-threads/worker-definition.md (role, Strategy B, hard
    limits, output contract), not in this prompt — the founder's 2026-10-23 directive to keep behaviour
    in files, not in the launch prompt."""
    return (f"You are this agent's execution worker. Read AGENTS.md, then "
            f"coordination-threads/worker-definition.md, then {folder}/context.md and {folder}/task.md, "
            f"and do EXACTLY what the worker definition says for the ONE task in task.md — then STOP. "
            f"The definition carries your Strategy-B loop, hard limits, and output contract; follow it.")


def _visible_worker_launch(target: dict, folder: Path, run_dir: Path, *, dry_run: bool,
                           profile: str = "impl", launch_mode: str = "full-auto",
                           model: str | None = None, resume: str | None = None) -> dict:
    """Open (or preview) a visible Terminal window for this agent's worker.

    profile='impl' (default) opens an interactive session in which the worker writes its own files;
    profile='doc' opens the locked-down read-only Codex-exec profile used by the documentation pilot.

    launch_mode (impl only) picks how much the founder approves:
      'full-auto'   — `codex --yolo` / `claude --dangerously-skip-permissions`; the worker runs
                      unattended like the coordinators and the founder watches the live window
                      (founder's choice 2026-10-23).
      'interactive' — the tool's own per-action approval prompts fire; the founder approves each step.

    Both open in a titled window under caffeinate, teed to terminal.log.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt = _worker_prompt(folder)
    executor = target.get("model", "claude")
    tag = profile if profile == "doc" else launch_mode
    mtag = f", {model}" if model else ""
    title = f"Example Project — {target['agent']} ({executor}, {tag}{mtag}) — thread{target['thread']}"
    full_auto = (profile != "doc" and launch_mode == "full-auto")
    if executor == "codex":
        if profile == "doc":
            stdin_file = run_dir / "worker-input.txt"
            stdin_file.write_text(prompt + "\n", encoding="utf-8")
            argv = vlaunch.codex_argv(folder)
            return vlaunch.launch_visible(run_dir, executor, argv, title=title,
                                          dry_run=dry_run, stdin_file=stdin_file)
        argv = vlaunch.codex_interactive_argv(folder, prompt, yolo=full_auto, model=model)
        return vlaunch.launch_visible(run_dir, executor, argv, title=title, dry_run=dry_run)
    # claude
    if profile == "doc":
        argv = vlaunch.claude_argv(folder, prompt, resume=resume, permission_mode="plan", model=model)
    else:
        argv = vlaunch.claude_argv(folder, prompt, resume=resume, skip_permissions=full_auto, model=model)
    return vlaunch.launch_visible(run_dir, executor, argv, title=title, dry_run=dry_run)


def assign(config_path: Path, agent_name: str, preview: bool = False) -> int:
    """Open the ALREADY-ASSIGNED worker (its current task.md) in a visible interactive Terminal.

    This is the founder's authorized 'assign automation' path (standing authorization in config:
    "assign_launch":"authorized"). It is SEPARATE from full automation: it launches exactly the one
    task the coordinator has written, never selects the next task itself, and never auto-recovers a
    writing worker. Hard action gates (push/deploy/DNS/live-send/spend/secrets/Class-B-C) stay with
    the worker's own approval + the founder watching."""
    config = _load_json(config_path)
    if config is None:
        print(f"ERROR: cannot read config {config_path}", file=sys.stderr)
        return 2
    coord_root = (config_path.parent / config.get("coordination_root", "..")).resolve()
    target = _find_agent(config, agent_name)
    if target is None:
        print(f"ERROR: agent {agent_name} not in topology", file=sys.stderr)
        return 2
    folder = coord_root / f"thread{target['thread']}" / agent_name

    print(f"=== assign({agent_name}) — {_utc()} ===")
    if config.get("assign_launch") != "authorized" and not preview:
        print("\nREFUSED: assign-launch is not authorized. Set \"assign_launch\": \"authorized\" in the")
        print("  topology config (founder standing directive 2026-10-23) to let the coordinator open")
        print("  the assigned worker's window. Or use --assign --preview-launch to see it first.")
        return 1

    state = _load_json(folder / "state.json") or {}
    status = state.get("status")
    seq = int(state.get("dispatch_sequence", 0))
    if status not in ("ready", "running"):
        print(f"\nHOLD: {agent_name} status is '{status}'. There is no assignment to launch. The")
        print("  coordinator must write task.md (replace) and set state.json ready first.")
        return 1
    if not (folder / "task.md").exists():
        print(f"\nHOLD: {folder}/task.md is missing. Nothing assigned to launch.")
        return 1

    launch_mode = config.get("worker_launch_mode", "full-auto")
    # pick up the sprint's chosen model (Q2), if a sprint is recorded for this thread
    model = None
    sp = sprint.load(sprint.sprint_path(coord_root / f"thread{target['thread']}"))
    if sp:
        model = sp.get("model")
        print(f"[sprint] {sprint.summary_line(sp)}")
    run_dir = folder / "runs" / f"{seq:03d}"
    rec = _visible_worker_launch(target, folder, run_dir, dry_run=preview, profile="impl",
                                 launch_mode=launch_mode, model=model)
    mode_word = "full-auto (unattended, you watch)" if launch_mode == "full-auto" else "interactive (you approve)"
    if preview:
        print(f"PREVIEW ONLY — the visible {mode_word} window that WOULD open (nothing launched):")
    else:
        print(f"Opening the assigned worker (seq {seq:03d}) in a visible {mode_word} window:")
    _print_launch_record(rec)
    if not preview and rec.get("window_id"):
        print("\n  Watch it in that window. Safe stop: Ctrl+C there.")
        print("  When the worker finishes, follow the coordinator switch prompt to summarize + assign next.")
    return 0 if (preview or rec.get("window_id") or rec.get("refused")) else 3


def _print_launch_record(rec: dict) -> None:
    print(f"  executor : {rec['executor']}")
    print(f"  window   : {rec['title']}")
    print(f"  command  : {' '.join(rec['command'])}")
    print(f"  script   : {rec['script']}")
    if rec.get("window_id"):
        print(f"  OPENED   : Terminal window id {rec['window_id']} (watch it; terminal.log mirrors it)")
    if rec.get("refused"):
        print(f"  REFUSED  : {rec['refused']}")
    if rec.get("error"):
        print(f"  ERROR    : {rec['error']}")
    if rec.get("note"):
        print(f"  note     : {rec['note']}")


def dispatch(config_path: Path, agent_name: str, authorized: bool, preview_only: bool = False) -> int:
    """REAL dispatch. Opens a VISIBLE Terminal window for the worker when authorized
    (config stage>=2 AND --i-have-reviewed-and-authorized-stage2). Otherwise previews the
    exact window that WOULD open and launches nothing."""
    config = _load_json(config_path)
    if config is None:
        print(f"ERROR: cannot read config {config_path}", file=sys.stderr)
        return 2
    coord_root = (config_path.parent / config.get("coordination_root", "..")).resolve()
    target = _find_agent(config, agent_name)
    if target is None:
        print(f"ERROR: agent {agent_name} not in topology", file=sys.stderr)
        return 2
    folder = coord_root / f"thread{target['thread']}" / agent_name

    stage = config.get("stage", 1)
    gated_out = preview_only or stage < 2 or not authorized
    print(f"=== dispatch({agent_name}) — {_utc()} — stage {stage} ===")

    if gated_out:
        # Preview writes to a throwaway dir — NEVER into a live run folder.
        import tempfile
        with tempfile.TemporaryDirectory(prefix=f"preview-{agent_name}-") as tmp:
            print("PREVIEW ONLY — the visible launch that WOULD open (nothing launched):")
            rec = _visible_worker_launch(target, folder, Path(tmp), dry_run=True)
            _print_launch_record(rec)
        reason = ("--preview-launch (explicit preview)" if preview_only else
                  "config stage < 2" if stage < 2 else
                  "missing --i-have-reviewed-and-authorized-stage2")
        print(f"\nNot launched. Reason: {reason}.")
        print("  At stage 1, dispatch MANUALLY or run --pilot-fake. When the founder authorizes")
        print("  live dispatch (stage>=2 + the flag), this same command opens the window for real.")
        return 1 if not preview_only else 0

    # Real dispatch: allocate the NEXT rolling run folder; never reuse/clobber an existing one.
    state = _load_json(folder / "state.json") or {}
    next_seq = int(state.get("dispatch_sequence", 0)) + 1
    run_dir = folder / "runs" / f"{next_seq:03d}"
    if run_dir.exists():
        print(f"\nREFUSED: next run folder {run_dir} already exists; the Lead must consume the current")
        print("  dispatch (advance state.json) before a new one is allocated. Not launching.")
        return 1
    print(f"AUTHORIZED — opening a visible Terminal window for the worker (run {next_seq:03d}):")
    rec = _visible_worker_launch(target, folder, run_dir, dry_run=False)
    _print_launch_record(rec)
    print("\n  Safe stop: Ctrl+C in that window. Run `supervisor.py --watchdog` alongside.")
    print("  The worker runs ONE bounded task and exits; it never picks its own next task.")
    return 0 if rec.get("window_id") else 3


def _pilot_task_text() -> str:
    return ("# FAKE PILOT TASK (throwaway sandbox)\n\n"
            "Exercises the Stage-2 loop with a FAKE worker. No real model, no live op.\n\n"
            "Read alongside this task: (none — pilot). What happens if a worker resumes with a "
            "stale fence?\n")


def fake_pilot(config_path: Path, agent_name: str, scenario: str = "ok") -> int:
    """Run the full Stage-2 loop through the validated components with a FAKE worker, in an
    isolated sandbox. Never touches live thread folders; launches no real model."""
    config = _load_json(config_path)
    if config is None:
        print(f"ERROR: cannot read config {config_path}", file=sys.stderr)
        return 2
    target = _find_agent(config, agent_name)
    if target is None:
        print(f"ERROR: agent {agent_name} not in topology", file=sys.stderr)
        return 2

    sandbox = Path(tempfile.mkdtemp(prefix="stage2-fake-pilot-"))
    try:
        t = target["thread"]
        folder = sandbox / f"thread{t}" / agent_name
        folder.mkdir(parents=True)
        seq, run_id = 1, f"fake-{agent_name}-001"
        (folder / "task.md").write_text(_pilot_task_text(), encoding="utf-8")

        print(f"=== FAKE-WORKER PILOT — {agent_name} (model {target.get('model')}) — {_utc()} ===")
        print(f"    scenario={scenario}   sandbox={sandbox}")
        print("    NO real model is launched; NO live operation; live thread folders untouched.\n")

        # 1) immutable envelope + learning fields
        env = dispatch_core.build_envelope(folder, seq, run_id)
        print(f"  [1] envelope: task_sha256={env['task_sha256'][:16]}…  learning_present={env['learning_present']}")

        # 2) ownership leases (sandbox registry)
        reg = ownership.empty_registry()
        owned = [o for o in target.get("owned_write_targets", []) if "no source" not in o.lower()]
        try:
            ownership.acquire_paths(reg, agent_name, 1, owned)
            print(f"  [2] ownership: leased {len(owned)} write target(s) exclusively  OK")
        except ownership.OwnershipConflict as e:
            print(f"  [2] ownership: CONFLICT {e}")

        # 3) scope allowlist (prompt text is not a boundary)
        pol = scope_mod.pilot_policy()
        d_ok = scope_mod.check_action(pol, "run-test", str(folder), "dev-disposable")
        d_no = scope_mod.check_action(pol, "deploy", "# totally safe", "dev-disposable")
        print(f"  [3] scope: run-test -> allowed={d_ok['allowed']}; deploy -> allowed={d_no['allowed']} "
              f"({d_no['reason']})")

        # 4) authorization (stage flag authorizes nothing)
        try:
            authz.execute_guard([], {"action": "apply-migration", "environment": "dev-disposable",
                                     "target": "mig:9999", "effect": "mutate"}, stage_authorized=True)
            print("  [4] authz: UNEXPECTEDLY allowed a mutate with no record")
        except authz.NotAuthorized:
            print("  [4] authz: mutate without an explicit record REFUSED (stage flag ignored)  OK")

        # 5) fake worker: fenced claim -> ack -> fenced completion
        out = fakeworker.run_fake(folder, owner="pilot", behavior=scenario, sequence=seq, run_id=run_id)
        print(f"  [5] worker: claimed={out['claimed']} fence={out['fence']} completed={out['completed']}"
              + (f" refused={out['refused']}" if out.get("refused") else "")
              + (f" note={out['note']}" if out.get("note") else ""))

        if scenario == "crash" and out["claimed"] and not out["completed"]:
            dup = fakeworker.run_fake(folder, owner="pilot-2", behavior="ok", sequence=seq, run_id=run_id)
            print(f"  [5b] concurrent 2nd launch refused (claim held): refused={dup['refused'] is not None}")
            print("       recovery is an EXPLICIT coordinator action (dispatch_core.recover), not automatic.")

        # 6) structured result + validation + exactly-once consume
        if out["completed"]:
            gate_status = "fail" if scenario == "fail-gate" else "pass"
            res = {
                "run_id": run_id, "sequence": seq, "agent": agent_name,
                "task_sha256": env["task_sha256"], "fence": out["fence"], "stage": "local",
                "created_utc": _utc(), "canonical_task_ids": target.get("canonical_task_ids", []),
                "gates": [
                    {"name": "fake-gate", "kind": "required", "status": gate_status,
                     "evidence": "fake worker synthetic evidence"},
                    {"name": "lint", "kind": "optional", "status": "skip"},
                ],
                "teaches": {"changed_behavior": "pilot", "example_ref": "sandbox",
                            "limitation": "fake worker; not a real task", "self_check": "fence?"},
            }
            ok, reasons = result_mod.is_acceptable(res, env)
            print(f"  [6] result: acceptable={ok}" + (f" reasons={reasons}" if reasons else "")
                  + f"  (stage=local, claims_live={result_mod.acceptance(res, env)['claims_live']})")
            journal = sandbox / "var" / "consume-journal.json"
            c1 = consume.consume(res, journal, env)
            c2 = consume.consume(res, journal, env)
            ann = c1["annotation"]
            print(f"  [7] consume: first={c1['status']} second={c2['status']} (exactly-once)  "
                  f"proposed annotation kind={ann['kind']}, accepted={ann['accepted']}")
            print("      (annotation is a PROPOSAL for the Lead Coordinator; automation writes no canonical status)")
        else:
            print(f"  [6] no completion to consume (scenario={scenario}).")

        # 8) retry/progress policy
        led = retry_mod.empty_ledger()
        can, why = retry_mod.can_retry(led)
        print(f"  [8] retry policy (fresh ledger): can_retry={can} ({why})")

        print("\n  DONE. Full loop exercised with a fake worker. Nothing live was launched or mutated.")
        return 0
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


# ----------------------------------------------------------------------------------------
# Product-specific real pilot removed: its scope and authorization do not transfer.
def pilot_real(*args, **kwargs):
    print("REFUSED: reusable templates have no real-launch authorization")
    return 2


def pilot_consume(*args, **kwargs):
    print("REFUSED: no product pilot exists in reusable templates")
    return 2


def watchdog_once(config_path: Path, recover: bool) -> int:
    """Report each agent's live-claim health; with --recover, safely reclaim orphans only."""
    config = _load_json(config_path)
    if config is None:
        print(f"ERROR: cannot read config {config_path}", file=sys.stderr)
        return 2
    coord_root = (config_path.parent / config.get("coordination_root", "..")).resolve()
    rows = watchdog.scan(config, coord_root)
    print(f"=== watchdog — {_utc()} ===")
    print(watchdog.report_text(rows))
    orphans = [r["agent"] for r in rows if r["state"] == "orphan"]
    due = [r["agent"] for r in rows if r["state"] == "checkpoint_due"]
    if due:
        print(f"\nCHECKPOINT DUE (compact + re-dispatch a fresh session): {', '.join(due)}")
    if orphans and not recover:
        print(f"\nORPHANS detected (crashed/slept/disconnected): {', '.join(orphans)}")
        print("  Re-run with --recover to safely retire their dead claims (no double-run).")
    if recover:
        reclaimed = watchdog.sweep(config, coord_root)
        print(f"\nrecovered orphans: {', '.join(reclaimed) if reclaimed else '(none)'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Dispatcher/supervisor (real dispatch hard-disabled)")
    ap.add_argument("--config", default=str(HERE / "config" / "adr-025.topology.json"))
    ap.add_argument("--assign", metavar="AGENT", help="open AGENT's already-assigned worker in a visible interactive window (founder assign-automation)")
    ap.add_argument("--dispatch", metavar="AGENT", help="full-automation dispatch in a visible Terminal (gated: stage>=2)")
    ap.add_argument("--preview-launch", metavar="AGENT", help="show the visible window that WOULD open; launch nothing")
    ap.add_argument("--preview", action="store_true", help="with --assign, preview the worker window without opening it")
    ap.add_argument("--i-have-reviewed-and-authorized-stage2", dest="authorized", action="store_true")
    ap.add_argument("--pilot-fake", metavar="AGENT", help="run the full loop with a FAKE worker in a sandbox")
    ap.add_argument("--scenario", default="ok", choices=["ok", "fail-gate", "crash", "edit-task", "no-ack"],
                    help="fake-worker behaviour for --pilot-fake")
    ap.add_argument("--watchdog", action="store_true", help="report each agent's live-claim health")
    ap.add_argument("--recover", action="store_true", help="with --watchdog, safely reclaim orphan claims")
    ap.add_argument("--pilot-real", metavar="AGENT", help="run the ONE authorized real-launch pilot (gated)")
    ap.add_argument("--pilot-authorize", metavar="TOKEN", default=None, help="per-pilot authorization token")
    ap.add_argument("--pilot-consume", action="store_true", help="capture + consume the pilot worker's result")
    ap.add_argument("--sprint-models", action="store_true", help="print the Q2 LLM/model options + suggestions")
    ap.add_argument("--sprint-show", metavar="THREAD", type=int, help="show the sprint + progress for thread N")
    args = ap.parse_args()

    config_path = Path(args.config).resolve()
    if args.sprint_models:
        print(sprint.model_menu_text()); return 0
    if args.sprint_show is not None:
        config = _load_json(config_path) or {}
        coord_root = (config_path.parent / config.get("coordination_root", "..")).resolve()
        sp = sprint.load(sprint.sprint_path(coord_root / f"thread{args.sprint_show}"))
        if not sp:
            print(f"No sprint recorded for thread{args.sprint_show}. First run: coordinator asks Q1+Q2, then records it.")
            return 0
        print(sprint.summary_line(sp))
        for t in sp["tasks"]:
            print(f"  {t['status']:<8} {t['id']:<12} {t.get('agent',''):<10} {t.get('name','')}")
        return 0
    if args.pilot_consume:
        return pilot_consume(config_path)
    if args.pilot_real:
        return pilot_real(config_path, args.pilot_real, args.pilot_authorize)
    if args.watchdog or args.recover:
        return watchdog_once(config_path, args.recover)
    if args.pilot_fake:
        return fake_pilot(config_path, args.pilot_fake, args.scenario)
    if args.preview_launch:
        return dispatch(config_path, args.preview_launch, args.authorized, preview_only=True)
    if args.assign:
        return assign(config_path, args.assign, preview=args.preview_launch is not None or args.preview)
    if args.dispatch:
        return dispatch(config_path, args.dispatch, args.authorized)
    print("Supervisor. Stage 1 = observe + assign-launch (founder assign-automation).")
    print("  --assign <agent>         open the agent's ASSIGNED worker in a visible interactive window")
    print("  --assign <agent> --preview   show that window without opening it")
    print("  --preview-launch <agent> show the full-automation window that WOULD open (launches nothing)")
    print("  --dispatch <agent>       full-automation dispatch (gated: stage>=2 + authorize flag)")
    print("  --sprint-models          print the Q2 LLM/model options + complexity suggestions")
    print("  --sprint-show <thread>   show the current sprint + per-task progress")
    print("  --pilot-fake <agent>     run the full Stage-2 loop with a FAKE worker (no real model)")
    print("  --watchdog [--recover]   report live-claim health; safely reclaim orphans")
    return 0


if __name__ == "__main__":
    sys.exit(main())

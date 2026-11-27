"""Shared helper for the per-Mode action scripts in automation/modes/<mode>/.

The Mode scripts are thin, explicit front doors. The engine (automode.py, owner_wake.py, supervisor.py,
initiate_automation.py, the watchers, ...) stays in automation/ because every Mode shares it and running
processes, hooks, tests and recorded evidence point at those paths. A Mode script only maps its own
actions onto engine commands and refuses actions that belong to a different Mode.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent          # coordination-threads/automation
THREADS = ENGINE / "coordination-threads"                                   # coordination-threads
sys.path.insert(0, str(ENGINE))

DRY_RUN = os.environ.get('MODE_DRY_RUN') == '1'


def run(script: str, *args: str) -> int:
    """Run an engine script from coordination-threads/, exactly as the docs show it."""
    cmd = [sys.executable, str(ENGINE / script), *args]
    shown = 'python3 automation/' + script + (' ' + ' '.join(args) if args else '')
    print(f'→ {shown}', flush=True)
    if DRY_RUN:
        return 0
    return subprocess.call(cmd, cwd=str(THREADS))


def running(name: str) -> int | None:
    import initiate_automation as runtime
    return runtime._running_pid(name)


def mode_word() -> str:
    import daemon
    try:
        return daemon.runtime_mode()['mode']
    except Exception as error:  # status must never crash a Mode script
        return f'unknown ({error})'


def refuse_if_ultimate(action: str) -> None:
    if running('owner_wake') and not DRY_RUN:
        raise SystemExit(f'Refused: Ultimate Auto Mode is running. Run '
                         f'`python3 automation/modes/ultimate-auto/ultimate_auto.py close` before {action}.')


def refuse_if_watchers(action: str) -> None:
    if (running('architect_bridge') or running('coordinator_trigger')) and not DRY_RUN:
        raise SystemExit(f'Refused: round watchers are running (another Mode is active). Close it before {action}.')


def banner(mode: str) -> None:
    print(f'Mode script: {mode} | live runtime Mode word: {mode_word()}')

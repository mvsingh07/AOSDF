#!/usr/bin/env python3
"""daemon.py — shared status/heartbeat/pid helpers for the automation runtime.

The automation "factory" is a set of long-lived, cheap Python TRIGGER daemons (the always-on
nervous system) that detect owed work and launch short-lived, billed AGENT sessions (architect,
coordinators, workers) in visible windows that do a bounded unit of work and exit. See
`initiate_automation.py` for the supervisor that starts/stops the daemon set and renders status.

Every daemon:
  * writes a heartbeat/status JSON to var/daemons/<name>.json every tick (atomic),
  * records its pid there so the supervisor can tell running from dead,
  * reports the current MODE it is operating in (so the dashboard shows it).

This module is stdlib-only, writes only under var/daemons/, reads only gate configs, launches
nothing and grants nothing. It is a status seam, not an authorization path.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import signal

HERE = os.path.dirname(os.path.abspath(__file__))
VAR_DIR = os.path.join(HERE, "var")
DAEMON_DIR = os.path.join(VAR_DIR, "daemons")
CONFIG_DIR = os.path.join(HERE, "config")


def utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
#  MODE — the one word the founder watches, computed from ACTUAL runtime.
#
#  Four operating modes, synchronized with coordinator-definition.md's Mode table:
#    MANUAL    — the automation runtime is down; the founder drives the architect,
#                coordinators and workers by hand.
#    EASY      — daemons are up but only DETECT + relay/preview (they open no agent
#                window); the founder relays `Discuss Thread<n>` to the architect and
#                restarts coordinators. This is the SAFE daemon set.
#    SEMI-AUTO — one launch path is actually live (coordinators auto-launch, OR the
#                architect auto-writes) but not the whole loop / no approved wave; each
#                sprint or round still returns to the founder.
#    AUTO      — BOTH launch paths are live AND an approved wave is advancing: software
#                invokes the architect and the coordinators across the wave; the founder
#                only handles genuine decisions, blockers and protected (hard-gate) actions.
#
#  Honesty rule (the bug this replaces): the mode is derived from what the daemons are
#  ACTUALLY doing — each daemon stamps a `live` flag in its heartbeat — plus whether a
#  wave is active. It is NOT read off a config gate alone. An armed config whose daemon is
#  still running in notify/preview is EASY, never AUTO. The gate columns are reported
#  separately so an armed-but-not-live gate is visible without masquerading as the mode.
# --------------------------------------------------------------------------- #
def _json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def architect_gate_open() -> bool:
    """Config leg for the architect auto write-back (the --auto flag is the second leg)."""
    return _json(os.path.join(CONFIG_DIR, "architect_bridge.json")).get("auto_writeback") == "authorized"


def coordinator_gate_open() -> bool:
    """Config leg for coordinator auto-launch (the --i-have-authorized… flag is the second leg)."""
    return _json(os.path.join(CONFIG_DIR, "coordinator_launch.json")).get("auto_launch") == "authorized"


def worker_gate_open() -> bool:
    """Config leg for supervisor worker dispatch / assign-launch."""
    topo = _json(os.path.join(CONFIG_DIR, "adr-025.topology.json"))
    # Either standing worker-launch authorization counts as "dispatch is armed".
    return topo.get("dispatch") == "authorized" or topo.get("assign_launch") == "authorized"


def _fresh_status(name: str, max_age: float = 300.0) -> dict | None:
    """A daemon's heartbeat iff it is running and the beat is fresh (< max_age), else None."""
    st = read_status(name)
    if not st:
        return None
    age = age_seconds(st.get("ts"))
    if age is None or age >= max_age:
        return None
    return st


def architect_live() -> bool:
    """True iff the architect write-back is ACTUALLY launching live (daemon up + --auto + gate)."""
    st = _fresh_status("architect_bridge")
    return bool(st and st.get("live"))


def coordinator_live() -> bool:
    """True iff coordinators are ACTUALLY being auto-launched (daemon up + flag + gate)."""
    st = _fresh_status("coordinator_trigger")
    return bool(st and st.get("live"))


def _active_wave() -> dict | None:
    try:
        import wave as _wave  # lazy: wave.py is a sibling, no circular import at load
        return _wave.active_wave()
    except Exception:
        return None


def runtime_mode() -> dict:
    """The live operating mode computed from actual daemon heartbeats + wave, not config alone."""
    arch = architect_live()
    coord = coordinator_live()
    wave = _active_wave()
    up = bool(_fresh_status("architect_bridge") or _fresh_status("coordinator_trigger")
              or _fresh_status("manual_detector"))
    relay = _fresh_status("owner_wake")
    relay_live = bool(relay and (relay.get("live") or relay.get("mode") == "live") and wave)
    if arch and coord and wave:
        mode = "AUTO"
    elif relay_live and not (arch or coord):
        # Founder-named 24Nov2026: existing bound sessions + SA-verified delivery-only wave + wake relay.
        mode = "ULTIMATE-AUTO"
    elif arch or coord:
        mode = "SEMI-AUTO"
    elif up:
        mode = "EASY"
    else:
        mode = "MANUAL"
    detail = "; ".join([
        f"architect write-back {'LIVE' if arch else 'relay/preview'}",
        f"coordinator launch {'LIVE' if coord else 'relay/preview'}",
        ("wave active" if wave else "no wave"),
    ] + (["wake relay LIVE (existing sessions)"] if relay_live else []))
    return {
        "mode": mode,
        "detail": detail,
        "architect_live": arch,
        "coordinator_live": coord,
        "wave_active": bool(wave),
        "daemons_up": up,
        "architect_gate": "armed" if architect_gate_open() else "off",
        "coordinator_gate": "armed" if coordinator_gate_open() else "off",
        "worker_gate": "armed" if worker_gate_open() else "off",
    }


def current_mode() -> str:
    """Back-compat one-word mode. Now the honest LIVE mode (was config-only, which misreported)."""
    return runtime_mode()["mode"]


def mode_detail() -> dict:
    return runtime_mode()


# --------------------------------------------------------------------------- #
#  Heartbeat / status files (one per daemon, under var/daemons/).
# --------------------------------------------------------------------------- #
def status_path(name: str) -> str:
    return os.path.join(DAEMON_DIR, f"{name}.json")


def write_status(name: str, **fields) -> None:
    """Atomically write this daemon's status. Always stamps pid + ts; caller adds the rest
    (mode, state, summary, counters). Never raises on a transient FS hiccup."""
    os.makedirs(DAEMON_DIR, exist_ok=True)
    rec = {"name": name, "pid": os.getpid(), "ts": utc()}
    rec.update(fields)
    path = status_path(name)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        os.replace(tmp, path)
    except OSError:
        pass


def read_status(name: str) -> dict:
    return _json(status_path(name))


def read_all_status() -> list[dict]:
    if not os.path.isdir(DAEMON_DIR):
        return []
    out = []
    for fn in sorted(os.listdir(DAEMON_DIR)):
        if fn.endswith(".json") and not fn.endswith(".tmp"):
            rec = _json(os.path.join(DAEMON_DIR, fn))
            if rec:
                out.append(rec)
    return out


def clear_status(name: str) -> None:
    for suffix in ("", ".tmp"):
        try:
            os.remove(status_path(name) + suffix)
        except OSError:
            pass


# --------------------------------------------------------------------------- #
#  pid liveness
# --------------------------------------------------------------------------- #
def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except (OSError, ValueError, TypeError):
        return False
    return True


def stop_pid(pid: int | None, *, sig=signal.SIGTERM) -> bool:
    if not pid_alive(pid):
        return False
    try:
        os.kill(int(pid), sig)
        return True
    except OSError:
        return False


def age_seconds(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        then = _dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc)
    except (ValueError, TypeError):
        return None
    return (_dt.datetime.now(_dt.timezone.utc) - then).total_seconds()

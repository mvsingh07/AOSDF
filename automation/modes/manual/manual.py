#!/usr/bin/env python3
"""Manual Mode actions. The founder drives the SA, the coordinators and the workers personally.

  check                      confirm no automation is running (nothing will wake or launch anyone)
  quiet                      stop all automation processes (Ultimate Auto relay and watchers, Easy detectors)
  assign AGENT [--preview]   open a worker whose task.md the coordinator prepared for you
  dashboard | monitor        worker views (live / one report)
  watchdog [--recover]       claim health / safe orphan recovery
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _engine as e  # noqa: E402

PROCESSES = ('owner_wake', 'architect_bridge', 'coordinator_trigger', 'manual_detector')


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    act, rest = argv[0], argv[1:]
    if act == 'check':
        e.banner('Manual')
        up = [n for n in PROCESSES if e.running(n)]
        print('Automation processes running: ' + (', '.join(up) if up else 'none — Manual Mode is clean'))
        return 1 if up else 0
    if act == 'quiet':
        if e.running('owner_wake') or e.DRY_RUN:
            e.run('automode.py', 'close')  # switch the relay off cleanly, wave left as it is
        return e.run('initiate_automation.py', '--stop')
    if act == 'assign' and rest:
        return e.run('supervisor.py', '--assign', rest[0], *rest[1:2])
    if act == 'dashboard':
        return e.run('monitor_dashboard.py', *rest)
    if act == 'monitor':
        return e.run('monitor.py', *rest)
    if act == 'watchdog':
        return e.run('supervisor.py', '--watchdog', *rest[:1])
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())

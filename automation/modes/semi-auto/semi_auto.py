#!/usr/bin/env python3
"""Semi-auto Mode actions. The founder acts as SA and opens each coordinator; coordinators dispatch workers.

  status                         live Mode word + sprint of every thread
  models                         worker model menu for the sprint-entry question
  sprint N [show|new|mark ...]   record/show thread N's sprint (automation/sprint.py)
  assign AGENT [--preview]       open the worker whose task.md is written (visible window)
  dashboard                      live worker dashboard
  watchdog [--recover]           claim health / safe orphan recovery
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _engine as e  # noqa: E402


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    act, rest = argv[0], argv[1:]
    if act == 'status':
        e.banner('Semi-auto')
        return max(e.run('supervisor.py', '--sprint-show', str(n)) for n in (1, 2, 3))
    if act == 'models':
        return e.run('supervisor.py', '--sprint-models')
    if act == 'sprint' and rest:
        return e.run('sprint.py', '--thread-folder', f'thread{rest[0]}', *(rest[1:] or ['show']))
    if act == 'assign' and rest:
        return e.run('supervisor.py', '--assign', rest[0], *rest[1:2])
    if act == 'dashboard':
        return e.run('monitor_dashboard.py', *rest)
    if act == 'watchdog':
        return e.run('supervisor.py', '--watchdog', *rest[:1])
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())

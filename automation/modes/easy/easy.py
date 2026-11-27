#!/usr/bin/env python3
"""Easy Mode actions. Coordinators run their sprints; the founder relays `Discuss Thread<N>` to the SA.

  start     start the two queue-only round watchers (no agent launch, no wake relay)
  owed      print `Discuss Thread<N>` for every round now waiting on the SA (one shot)
  status    runtime status (Mode word, watchers, wave)
  watch     repainting runtime dashboard
  stop      stop the watchers
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _engine as e  # noqa: E402


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    act = argv[0] if argv else ''
    if act == 'start':
        e.refuse_if_ultimate('starting Easy Mode')
        return e.run('initiate_automation.py', '--start-delivery')
    if act == 'owed':
        return e.run('architect_bridge.py', '--notify')
    if act == 'status':
        return e.run('initiate_automation.py', '--status')
    if act == 'watch':
        return e.run('initiate_automation.py', '--watch')
    if act == 'stop':
        e.refuse_if_ultimate('stopping watchers that Ultimate Auto Mode owns (use ultimate_auto.py close)')
        return e.run('initiate_automation.py', '--stop')
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())

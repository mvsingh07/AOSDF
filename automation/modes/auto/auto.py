#!/usr/bin/env python3
"""Auto Mode actions (implemented, NOT in use). Software launches fresh SA/coordinator sessions per round.

  status                     runtime status, gates and Mode word
  preview THREAD             show the coordinator launch that WOULD happen (opens nothing)
  start-armed --i-have-founder-authorization
                             start the daemons with live launch flags (each still gated by its config file)
  stop                       stop all daemons

Do not use alongside Ultimate Auto Mode: it would start new sessions next to the existing bound ones.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _engine as e  # noqa: E402


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    act, rest = (argv[0], argv[1:]) if argv else ('', [])
    if act == 'status':
        return e.run('initiate_automation.py', '--status')
    if act == 'preview' and rest:
        return e.run('coordinator_trigger.py', '--preview', rest[0])
    if act == 'start-armed':
        if '--i-have-founder-authorization' not in rest:
            raise SystemExit('Refused: Auto Mode launches new agent sessions. Pass --i-have-founder-authorization '
                             'only with a recorded founder decision; the config gates still apply.')
        e.refuse_if_ultimate('arming Auto Mode')
        return e.run('initiate_automation.py', '--start', '--arm')
    if act == 'stop':
        return e.run('initiate_automation.py', '--stop')
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Ultimate Auto Mode actions (current Mode). Front door to automation/automode.py.

  start | pause | continue | close [--complete-wave] | restart | status | watch | wake [--owner R]
  tell --to all|architect|coordinator1.. --message "..." | header --thread N --round R --checkpoint C
  decisions [--all] | answer ID --message "..." | dismiss ID | learning [--all] | done ID [--note ...]
  (agents) ask --from ROLE --question ... | learn --from ROLE --kind K --title ... --why ...
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _engine as e  # noqa: E402

ACTIONS = {'start', 'pause', 'continue', 'resume', 'close', 'stop', 'restart', 'status', 'watch', 'wake', 'tell', 'header', 'rotate',
           'decisions', 'answer', 'dismiss', 'ask', 'learn', 'learning', 'done'}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ACTIONS:
        print(__doc__)
        return 2
    if argv[0] in ('start', 'continue', 'resume', 'restart') and not e.DRY_RUN:
        legacy = [n for n in ('manual_detector',) if e.running(n)]
        if legacy:
            raise SystemExit(f'Refused: {legacy} from another Mode is running; stop it first '
                             '(python3 automation/modes/easy/easy.py stop).')
    return e.run('automode.py', *argv)


if __name__ == '__main__':
    sys.exit(main())

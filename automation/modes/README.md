# Operating Modes

Each folder provides a definition, setup guidance and a thin action script over the shared engine. Run commands from the framework/project root. Choose the process Mode explicitly; startup scripts do not choose it for you.

| Mode | Definition and setup | Action script | Who coordinates |
| --- | --- | --- | --- |
| Manual | [manual/](manual/README.md) | `manual/manual.py` | Founder acts as architect and relays work. |
| Semi-auto | [semi-auto/](semi-auto/README.md) | `semi-auto/semi_auto.py` | Founder remains architect; dispatch is assisted. |
| Easy | [easy/](easy/README.md) | `easy/easy.py` | Founder relays alignment via Discuss Thread. |
| Auto | [auto/](auto/README.md) | `auto/auto.py` | Architect coordinates an explicitly authorized bounded wave. |
| Ultimate Auto (optional) | [ultimate-auto/](ultimate-auto/README.md) | `ultimate-auto/ultimate_auto.py` | Wake relay delivers input to existing bound architect/coordinator sessions. |

The first four are framework process Modes. A project explicitly adopts the fifth extension before using it. No script modifies its review policy or transfers authority. Scripts refuse conflicting running Modes; previews use `MODE_DRY_RUN=1`. Existing owners, claims and deadlines remain authoritative.

```sh
MODE_DRY_RUN=1 python3 automation/modes/ultimate-auto/ultimate_auto.py status
```

All Modes share `automation/` engine scripts, config schemas, ownership checks and tests. Do not duplicate the engine per Mode. Close a previous Mode only under the installation's authority, reconcile in-flight work, then start the selected Mode with its own reviewed configuration. Copying a folder does not start a process.

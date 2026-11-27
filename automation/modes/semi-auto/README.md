# Semi Auto

Founder remains architect; coordinators use assisted assignment and dispatch.

1. Read [the automation guide](../../README.md) and [Mode index](../README.md).
2. Select this Mode as an explicit project decision. Record topology, ownership, scope, environment, model policy, budgets and stop conditions.
3. Install project-specific configuration from reviewed examples; keep source examples inactive. Reconcile existing processes and owner sessions before any start or stop.
4. Inspect available commands with `python3 automation/modes/semi-auto/semi_auto.py --help`, or preview with:

```sh
MODE_DRY_RUN=1 python3 automation/modes/semi-auto/semi_auto.py status
```

For Ultimate Auto, bind existing sessions and verify a delivery-only wave with an original deadline first. Configure adapters only after checking installed CLI support. Keep `claude_bg_resume` false unless separately adopted. Wake budgets are at most 96 per owner; idle windows are 300–7200 seconds; no automatic wave/deadline renewal. First wakes and protected operations require the adopting project's authority.

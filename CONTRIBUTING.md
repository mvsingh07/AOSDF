# Contributing

Start with README.md, manual.md and reference/current-workflow-rules.md. Keep reusable code and examples independent of private workspaces. Never include active assignments, credentials, customer data or authorization grants.

For a change, describe the user-visible behavior and run the relevant checks:

```sh
(cd aosdf-mcp && npm test)
(cd aosdf-vscode && npm test)
(cd templates/coordination_threads/automation && python3 -m unittest discover -s tests -v)
(cd templates/coordination_threads/file-signals && python3 -m unittest discover -s tests -v)
python3 -m pip install -r tools/requirements-metadata.txt
python3 -m unittest discover -s tools/tests -v
(cd website && npm ci && npm run build)
```

Document changes to role authority, owned paths, review gates and recovery. Keep new-project templates inactive. Existing installations migrate independently following upgrades/README.md; updating the framework does not migrate an adopting product. Do not change VERSION to publish a packaging-only working-tree change. Released payloads and accepted project evidence remain immutable; follow-up corrections need a new release decision.

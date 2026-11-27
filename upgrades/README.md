# Portable framework upgrades

Current reusable framework baseline: **3.8.0**. Use the [existing-project migration](releases/3.8.0/migrate.md), [distribution scope](releases/3.8.0/README.md), [adaptation manifest](releases/3.8.0/source-adaptations.json) and [public registry](registry.json).

The current inventory hashes public source in this checkout. Earlier release inventories remain historical snapshots; they are not rewritten when files move. The top-level checker follows the current registry:

```sh
python3 upgrades/check_inventory.py
```

The update5 source adoption was explicitly requested for the canonical root. It merges generic single-review/outcome-first rules and inactive founder inbox/learning/rotation capabilities. It changes no other installation, source account/profile choice or runtime state.

Include recipes, the inventory and every listed source file in a distribution. Private application receipts remain with their owning project. Local acceptance is distinct from a Git commit, package publication, deployment or live-session validation.

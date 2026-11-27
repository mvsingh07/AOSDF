# Portable root and existing-project upgrades

Use [the public upgrade package](../upgrades/README.md) and [3.8.0 existing-project migration](../upgrades/releases/3.8.0/migrate.md). They require no private originating workspace. The source inventory describes this distribution snapshot; it does not reconstruct historical frozen payloads or private application receipts.

Root improvements change the reusable framework and new-project templates. Existing projects migrate independently, preserving product rules, active claims, accepted artifacts, task IDs, environments and local context. Updating the framework never marks a project migrated.

Resolve the actual target; inspect instructions, baseline and Git state before changing it. Validate behavior with isolated tests before changing project version labels and its own receipt. Record partial work at the old version. Reapplication checks incorporation without redispatch or downgrade. Framework SemVer, product/package versions and document revisions are separate.

Never transfer live state, model profiles, credentials or permissions from another project. Proposed updates and held work are not releases. Version 3.8.0 is the locally validated canonical baseline after the explicit update5 source-adoption request. The separate sprint-loop architecture remains excluded; runtime activation and project migrations remain independent.

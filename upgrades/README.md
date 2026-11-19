# Portable framework upgrades

This directory is the public upgrade entry point. It replaces dependence on the originating product's private update registry for ordinary framework adoption. The current distributed baseline is **3.6.0**.

- [Existing-project migration](releases/3.6.0/migrate.md)
- [Distribution scope](releases/3.6.0/README.md)
- [Public registry](registry.json)
- [Source inventory checker](check_inventory.py)

The inventory hashes reusable source files in this checkout; source files are the payload. It is a packaging snapshot of the current 3.6.0 working source, not a reconstruction of the original immutable update1–3 archives and not evidence that an existing product migrated. Packaging changes are unreleased until maintainers review and publish them. Held or proposed 3.7.0 work is excluded.

When distributing an archive, include these recipes, the inventory and every listed source file. Run `python3 upgrades/check_inventory.py` before handoff. Existing projects retain their own application receipts privately. The public registry never enumerates private customer/product installations.

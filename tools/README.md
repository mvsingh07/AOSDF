# Document metadata tooling

`document_metadata.py` reads and validates adopted `aosdf-doc/v1` headers. Python 3.10+ and the pinned PyYAML dependency in `requirements-metadata.txt` are required. It does not start agents, index jobs, model calls or source synchronization.

```sh
python3 -m pip install -r tools/requirements-metadata.txt
python3 -m unittest discover -s tools/tests -v
python3 tools/document_metadata.py --root /absolute/project/docs/documents --inventory /absolute/migration/manifest.json
```

Run from the framework root, using a project-owned or temporary virtual environment. With `--inventory`, the checker verifies every recorded original path, source SHA-256, migrated body hash, retained old metadata values and adopted document-ID uniqueness. Protected originals are verified whole-file rather than falsely reported as schema-adopted. Without an inventory it checks every `.md` below the chosen root and reports missing/invalid metadata; that command does not silently exempt legacy files.

`prepare(original_bytes, relative_path, project_id, metadata_date)` is an importable pure function for a reviewed migration driver. It returns proposed bytes and parsed metadata; it does not write. It preserves existing values, original header lines/comments and exact body bytes; missing dates remain null; new values have recorded provenance; another pass is byte-identical. The command line deliberately has no blanket `--fix`: corpus inventory, protected/digest exceptions and before/after evidence must be established before any driver writes.

Malformed YAML, duplicate keys, merge keys, flow-style root mappings and any unsupported layout that cannot retain exact values are refused. A frontmatter block that is already complete is validated and retained byte-for-byte. Schema: `reference/schemas/document-metadata.schema.json`; field semantics and consent rules: `reference/document_authoring.md`.

The Comms pilot's manifest also stores the exact original header prefix in base64 for rollback: verify current `after_sha256`, combine decoded `original_prefix_base64` with the current unchanged body, and verify `before_sha256` before restoring. Never roll back over a later edit. Deferred files' proposed metadata is tied to their original SHA-256 and is not a claim their inline header was migrated.

## Enforcing future document creation

`create_document.py` writes a new document exclusively, refuses existing paths and symlinks, requires actual title/type/summary, records current UTC creation dates and preserves the supplied body. Give it body-only Markdown, without a copied header:

```sh
python tools/create_document.py --root docs/documents --path 03_System_Design/new_contract.md --project-id my-project --title "New contract" --type design --summary "Owns the new contract and its acceptance criteria." --body-file /tmp/new_contract_body.md
python tools/check_document_metadata.py --root docs/documents --legacy-baseline .aosdf/document-metadata-legacy.json
```

The read-only gate walks every Markdown document (including new archive/run/generated files), rejects missing/invalid headers, duplicate/placeholder IDs and symlinks. Only explicitly recorded pre-existing legacy paths are grandfathered. Never expand that list to silence an error. Install `document_metadata_hook.py` with the tools and add `hooks: [tools/document_metadata_hook.py]` in the docs repository's `mkdocs.yml`; it calls the same gate before rendering. Install an empty baseline for new projects. Existing projects need a reviewed legacy inventory; adopted documents cannot be stripped of their metadata. Requirements remain pinned in `requirements-metadata.txt`. No watcher, auto-fixer or LLM is involved.

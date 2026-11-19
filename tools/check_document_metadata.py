#!/usr/bin/env python3
"""Read-only new/adopted-document gate. Fixed legacy paths are not folder exemptions."""
import argparse
import json
from pathlib import Path
import document_metadata as metadata


def check(root, baseline):
    root = Path(root).resolve()
    policy = json.loads(Path(baseline).read_text())
    if policy.get('schema') != 'aosdf-document-legacy/v1':
        raise ValueError('unsupported legacy baseline schema')
    legacy = set(policy['legacy_paths'])
    for name in legacy:
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or path.suffix.lower() != '.md':
            raise ValueError('unsafe legacy path: ' + name)
    if not root.is_dir():
        raise ValueError('document root missing')
    errors, ids = [], {}
    checked = grandfathered = 0
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            if path.suffix.lower() == '.md':
                errors.append(f'{path.relative_to(root)}: symlinks are not document sources')
            continue  # Native assets/dependency links are not Markdown sources.
        if not path.is_file() or path.suffix.lower() != '.md':
            continue
        name = str(path.relative_to(root))
        try:
            raw, _ = metadata.split_document(path.read_bytes())
            header = metadata.parse_header(raw)
            if name in legacy and 'document_schema' not in header:
                grandfathered += 1
                continue
            problems = metadata.validate(header)
            identity = header.get('id')
            if isinstance(identity, str):
                if identity.startswith('<') or '{{' in identity:
                    problems.append('placeholder document id; assign a fresh stable identity')
                if identity in ids:
                    problems.append('duplicate id also in ' + ids[identity])
                ids[identity] = name
            errors.extend(f'{name}: {problem}' for problem in problems)
            checked += 1
        except (metadata.MetadataError, UnicodeError) as error:
            if name in legacy:
                grandfathered += 1
            else:
                errors.append(f'{name}: {error}')
    return {'validated_documents': checked, 'legacy_documents': grandfathered, 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--legacy-baseline', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.root, args.legacy_baseline)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(result, indent=2))
    return bool(result['errors'])


if __name__ == '__main__':
    raise SystemExit(main())

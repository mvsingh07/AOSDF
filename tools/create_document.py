#!/usr/bin/env python3
"""Create a new document with metadata; never overwrite or modify an existing document."""
import argparse
import datetime as dt
from pathlib import Path
import yaml
import document_metadata as metadata


def create(root, relative, project_id, title, kind, summary, body):
    root = Path(root).resolve()
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts or relative.suffix.lower() != '.md':
        raise ValueError('path must be a relative Markdown path inside document root')
    if not root.is_dir():
        raise ValueError('document root must already exist')
    target = root / relative
    for part in [target, *target.parents]:
        if part == root:
            break
        if part.is_symlink():
            raise ValueError('symlink document path refused')
    if target.exists():
        raise FileExistsError('document already exists: ' + str(relative))
    for label, value in [('project', project_id), ('title', title), ('type', kind), ('summary', summary)]:
        if not value.strip() or '{{' in value or value.strip().startswith('<'):
            raise ValueError(label + ' must be filled in')
    body.decode('utf-8')
    # A template body may start with a prose horizontal rule; a real header must
    # be supplied separately, never nested/copied with its original identity.
    try:
        oldraw, _ = metadata.split_document(body)
        if oldraw is not None and metadata.parse_header(oldraw):
            raise ValueError('body contains frontmatter; provide body-only Markdown')
    except metadata.MetadataError:
        pass  # Preserve explicitly provided prose, including non-YAML rules.
    now = dt.datetime.now(dt.timezone.utc).date().isoformat()
    prepared, header = metadata.prepare(b'\n' + body, str(relative), project_id, now)
    header.update(title=title, type=kind, summary=summary, created=now, updated=now)
    header['metadata_provenance'].update(title='author_supplied', type='author_supplied', summary='author_supplied', created='new_document_creation_utc', updated='new_document_creation_utc')
    problems = metadata.validate(header)
    if problems:
        raise ValueError('; '.join(problems))
    for existing in root.rglob('*'):
        if existing.is_file() and existing.suffix.lower() == '.md' and not existing.is_symlink():
            try:
                value = metadata.parse_header(metadata.split_document(existing.read_bytes())[0])
            except (metadata.MetadataError, UnicodeError):
                continue
            if value.get('id') == header['id']:
                raise ValueError('document identity already exists at ' + str(existing.relative_to(root)))
    result = b'---\n' + yaml.safe_dump(header, sort_keys=False, allow_unicode=True).encode() + b'---\n' + body
    assert metadata.split_document(result)[1] == body
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(result)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--path', required=True)
    parser.add_argument('--project-id', required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--type', required=True)
    parser.add_argument('--summary', required=True)
    parser.add_argument('--body-file', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(create(args.root, args.path, args.project_id, args.title, args.type, args.summary, args.body_file.read_bytes()))
    except (ValueError, OSError, metadata.MetadataError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()

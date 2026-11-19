#!/usr/bin/env python3
"""Read/validate document metadata; migrate a manifest-selected batch without changing bodies.

Dependency: PyYAML (see requirements-metadata.txt). Importing never writes files.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import uuid
import yaml

SCHEMA = 'aosdf-doc/v1'
ORDER = ('title', 'type', 'tags', 'created', 'updated', 'sources', 'document_schema',
         'id', 'summary', 'entities', 'metadata_updated', 'metadata_provenance')
REQUIRED = ORDER[:10]

class MetadataError(ValueError):
    pass

class UniqueLoader(yaml.SafeLoader):
    pass

def unique_mapping(loader, node, deep=False):
    if any(key.value == '<<' for key, _ in node.value):
        raise MetadataError('YAML merge keys need manual metadata migration')
    result = {}
    for key, value in node.value:
        name = loader.construct_object(key, deep=deep)
        if not isinstance(name, str):
            raise MetadataError('metadata keys must be strings')
        if name in result:
            raise MetadataError(f'duplicate metadata key: {name}')
        result[name] = loader.construct_object(value, deep=deep)
    return result

UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def split_document(data: bytes):
    """Return raw header or None, and the exact original bytes after the delimiter."""
    if data.startswith(b'\xef\xbb\xbf'):
        raise MetadataError('UTF-8 BOM needs explicit review')
    data.decode('utf-8')
    if not re.match(br'\A---\r?\n', data):
        return None, data
    match = re.match(br'\A---\r?\n(.*?)^---[ \t]*(?:\r?\n|\Z)', data, re.M | re.S)
    if not match:
        raise MetadataError('unclosed frontmatter')
    return match[1], data[match.end():]

def parse_header(raw):
    if raw is None:
        return {}
    try:
        data = yaml.load(raw.decode('utf-8'), Loader=UniqueLoader)
    except yaml.YAMLError as error:
        raise MetadataError('invalid YAML frontmatter') from error
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise MetadataError('frontmatter must be a mapping')
    return data

def prose(body):
    fence = None
    lines = []
    for line in body.decode('utf-8').splitlines():
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return lines

def title_and_excerpt(body, relative):
    lines = prose(body)
    title = next((re.sub(r'\s+#+\s*$', '', line[2:].strip())
                  for line in lines if line.startswith('# ')), None)
    title_origin = 'first_h1'
    if not title:
        title = Path(relative).stem.replace('_', ' ').replace('-', ' ')
        title_origin = 'filename'
    paragraphs, current = [], []
    for line in lines + ['']:
        stripped = line.strip()
        if not stripped or re.match(r'^(#|\||>|<!--|---|\*\*\*|\d+\.|[-*+]\s)', stripped):
            if current:
                paragraphs.append(' '.join(current)); current = []
        else:
            current.append(stripped)
    excerpt = paragraphs[0] if paragraphs else title
    excerpt = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', excerpt)
    excerpt = re.sub(r'[*`]', '', excerpt)
    excerpt = re.sub(r'\s+', ' ', excerpt).strip()
    if len(excerpt) > 360:
        excerpt = excerpt[:357].rsplit(' ', 1)[0] + '...'
    return title, excerpt, title_origin, 'body_excerpt' if paragraphs else 'title_only'

def classify(relative):
    parts = Path(relative).parts
    name = Path(relative).name.lower()
    if 'prompt' in name or 'prompt_templates' in parts:
        return 'prompt'
    if name.startswith('adr-') or 'decisions' in parts or name in ('decisions.md', 'decisions_log.md'):
        return 'decision'
    section = parts[0] if len(parts) > 1 else ''
    for prefix, kind in [('00_', 'context'), ('01_', 'requirements'), ('02_', 'policy'),
                         ('03_', 'design'), ('04_', 'design'), ('05_', 'policy'),
                         ('06_', 'plan'), ('07_', 'milestone'), ('08_', 'decision'),
                         ('09_', 'plan'), ('10_', 'runbook'), ('11_', 'requirements'),
                         ('12_', 'runbook'), ('13_', 'policy'), ('14_', 'reference'),
                         ('15_', 'plan'), ('17_', 'plan')]:
        if section.startswith(prefix):
            return kind
    return {'templates': 'template', 'reviews': 'analysis',
            'email-architecture-review': 'analysis', 'status-reports': 'evidence'}.get(section, 'reference')

def ordered_raw_header(raw, additions):
    """Reorder top-level blocks, retaining original values, comments and extension fields.

    YAML anchors that would become forward references are refused by the subsequent parse.
    """
    text = raw.decode('utf-8') if raw is not None else ''
    lines = text.splitlines(keepends=True)
    existing = parse_header(raw)
    nodes = yaml.compose(text, Loader=UniqueLoader) if text.strip() else None
    blocks = {}
    prefix = ''
    if nodes is not None:
        positions = [(key.value, key.start_mark.line) for key, _ in nodes.value]
        if positions and any(key.start_mark.column != 0 for key, _ in nodes.value):
            raise MetadataError('flow-style root mapping needs manual migration')
        if positions:
            prefix = ''.join(lines[:positions[0][1]])
        for index, (name, start) in enumerate(positions):
            end = positions[index + 1][1] if index + 1 < len(positions) else len(lines)
            blocks[name] = ''.join(lines[start:end])
    for key, value in additions.items():
        blocks[key] = yaml.safe_dump({key: value}, allow_unicode=True, sort_keys=False, width=1000)
    keys = [key for key in ORDER if key in blocks] + [key for key in blocks if key not in ORDER]
    rendered = prefix + ''.join(blocks[key].rstrip('\r\n') + '\n' for key in keys)
    if raw is not None and b'\r\n' in raw:
        rendered = rendered.replace('\r\n', '\n').replace('\n', '\r\n')
    parsed = parse_header(rendered.encode('utf-8'))
    for key, value in existing.items():
        if parsed.get(key) != value:
            raise MetadataError(f'original metadata value changed: {key}')
    return rendered.encode('utf-8')

def validate(metadata):
    errors = []
    for key in REQUIRED:
        if key not in metadata:
            errors.append(f'missing {key}')
    if metadata.get('document_schema') != SCHEMA:
        errors.append('unsupported document_schema')
    for key in ['id', 'title', 'type', 'summary']:
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            errors.append(f'{key} must be a nonempty string')
    for key in ['tags', 'entities', 'sources']:
        if not isinstance(metadata.get(key), list) or any(not isinstance(item, str) for item in metadata.get(key, [])):
            errors.append(f'{key} must be a string list')
    for key in ['created', 'updated', 'metadata_updated']:
        value = metadata.get(key)
        if value is not None:
            try:
                if not isinstance(value, (str, dt.date)):
                    raise ValueError()
                dt.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            except ValueError:
                errors.append(f'{key} must be ISO date/date-time or null')
    return errors

def prepare(data, relative, project_id, metadata_date):
    raw, body = split_document(data)
    existing = parse_header(raw)
    title, summary, title_origin, summary_origin = title_and_excerpt(body, relative)
    defaults = {'title': title, 'type': classify(relative), 'tags': [], 'created': None,
                'updated': None, 'sources': [], 'document_schema': SCHEMA,
                'id': f'{project_id}:doc:{uuid.uuid5(uuid.NAMESPACE_URL, project_id + "/" + relative)}',
                'summary': summary, 'entities': []}
    origins = {'title': title_origin, 'type': 'directory_classification', 'tags': 'none_declared',
               'created': 'unknown', 'updated': 'unknown', 'sources': 'none_declared',
               'id': 'project_and_original_path_uuid5', 'summary': summary_origin,
               'entities': 'none_declared', 'document_schema': 'migration_profile'}
    additions = {key: value for key, value in defaults.items() if key not in existing}
    if additions:
        if 'metadata_updated' not in existing:
            additions['metadata_updated'] = metadata_date
        if 'metadata_provenance' not in existing:
            additions['metadata_provenance'] = {key: origins[key] for key in additions if key in origins}
    if not additions:
        errors = validate(existing)
        if errors:
            raise MetadataError('; '.join(errors))
        return data, existing
    new_raw = ordered_raw_header(raw, additions)
    metadata = parse_header(new_raw)
    errors = validate(metadata)
    if errors:
        raise MetadataError('; '.join(errors))
    newline = b'\r\n' if b'\r\n' in data else b'\n'
    result = b'---' + newline + new_raw + b'---' + newline + body
    if split_document(result)[1] != body:
        raise MetadataError('body bytes changed')
    return result, metadata

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, help='JSON with exact entries[path, after_sha256, before_body_sha256, disposition]')
    args = parser.parse_args()
    root = args.root.resolve()
    entries = json.loads(args.inventory.read_text())['entries'] if args.inventory else [
        {'path': str(p.relative_to(root)), 'disposition': 'migrated'} for p in sorted(root.rglob('*.md'))]
    errors, ids, checked, protected = [], {}, 0, 0
    for entry in entries:
        relative = entry['path']; path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            errors.append(f'{relative}: path escapes root or is symlink'); continue
        if not path.is_file():
            errors.append(f'{relative}: missing file'); continue
        data = path.read_bytes()
        if 'after_sha256' in entry and sha(data) != entry['after_sha256']:
            errors.append(f'{relative}: inventory source hash changed')
        if entry['disposition'] != 'migrated':
            protected += 1
            continue
        try:
            raw, body = split_document(data); metadata = parse_header(raw)
            errors += [f'{relative}: {error}' for error in validate(metadata)]
            if entry.get('before_body_sha256') and sha(body) != entry['before_body_sha256']:
                errors.append(f'{relative}: body bytes changed')
            for key, value in entry.get('original_metadata', {}).items():
                if json.loads(json.dumps(metadata.get(key), default=str)) != value:
                    errors.append(f'{relative}: original metadata changed: {key}')
            identity = metadata.get('id')
            if identity and identity in ids:
                errors.append(f'{relative}: duplicate id also in {ids[identity]}')
            ids[identity] = relative
            checked += 1
        except (MetadataError, UnicodeError) as error:
            errors.append(f'{relative}: {error}')
    print(json.dumps({'validated_documents': checked, 'protected_unchanged': protected, 'errors': errors}, indent=2))
    return 1 if errors else 0

if __name__ == '__main__':
    raise SystemExit(main())

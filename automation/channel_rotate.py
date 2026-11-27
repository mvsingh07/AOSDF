#!/usr/bin/env python3
"""channel_rotate.py — keep coordinator-architect/threadN.md small (rule C17, founder 26Nov2026).

Every wake makes an owner read its channel; channels can grow large. This moves all
rounds except the newest KEEP, verbatim and oldest first, to coordinator-architect/history/threadN.md.
The first time, that file is created with aosdf-doc/v1 metadata through tools/create_document.py; after
that, rounds are appended. The channel keeps its preamble, one pointer line to the history file, and the
kept rounds, all byte-identical. No round is changed, renumbered or dropped; the split is verified before
the write.

Safety: refuses when the channel was written in the last QUIET seconds (an owner may be mid-edit), and
when the file changed between read and write. The watchers read only the newest round, which is kept.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
from layout import THREADS, DOCUMENTS, DOCUMENT_TOOLS, PROJECT_ID
CHANNEL_DIR = THREADS / 'coordinator-architect'
DOCS_PROJECT = DOCUMENT_TOOLS.parent
DOCS_ROOT = DOCUMENTS
ROUND_RE = re.compile(r'<!--\s*round:(\d+)\s+checkpoint:[A-Za-z0-9_-]+\s+status:[A-Za-z\-]+')
KEEP = 5
MIN_BYTES = 150_000
QUIET = 60


def pointer(thread: int) -> str:
    return (f'> **Older rounds** are archived verbatim in [history/thread{thread}.md](history/thread{thread}.md) '
            '(rule C17, `automation/automode.py rotate`). Read this file\'s tail; search the history only when needed.\n\n')


def split(text: str, keep: int) -> tuple[str, str, str] | None:
    """(preamble, moved, kept), or None if there is nothing to move."""
    starts = [text.rfind('\n', 0, m.start()) + 1 for m in ROUND_RE.finditer(text)]
    if len(starts) <= keep:
        return None
    cut = starts[-keep]
    return text[:starts[0]], text[starts[0]:cut], text[cut:]


def _create_history(thread: int, moved: str) -> None:
    body = (f'# Thread {thread} channel history\n\n'
            f'Rounds moved verbatim, oldest first, from [thread{thread}.md](../thread{thread}.md) by '
            '`automation/channel_rotate.py` (rule C17). Later rotations append below. Nothing here is owed '
            'to anyone; the live round is always in the channel file.\n\n' + moved)
    with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as fh:
        fh.write(body)
        body_file = fh.name
    try:
        python = DOCS_PROJECT / '.venv' / 'bin' / 'python'
        rel = (CHANNEL_DIR / 'history' / f'thread{thread}.md').relative_to(DOCS_ROOT)
        subprocess.run([str(python if python.exists() else sys.executable), str(DOCUMENT_TOOLS / 'create_document.py'),
                        '--root', str(DOCS_ROOT), '--path', str(rel), '--project-id', PROJECT_ID,
                        '--title', f'Thread {thread} channel history', '--type', 'reference',
                        '--summary', f'Verbatim archive of older Thread {thread} coordinator-architect rounds, '
                        'moved out of the live channel to keep wakes small (rule C17).',
                        '--body-file', body_file], cwd=DOCS_PROJECT, check=True, capture_output=True, text=True)
    finally:
        os.unlink(body_file)


def rotate(thread: int, keep: int = KEEP, min_bytes: int = MIN_BYTES, quiet: int = QUIET,
           dry_run: bool = False, now: float | None = None) -> dict:
    import time
    path = CHANNEL_DIR / f'thread{thread}.md'
    st = path.stat()
    out = {'thread': thread, 'bytes': st.st_size}
    if st.st_size < min_bytes:
        return dict(out, state='small')
    if (now or time.time()) - st.st_mtime < quiet:
        return dict(out, state='recently-written')
    text = path.read_text(encoding='utf-8')
    parts = split(text, keep)
    if not parts:
        return dict(out, state='few-rounds')
    preamble, moved, kept = parts
    mark = pointer(thread)
    head = preamble if mark in preamble else preamble + mark
    new = head + kept
    assert preamble + moved + kept == text
    assert len(ROUND_RE.findall(moved)) + len(ROUND_RE.findall(new)) == len(ROUND_RE.findall(text))
    out.update(moved_rounds=len(ROUND_RE.findall(moved)), kept_rounds=len(ROUND_RE.findall(kept)),
               new_bytes=len(new.encode()))
    if dry_run:
        return dict(out, state='would-rotate')
    history = CHANNEL_DIR / 'history' / f'thread{thread}.md'
    if path.stat().st_mtime != st.st_mtime:
        return dict(out, state='changed-during-read')
    if history.exists():
        prev = history.read_text(encoding='utf-8')
        with history.open('a', encoding='utf-8') as fh:
            fh.write(('' if prev.endswith('\n\n') else '\n' if prev.endswith('\n') else '\n\n') + moved)
    else:
        history.parent.mkdir(exist_ok=True)
        _create_history(thread, moved)
    tmp = path.with_suffix('.md.rotate-tmp')
    tmp.write_text(new, encoding='utf-8')
    if path.stat().st_mtime != st.st_mtime:      # a writer slipped in: history has a copy, channel untouched
        tmp.unlink()
        return dict(out, state='changed-during-write', note='history already has the moved rounds; rerun later')
    os.replace(tmp, path)
    return dict(out, state='rotated', history=str(history.relative_to(CHANNEL_DIR)))


def large_channels(min_bytes: int = MIN_BYTES) -> list[tuple[int, int]]:
    found = []
    for n in (1, 2, 3):
        p = CHANNEL_DIR / f'thread{n}.md'
        if p.exists() and p.stat().st_size >= min_bytes:
            found.append((n, p.stat().st_size))
    return found

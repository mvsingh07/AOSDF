import datetime as dt
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'document_metadata.py'
spec = importlib.util.spec_from_file_location('document_metadata', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class DocumentMetadataTests(unittest.TestCase):
    def prepare(self, data, relative='00_Project_Context/web_prompt.md'):
        return m.prepare(data, relative, 'test-project', '2026-11-15')

    def test_plain_document_body_is_byte_identical(self):
        original = b'# Real title\n\nOriginal paragraph.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n'
        result, meta = self.prepare(original)
        self.assertEqual(m.split_document(result)[1], original)
        self.assertEqual(meta['type'], 'prompt')
        self.assertIsNone(meta['created']); self.assertIsNone(meta['updated'])
        self.assertNotIn('status', meta); self.assertNotIn('owner', meta)

    def test_original_values_comments_and_concepts_survive(self):
        original = b'''---
# Keep this reason.
entities: [redis, postgresql] # retain inline note
summary: >
  An existing multiline summary
  whose words must stay.
concepts:
  - name: Original concept
    why: Original reason
status: content-draft-v1.0
created: 2026-08-31
type: pitch-report
---
\n# Body\nDo not alter me.\n'''
        raw, body = m.split_document(original)
        result, metadata = self.prepare(original)
        self.assertEqual(m.split_document(result)[1], body)
        for key, value in m.parse_header(raw).items():
            self.assertEqual(metadata[key], value)
        self.assertIn(b'# Keep this reason.', result)
        self.assertIn(b'# retain inline note', result)
        self.assertEqual(metadata['type'], 'pitch-report')

    def test_unknown_sources_are_not_fabricated_from_navigation_links(self):
        result, metadata = self.prepare(b'# Title\n\nSee [other doc](../other.md) for details.\n')
        self.assertEqual(metadata['sources'], [])
        self.assertEqual(metadata['metadata_provenance']['sources'], 'none_declared')

    def test_second_pass_is_byte_idempotent(self):
        result, _ = self.prepare(b'# Title\n\nExact body.\n')
        again, _ = m.prepare(result, '00_Project_Context/web_prompt.md', 'test-project', '2026-11-16')
        self.assertEqual(result, again)

    def test_id_survives_move(self):
        result, metadata = self.prepare(b'# Title\n\nExact body.\n')
        moved, current = m.prepare(result, 'other/location.md', 'test-project', '2026-11-16')
        self.assertEqual(metadata['id'], current['id'])
        self.assertEqual(result, moved)

    def test_h1_inside_fence_is_not_document_title(self):
        _, metadata = self.prepare(b'````\n# Fake title\n```\n````\n\n# Actual title\n\nReal paragraph.\n')
        self.assertEqual(metadata['title'], 'Actual title')
        self.assertEqual(metadata['summary'], 'Real paragraph.')

    def test_title_fallback_is_explicit(self):
        _, metadata = self.prepare(b'No heading in this file.\n', 'reference/no_heading.md')
        self.assertEqual(metadata['title'], 'no heading')
        self.assertEqual(metadata['metadata_provenance']['title'], 'filename')

    def test_duplicate_keys_are_refused(self):
        with self.assertRaises(m.MetadataError):
            self.prepare(b'---\ntitle: One\ntitle: Two\n---\n# Body\n')

    def test_unclosed_header_is_refused(self):
        with self.assertRaises(m.MetadataError):
            self.prepare(b'---\ntitle: One\n# Body\n')

    def test_unknown_extensions_survive(self):
        original = b'---\nproduct: supagram\nchannel: email\nversion: 1.0\ncustom: {nested: [a, b]}\n---\n# Body\n'
        _, metadata = self.prepare(original)
        self.assertEqual(metadata['custom'], {'nested': ['a', 'b']})
        self.assertEqual(metadata['version'], 1.0)

    def test_crlf_body_is_preserved(self):
        original = b'---\r\nsummary: Original summary\r\n---\r\n\r\n# Title\r\nBody.\r\n'
        result, _ = self.prepare(original)
        self.assertEqual(m.split_document(result)[1], m.split_document(original)[1])

    def test_invalid_date_is_not_silently_repaired(self):
        with self.assertRaises(m.MetadataError):
            self.prepare(b'---\ncreated: yesterday\n---\n# Body\n')

    def test_invalid_list_is_not_replaced(self):
        with self.assertRaises(m.MetadataError):
            self.prepare(b'---\ntags: string-instead-of-list\n---\n# Body\n')

    def test_prose_horizontal_rule_is_not_frontmatter(self):
        body = b'# Title\n\n---\n\nThe rest.\n'
        result, _ = self.prepare(body)
        self.assertEqual(m.split_document(result)[1], body)

    def test_merge_keys_are_refused_without_lossy_flattening(self):
        with self.assertRaises(m.MetadataError):
            self.prepare(b'---\nbase: &base {a: b}\n<<: *base\n---\n# Body\n')

    def test_summary_excerpt_is_bounded_and_flagged(self):
        _, metadata = self.prepare(('# Title\n\n' + 'original words ' * 100 + '\n').encode())
        self.assertLessEqual(len(metadata['summary']), 360)
        self.assertEqual(metadata['metadata_provenance']['summary'], 'body_excerpt')

if __name__ == '__main__':
    unittest.main()

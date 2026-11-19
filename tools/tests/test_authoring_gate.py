import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from check_document_metadata import check
from create_document import create
import document_metadata as metadata


class AuthoringGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'documents'; self.root.mkdir()
        self.baseline = Path(self.temp.name) / 'legacy.json'
        self.baseline.write_text(json.dumps({'schema': 'aosdf-document-legacy/v1', 'legacy_paths': ['legacy.md']}))

    def new(self, path='new.md', body=b'# New\n\nBody.\n'):
        return create(self.root, path, 'test', 'New', 'design', 'Owns an example contract.', body)

    def test_new_document_body_dates_and_schema(self):
        body=b'---\n\n## Historical prose\n\n---\n# Content\n'
        p=self.new(body=body); raw,result=metadata.split_document(p.read_bytes()); h=metadata.parse_header(raw)
        self.assertEqual(result,body);self.assertTrue(h['created']);self.assertFalse(metadata.validate(h))
        self.assertFalse(check(self.root,self.baseline)['errors'])

    def test_new_files_including_archive_or_run_have_no_folder_exemption(self):
        (self.root/'legacy.md').write_text('# Old\n')
        for name in ['new.md','runs/new.md','_archive/new.md']:
            p=self.root/name;p.parent.mkdir(exist_ok=True);p.write_text('# Missing header\n')
        result=check(self.root,self.baseline)
        self.assertEqual(result['legacy_documents'],1)
        self.assertTrue(all(any(e.startswith(name+':') for e in result['errors']) for name in ['new.md','runs/new.md','_archive/new.md']))

    def test_copied_identity_is_rejected(self):
        p=self.new();(self.root/'copy.md').write_bytes(p.read_bytes())
        self.assertTrue(any('duplicate id' in e for e in check(self.root,self.baseline)['errors']))

    def test_invalid_field_duplicate_yaml_and_placeholder_id_are_rejected(self):
        p=self.new();original=p.read_bytes()
        variants=[original.replace(b'tags: []',b'tags: wrong'),original.replace(b'tags: []',b'tags: []\ntags: []'),original.replace(b'id: test:doc:',b'id: <placeholder>#')]
        for variant in variants:
            p.write_bytes(variant);self.assertTrue(check(self.root,self.baseline)['errors'])

    def test_never_overwrites_and_rejects_unsafe_or_placeholder_input(self):
        p=self.new();original=p.read_bytes()
        with self.assertRaises(FileExistsError):self.new()
        self.assertEqual(p.read_bytes(),original)
        for path in ['../escape.md','/tmp/escape.md','new.txt']:
            with self.assertRaises(ValueError):self.new(path)
        with self.assertRaises(ValueError):create(self.root,'other.md','test','<title>','design','Summary',b'# Body\n')
        with self.assertRaises(ValueError):self.new('nested.md',original)

    def test_symlink_and_missing_baseline_fail_closed(self):
        (self.root/'linked.md').symlink_to(self.baseline)
        self.assertTrue(check(self.root,self.baseline)['errors'])
        with self.assertRaises(FileNotFoundError):check(self.root,self.root/'missing.json')

    def test_non_markdown_dependency_symlink_is_not_a_document(self):
        (self.root/'node_modules').symlink_to(self.root.parent, target_is_directory=True)
        self.new()
        self.assertFalse(check(self.root,self.baseline)['errors'])

    def test_mkdocs_hook_refuses_bad_document_before_build(self):
        # Hook uses installed MkDocs when present; otherwise exercise the exact
        # PluginError contract with a minimal temporary module, no build needed.
        import types
        from unittest.mock import patch
        errors=types.ModuleType('mkdocs.exceptions');errors.PluginError=type('PluginError',(Exception,),{})
        spec=importlib.util.spec_from_file_location('metadata_hook',TOOLS/'document_metadata_hook.py');hook=importlib.util.module_from_spec(spec);spec.loader.exec_module(hook)
        docs=self.root.parent/'docs';docs.mkdir();(docs/'documents').mkdir();(docs/'documents'/'bad.md').write_text('# No metadata\n')
        state=docs.parent/'.aosdf';state.mkdir();(state/'document-metadata-legacy.json').write_bytes(self.baseline.read_bytes())
        with patch.dict(sys.modules,{'mkdocs.exceptions':errors}):
            with self.assertRaises(errors.PluginError):hook.on_pre_build({'docs_dir':str(docs)})
            (docs/'documents'/'bad.md').unlink();hook.on_pre_build({'docs_dir':str(docs)})


if __name__ == '__main__':
    unittest.main()

"""MkDocs pre-build gate. Install together with metadata tools at docs-repo/tools/."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_document_metadata import check


def on_pre_build(config):
    from mkdocs.exceptions import PluginError
    docs = Path(config['docs_dir'])
    try:
        result = check(docs / 'documents', docs.parent / '.aosdf/document-metadata-legacy.json')
    except (ValueError, OSError, KeyError) as error:
        raise PluginError('Document metadata gate: ' + str(error)) from error
    if result['errors']:
        raise PluginError('Document metadata gate failed:\n' + '\n'.join(result['errors']))

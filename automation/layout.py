"""Portable source/install layout; no implicit traversal to a private workspace."""
from pathlib import Path
import os
HERE = Path(__file__).resolve().parent
THREADS = HERE / "coordination-threads"
PROJECT_ROOT = Path(os.environ.get("AOSDF_PROJECT_ROOT", str(HERE.parent))).resolve()
AGENT_SYSTEM = HERE.parent
DOCUMENTS = Path(os.environ.get("AOSDF_DOCUMENTS_ROOT", str(HERE.parent.parent if HERE.parent.name == "05_AI_Agent_System" else HERE.parent))).resolve()
PROJECT_ID = os.environ.get("AOSDF_PROJECT_ID", "aosdf-project")
_TOOL_DEFAULTS = (DOCUMENTS / "tools", DOCUMENTS.parent / "tools", DOCUMENTS.parent.parent / "tools")
DOCUMENT_TOOLS = Path(os.environ.get("AOSDF_DOCUMENT_TOOLS", str(next((p for p in _TOOL_DEFAULTS if (p / "create_document.py").is_file()), DOCUMENTS / "tools")))).resolve()

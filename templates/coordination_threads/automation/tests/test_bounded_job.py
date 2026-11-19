"""The product pilot must not be usable from a reusable template."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bounded_job

class BoundedJobTests(unittest.TestCase):
    def test_foreign_authorization_cannot_activate_adapter(self):
        for config in (None, {}, {"status": "prepared", "founder_auth_ref": "foreign", "thread": 1}):
            with self.assertRaises(ValueError):
                bounded_job.validate_config(config)

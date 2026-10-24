import tempfile
from pathlib import Path
import shutil
import unittest
from public_audit import audit_public, ROOT

class PublicAuditTests(unittest.TestCase):
    def test_exact_synthetic_public_directory(self):
        self.assertEqual(audit_public()['status'],'PASSED')

    def test_private_file_symlink_and_changed_payload_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            for name in ('index.html','.nojekyll'):shutil.copyfile(ROOT/'docs'/name,folder/name)
            private=folder/'holdings.csv';private.write_text('private fixture')
            with self.assertRaisesRegex(ValueError,'only'):audit_public(folder)
            private.unlink()
            index=folder/'index.html';text=index.read_text();index.write_text(text.replace('const DATA = {','const DATA = {"private":true,',1))
            with self.assertRaisesRegex(ValueError,'payload'):audit_public(folder)
            index.unlink();index.symlink_to(ROOT/'docs/index.html')
            with self.assertRaisesRegex(ValueError,'symlink'):audit_public(folder)

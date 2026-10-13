import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import distribution as d
import install as installer
ROOT=Path(__file__).resolve().parents[1]

class MigrationTests(unittest.TestCase):
    def legacy(self, dest):
        dest.mkdir()
        names=tuple(n for n in d.FILES if n!='scripts/mcp_server.py')
        self.assertEqual(len(names),21)
        for n in names:
            p=dest/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
        hashes={n:hashlib.sha256((dest/n).read_bytes()).hexdigest()for n in names}
        (dest/d.MARKER).write_text(json.dumps(dict(product='token-router',schema_version=1,files=hashes)))
        return hashes

    def test_known_legacy_update_and_restore_preserve_exact_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);dest=root/'skill';old=self.legacy(dest)
            self.assertEqual(d.read_install(dest)['files'],old)
            result=installer.install(ROOT,dest);backup=Path(result['backup'])
            self.assertTrue((dest/'scripts/mcp_server.py').is_file())
            self.assertEqual(d.read_install(backup)['files'],old)
            installer.install(backup,dest)
            self.assertEqual(d.read_install(dest)['files'],old)
            self.assertFalse((dest/'scripts/mcp_server.py').exists())

    def test_unknown_missing_or_extra_legacy_inventory_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            dest=Path(temp)/'skill';old=self.legacy(dest)
            bad=dict(old);bad.pop('SKILL.md')
            marker=dest/d.MARKER;record=json.loads(marker.read_text());record['files']=bad;marker.write_text(json.dumps(record))
            with self.assertRaises(ValueError):d.read_install(dest)
            record['files']=old;marker.write_text(json.dumps(record));(dest/'scripts/mcp_server.py').write_text('unmanaged')
            with self.assertRaises(ValueError):d.read_install(dest)

if __name__=='__main__':unittest.main()

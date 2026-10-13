import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import install as ins
import distribution as d
ROOT=Path(__file__).resolve().parents[1]

class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.dest=Path(self.temp.name)/'skill';ins.install(ROOT,self.dest)
        self.current=None;self.changes=[]
    def run(self,args):
        if args[0]=='get':return self.current
        self.changes.append(args)
        if args[0]=='add':self.current={'transport':{'type':'stdio','command':args[3],'args':args[4:],'cwd':None,'env':None,'env_vars':[]}}
        if args[0]=='remove':self.current=None
        return None
    def test_connect_is_idempotent_and_disconnect_only_managed_transport(self):
        with patch.object(ins,'codex_mcp',side_effect=self.run):
            ins.connect_codex(self.dest,[]);record=d.read_install(self.dest)['codex_mcp'];self.assertNotIn('--allow-root',record['args'])
            ins.connect_codex(self.dest,[]);self.assertEqual(len(self.changes),1)
            ins.disconnect_codex(self.dest);self.assertIsNone(self.current);self.assertNotIn('codex_mcp',d.read_install(self.dest))
    def test_foreign_or_changed_server_is_not_overwritten(self):
        self.current={'transport':{'type':'stdio','command':'other','args':[]}}
        with patch.object(ins,'codex_mcp',side_effect=self.run):
            with self.assertRaises(ValueError):ins.connect_codex(self.dest,[])
        self.assertEqual(self.changes,[])
        self.current=None
        with patch.object(ins,'codex_mcp',side_effect=self.run):
            ins.connect_codex(self.dest,[]);self.current['transport']['env']={'CUSTOM':'preserve'}
            with self.assertRaises(ValueError):ins.disconnect_codex(self.dest)
        self.assertEqual(len(self.changes),1)
    def test_update_preserves_registration_and_invalid_root_is_nonmutating(self):
        with patch.object(ins,'codex_mcp',side_effect=self.run):
            with self.assertRaises(ValueError):ins.connect_codex(self.dest,[str(self.dest/'missing')])
            self.assertEqual(self.changes,[])
            ins.connect_codex(self.dest,[str(self.dest.parent)])
        before=d.read_install(self.dest)['codex_mcp'];ins.install(ROOT,self.dest)
        self.assertEqual(d.read_install(self.dest)['codex_mcp'],before)

if __name__=='__main__':unittest.main()

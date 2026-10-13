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
        writer=patch.object(ins,'write_codex_slot',side_effect=self.fake_write)
        writer.start();self.addCleanup(writer.stop)
    def fake_write(self, expected, value):
        self.changes.append(('scoped', value))
        if value is None:self.current=None
        else:self.current={'transport':{'type':'stdio','command':value['command'],'args':value['args'],'cwd':None,'env':None,'env_vars':[]}}
        return True
    def fake_codex(self,args):
        self.assertEqual(args,['get','token-router','--json'])
        return self.current
    def test_connect_is_idempotent_and_disconnect_only_managed_transport(self):
        with patch.object(ins,'read_codex_server',side_effect=lambda:{'effective_omit_tools_from':['deferred'],'server':{'command':self.current['transport']['command'],'args':self.current['transport']['args'],'omit_tools_from':['deferred']}}),patch.object(ins,'set_direct_exposure',return_value=True),patch.object(ins,'codex_mcp',side_effect=self.fake_codex):
            ins.connect_codex(self.dest,[]);record=d.read_install(self.dest)['codex_mcp'];self.assertNotIn('--allow-root',record['args'])
            ins.connect_codex(self.dest,[]);self.assertEqual(len(self.changes),1)
            ins.disconnect_codex(self.dest);self.assertIsNone(self.current);self.assertNotIn('codex_mcp',d.read_install(self.dest))
    def test_foreign_or_changed_server_is_not_overwritten(self):
        self.current={'transport':{'type':'stdio','command':'other','args':[]}}
        with patch.object(ins,'read_codex_server',side_effect=lambda:{'effective_omit_tools_from':['deferred'],'server':{'command':self.current['transport']['command'],'args':self.current['transport']['args'],'omit_tools_from':['deferred']}}),patch.object(ins,'set_direct_exposure',return_value=True),patch.object(ins,'codex_mcp',side_effect=self.fake_codex):
            with self.assertRaises(ValueError):ins.connect_codex(self.dest,[])
        self.assertEqual(self.changes,[])
        self.current=None
        with patch.object(ins,'read_codex_server',side_effect=lambda:{'effective_omit_tools_from':['deferred'],'server':{'command':self.current['transport']['command'],'args':self.current['transport']['args'],'omit_tools_from':['deferred']}}),patch.object(ins,'set_direct_exposure',return_value=True),patch.object(ins,'codex_mcp',side_effect=self.fake_codex):
            ins.connect_codex(self.dest,[]);self.current['transport']['env']={'CUSTOM':'preserve'}
            with self.assertRaises(ValueError):ins.disconnect_codex(self.dest)
        self.assertEqual(len(self.changes),1)
    def test_user_filters_and_disabled_setting_are_preserved(self):
        with patch.object(ins,'read_codex_server',side_effect=lambda:{'effective_omit_tools_from':['deferred'],'server':{'command':self.current['transport']['command'],'args':self.current['transport']['args'],'omit_tools_from':['deferred']}}),patch.object(ins,'set_direct_exposure',return_value=True),patch.object(ins,'codex_mcp',side_effect=self.fake_codex):
            ins.connect_codex(self.dest,[])
            self.current['enabled_tools']=['read_pytest_failures']
            with self.assertRaises(ValueError):ins.disconnect_codex(self.dest)
            with self.assertRaises(ValueError):ins.connect_codex(self.dest,[])
        self.assertEqual(len(self.changes),1)
    def test_disabled_existing_matching_server_is_never_mutated(self):
        self.current={'enabled':False,'transport':{'type':'stdio','command':str(Path(sys.executable).absolute()),'args':[str(self.dest/'scripts/mcp_server.py')],'cwd':None,'env':None,'env_vars':[]}}
        with patch.object(ins,'codex_mcp',side_effect=self.fake_codex),patch.object(ins,'set_direct_exposure') as write:
            with self.assertRaises(ValueError):ins.connect_codex(self.dest,[])
            write.assert_not_called()
        self.assertEqual(self.changes,[])
    def test_marker_failure_removes_only_new_registration(self):
        with patch.object(ins,'read_codex_server',side_effect=lambda:{'effective_omit_tools_from':['deferred'],'server':{'command':self.current['transport']['command'],'args':self.current['transport']['args'],'omit_tools_from':['deferred']}}),patch.object(ins,'set_direct_exposure',return_value=True),patch.object(ins,'codex_mcp',side_effect=self.fake_codex),patch.object(ins,'save_marker',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):ins.connect_codex(self.dest,[])
        self.assertIsNone(self.current)
        self.assertNotIn('codex_mcp',d.read_install(self.dest))
    def test_failed_creation_does_not_enter_rollback(self):
        with patch.object(ins,'codex_mcp',side_effect=self.fake_codex),patch.object(ins,'write_codex_slot',side_effect=ins.CodexConfigError('rpc_error')) as write:
            with self.assertRaisesRegex(ins.CodexConfigError,'rpc_error'):
                ins.connect_codex(self.dest,[])
            self.assertEqual(write.call_count,1)

    def test_unavailable_postwrite_snapshot_preserves_original_error(self):
        with patch.object(ins,'codex_mcp',side_effect=[None, ValueError('inspection failed')]):
            with self.assertRaisesRegex(ValueError,'inspection failed'):
                ins.connect_codex(self.dest,[])
        self.assertIsNotNone(self.current)
        self.assertEqual(len(self.changes),1)

    def test_connected_install_cannot_restore_legacy_without_disconnect(self):
        with patch.object(ins,'read_codex_server',side_effect=lambda:{'effective_omit_tools_from':['deferred'],'server':{'command':self.current['transport']['command'],'args':self.current['transport']['args'],'omit_tools_from':['deferred']}}),patch.object(ins,'set_direct_exposure',return_value=True),patch.object(ins,'codex_mcp',side_effect=self.fake_codex):ins.connect_codex(self.dest,[])
        with tempfile.TemporaryDirectory() as temp:
            old=Path(temp)/'old';old.mkdir()
            import shutil
            for n in d.LEGACY_FILES:
                target=old/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
            hashes={n:d.digest(old/n)for n in d.LEGACY_FILES}
            (old/d.MARKER).write_text(json.dumps(dict(product='token-router',schema_version=1,files=hashes)))
            with self.assertRaises(ValueError):ins.install(old,self.dest)
        self.assertIsNotNone(self.current)
    def test_update_preserves_registration_and_invalid_root_is_nonmutating(self):
        with patch.object(ins,'read_codex_server',side_effect=lambda:{'effective_omit_tools_from':['deferred'],'server':{'command':self.current['transport']['command'],'args':self.current['transport']['args'],'omit_tools_from':['deferred']}}),patch.object(ins,'set_direct_exposure',return_value=True),patch.object(ins,'codex_mcp',side_effect=self.fake_codex):
            with self.assertRaises(ValueError):ins.connect_codex(self.dest,[str(self.dest/'missing')])
            self.assertEqual(self.changes,[])
            ins.connect_codex(self.dest,[str(self.dest.parent)])
        before=d.read_install(self.dest)['codex_mcp'];ins.install(ROOT,self.dest)
        self.assertEqual(d.read_install(self.dest)['codex_mcp'],before)

if __name__=='__main__':unittest.main()

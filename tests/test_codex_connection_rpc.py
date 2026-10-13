import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from install import ConfigRPC, CodexConfigError as ConnectionError, read_codex_server, set_direct_exposure

SERVER = {'command': 'python3', 'args': ['/managed/mcp_server.py']}

def layer():
    return {'layers': [{'name': {'type': 'user', 'file': '/tmp/config.toml'},
        'version': 'v1', 'config': {'secret': 'NEVER_RETURN', 'mcp_servers': {
            'other': {'env': {'KEY': 'NEVER_RETURN'}}, 'token-router': SERVER.copy()}}}]}

class ConfigTests(unittest.TestCase):
    def test_scoped_read_and_write(self):
        rpc = Mock(); rpc.call.side_effect = [layer(), {"status":"ok"}]
        self.assertTrue(set_direct_exposure(SERVER, rpc))
        self.assertEqual(rpc.call.call_args.args, ('config/value/write', {
            'keyPath': 'mcp_servers.token-router.omit_tools_from', 'value': ['deferred'],
            'mergeStrategy': 'replace', 'filePath': '/tmp/config.toml', 'expectedVersion': 'v1'}))
        rpc.call.return_value = layer(); rpc.call.side_effect = None
        self.assertNotIn('NEVER_RETURN', repr(read_codex_server(rpc)))

    def test_reject_foreign_transport_before_write(self):
        for expected in ({}, {'command':'bad', 'args':[]}, {'command':'python3','args':'bad'}):
            rpc=Mock();rpc.call.return_value=layer()
            with self.assertRaisesRegex(ConnectionError,'server_not_owned'):
                set_direct_exposure(expected,rpc)
            self.assertEqual(rpc.call.call_count,1)

    def test_missing_and_ambiguous(self):
        rpc=Mock();value=layer();value['layers'][0]['config']['mcp_servers'].pop('token-router')
        rpc.call.return_value=value;self.assertIsNone(read_codex_server(rpc))
        rpc.call.return_value={'layers':[]}
        with self.assertRaises(ConnectionError):read_codex_server(rpc)

    def fake(self, body):
        return [sys.executable, '-u', '-c', body]

    def test_protocol_no_model_methods(self):
        code='''import sys,json
for line in sys.stdin:
 r=json.loads(line)
 if r['method']=='initialized':continue
 assert r['method'] in ('initialize','config/read')
 print(json.dumps({'id':r['id'],'result':{}}),flush=True)
'''
        with ConfigRPC(self.fake(code)) as rpc:
            self.assertEqual(rpc.call('config/read',{'includeLayers':True}),{})
            with self.assertRaises(ConnectionError):rpc.call('turn/start',{})
        self.assertIsNotNone(rpc.process.poll())

    def test_failure_modes_safe_and_reaped(self):
        for body,reason in [("print('bad',flush=True)",'malformed_response'),
              ("pass",'unexpected_eof'),
              ("import time;time.sleep(3)",'timeout'),
              ("import sys,json;r=json.loads(sys.stdin.readline());print(json.dumps({'id':r['id'],'error':{'message':'SECRET'}}),flush=True)",'rpc_error'),
              ("print('x'*4000001,flush=True)",'response_limit')]:
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(ConnectionError,reason) as caught:
                    ConfigRPC(self.fake(body),timeout=.2,total_timeout=.3)
                self.assertNotIn('SECRET',str(caught.exception))

    @unittest.skipUnless(shutil.which('codex'), 'Codex unavailable')
    def test_real_temporary_home_config_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'config.toml'
            path.write_text('unrelated = "preserved"\n[mcp_servers.token-router]\ncommand = "python3"\nargs = ["/managed/mcp_server.py"]\n')
            env=os.environ.copy();env['CODEX_HOME']=tmp
            with ConfigRPC(env=env) as rpc:
                self.assertEqual(read_codex_server(rpc)['server']['command'],'python3')
                set_direct_exposure(SERVER,rpc)
                self.assertEqual(read_codex_server(rpc)['server']['omit_tools_from'],['deferred'])
            self.assertIn('unrelated = "preserved"',path.read_text())
            self.assertFalse((Path(tmp)/'auth.json').exists())

    def test_scoped_slot_absence_concurrency_and_null_delete(self):
        from install import read_codex_slot, write_codex_slot
        rpc=Mock(); empty=layer();empty['layers'][0]['config']['mcp_servers'].pop('token-router')
        rpc.call.return_value=empty
        self.assertEqual(read_codex_slot(rpc)['version'],'v1')
        self.assertIsNone(read_codex_slot(rpc)['server'])
        rpc.call.side_effect=[layer(), {'status':'ok'}]
        write_codex_slot(SERVER,None,rpc)
        self.assertEqual(rpc.call.call_args.args[1], {
            'keyPath':'mcp_servers.token-router','value':None,'mergeStrategy':'replace',
            'filePath':'/tmp/config.toml','expectedVersion':'v1'})
        rpc.reset_mock();rpc.call.side_effect=None;rpc.call.return_value=layer()
        with self.assertRaisesRegex(ConnectionError,'server_changed'):
            write_codex_slot(None,SERVER,rpc)
        self.assertEqual(rpc.call.call_count,1)

    @unittest.skipUnless(shutil.which('codex'), 'Codex unavailable')
    def test_real_scoped_create_delete_preserves_unrelated_bytes(self):
        from install import read_codex_slot, write_codex_slot
        original = ('# top comment\nmodel = "gpt-6.1-sol"\n\n'
            '[mcp_servers.other] # table comment\ncommand = "python3"\n'
            'args = [] # empty args\nstartup_timeout_sec = 17 # integer\n'
            'tool_timeout_sec = 23\nenabled_tools = [] # means none\n'
            'disabled_tools = []\n# trailing comment\n')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'config.toml';path.write_text(original)
            env=os.environ.copy();env['CODEX_HOME']=tmp
            with ConfigRPC(env=env) as rpc:
                self.assertIsNone(read_codex_slot(rpc)['server'])
                value=dict(SERVER,omit_tools_from=['deferred'])
                write_codex_slot(None,value,rpc)
                self.assertTrue(path.read_text().startswith(original.rsplit('# trailing comment',1)[0]))
                self.assertIn('# trailing comment\n',path.read_text())
                self.assertEqual(read_codex_server(rpc)['server'],value)
                # Versions track semantic configuration; comments are preserved, not CAS inputs.
                comment_version=read_codex_slot(rpc)
                path.write_text(path.read_text()+'\n# comment-only edit\n')
                reply=rpc.call('config/value/write', {'keyPath':'mcp_servers.token-router.omit_tools_from',
                    'value':['deferred'],'mergeStrategy':'replace','filePath':comment_version['filePath'],
                    'expectedVersion':comment_version['version']})
                self.assertEqual(reply['status'],'ok')
                self.assertIn('# comment-only edit',path.read_text())
                # Concurrent unrelated semantic edits must reject stale configuration versions.
                stale=read_codex_slot(rpc)
                path.write_text(path.read_text().replace('startup_timeout_sec = 17', 'startup_timeout_sec = 19')+'\n# concurrent edit\n')
                with self.assertRaises(ConnectionError):
                    rpc.call('config/value/write', {'keyPath':'mcp_servers.token-router',
                        'value':None,'mergeStrategy':'replace','filePath':stale['filePath'],
                        'expectedVersion':stale['version']})
                self.assertEqual(read_codex_server(rpc)['server'],value)
                write_codex_slot(value,None,rpc)
                self.assertIsNone(read_codex_server(rpc))
                self.assertTrue(path.read_text().startswith(original.replace('startup_timeout_sec = 17', 'startup_timeout_sec = 19').rsplit('# trailing comment',1)[0]))
                self.assertIn('# trailing comment\n',path.read_text())
                self.assertIn('# concurrent edit',path.read_text())

if __name__=='__main__':unittest.main()

import importlib.util
import io
import json
from pathlib import Path, PureWindowsPath, PurePosixPath
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('mcp_reader',Path(__file__).resolve().parents[1]/'scripts/mcp_server.py')

class MCPTests(unittest.TestCase):
    def setUp(self):
        self.m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(self.m)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.path=self.root/'build.log';self.path.write_text('source')
        self.server=self.m.Server([self.root])
        self.args={'path':str(self.path),'failure_headers':['____ test_a ____','____ test_b ____']}
    def test_validation_and_escape(self):
        for delta in [{'failure_headers':['same','same']},{'failure_headers':[True,'x']},{'path':False},{'extra':1},{'result_term':'\nx'}]:
            result=self.server.call({**self.args,**delta});self.assertTrue(result['isError'])

    def test_default_root_guard_posix_and_windows(self):
        for cls,root,home,project in [(PurePosixPath,'/','/home/u','/work/project'),(PureWindowsPath,'C:/','C:/Users/u','C:/work/project')]:
            self.assertFalse(self.m.default_root_allowed(cls(root),cls(home)))
            self.assertFalse(self.m.default_root_allowed(cls(home),cls(home)))
            self.assertTrue(self.m.default_root_allowed(cls(project),cls(home)))
    def test_existing_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            other=Path(outside)/'private.log';other.write_text('SECRET')
            link=self.root/'escape.log'
            try:link.symlink_to(other)
            except OSError as exc:self.skipTest('symlinks unavailable: '+str(exc))
            with patch.object(self.m.subprocess,'run',side_effect=AssertionError('must reject before subprocess')):
                self.assertTrue(self.server.call({**self.args,'path':str(link)})['isError'])
    def test_invalid_types_never_start_reader(self):
        with patch.object(self.m.subprocess,'run',side_effect=AssertionError('unexpected reader')):
            for args in (None,False,[],{}, {**self.args,'failure_headers':'name'}, {**self.args,'result_term':True}, {**self.args,'failure_headers':['a',3]}):
                self.assertTrue(self.server.call(args)['isError'])
    def test_mutation_after_reader_withholds_success(self):
        def changed(*a,**kw):
            self.path.write_text('mutated')
            return subprocess.CompletedProcess([],0,'SECRET','[token-router status] {"status":"auto_candidates","activation":"activate"}\n')
        with patch.object(self.m.subprocess,'run',side_effect=changed):result=self.server.call(self.args)
        self.assertTrue(result['isError']);self.assertNotIn('SECRET',json.dumps(result))
    def test_rpc_params_and_identifiers(self):
        self.server.initialized=True
        for params in (None,False,[],42):
            reply=self.server.dispatch({'jsonrpc':'2.0','id':1,'method':'tools/call','params':params})
            self.assertEqual(reply['error']['code'],-32602)
        for ident in (None,True,[],{}):
            reply=self.server.dispatch({'jsonrpc':'2.0','id':ident,'method':'ping'})
            self.assertEqual(reply['error']['code'],-32600)
    def test_credentials_and_router_overrides_scrubbed(self):
        done=subprocess.CompletedProcess([],2,'','')
        extra={'ROUTER_MOCK_RESPONSE':'secret','ROUTER_CODEX_BIN':'bad','OPENAI_API_KEY':'secret','CODEX_API_KEY':'secret','OPENAI_BASE_URL':'secret'}
        with patch.dict(self.m.os.environ,extra),patch.object(self.m.subprocess,'run',return_value=done) as run:
            self.server.call(self.args)
        env=run.call_args.kwargs['env']
        for key in extra:self.assertNotIn(key,env)
        cmd=run.call_args.args[0]
        self.assertIn('--activation-profile',cmd);self.assertIn('log-context',cmd)
        self.assertFalse(set(cmd)&{'--force-model','--deterministic','--optimize'})
    def test_exact_payload_and_safe_command(self):
        payload='--- source unchanged ---\n'
        done=subprocess.CompletedProcess([],0,payload,'[token-router status] {"status":"auto_candidates","activation":"activate"}\n')
        with patch.object(self.m.subprocess,'run',return_value=done) as run:
            result=self.server.call(self.args)
        self.assertFalse(result['isError']);self.assertEqual(result['content'][0]['text'],payload)
        args,kw=run.call_args;self.assertNotIn('--force-model',args[0]);self.assertNotIn('shell',kw)
        self.assertEqual(kw['timeout'],5);self.assertEqual(kw['env']['TOKEN_ROUTER_ACTIVE'],'1')
        self.assertFalse(any(k.startswith('ROUTER_') for k in kw['env']))
    def test_failure_never_echoes_source_or_diagnostics(self):
        for outcome in [subprocess.CompletedProcess([],2,'SECRET','SECRET'),subprocess.CompletedProcess([],0,'x'*12001,''),subprocess.TimeoutExpired('secret',5)]:
            with patch.object(self.m.subprocess,'run',side_effect=outcome if isinstance(outcome,Exception) else None,return_value=outcome):
                result=self.server.call(self.args)
            self.assertTrue(result['isError']);self.assertNotIn('SECRET',json.dumps(result))
    def test_transport_and_negotiation(self):
        requests=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05'}},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/list'},{'jsonrpc':'2.0','id':3,'method':'ping'}]
        source=io.BytesIO(('\n'.join(json.dumps(x) for x in requests)+'\n').encode());out=io.StringIO()
        self.m.serve(self.server,source,out)
        replies=[json.loads(x) for x in out.getvalue().splitlines()]
        self.assertEqual(len(replies),3);self.assertEqual(replies[0]['result']['protocolVersion'],'2024-11-05')
        self.assertEqual(replies[1]['result']['tools'][0]['name'],'read_pytest_failures')
    def test_oversized_request_and_bad_json(self):
        out=io.StringIO();self.m.serve(self.server,io.BytesIO(b'x'*65537+b'\n{bad}\n'),out)
        self.assertTrue(all('error' in json.loads(x) for x in out.getvalue().splitlines()))
    def test_real_reader_reuses_guarded_cli(self):
        lines=['padding '*12+'\n']*1200
        for start,name in [(100,'alpha'),(600,'beta')]:
            lines[start]='______ test_'+name+' ______\n';lines[start+1]='value = broken\n';lines[start+2]='tests/test_x.py:42: ValueError\n'
        lines[1100]='2 failed, 20 passed\n';self.path.write_text(''.join(lines))
        args={**self.args,'failure_headers':['______ test_alpha ______','______ test_beta ______']}
        result=self.server.call(args);self.assertFalse(result['isError'],result)
        self.assertIn('103: tests/test_x.py:42: ValueError',result['content'][0]['text'])
        self.assertNotIn('padding padding padding',result['content'][0]['text'][:50])

if __name__=='__main__':unittest.main()

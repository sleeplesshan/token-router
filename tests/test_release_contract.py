import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import router as r
import source_guard as sg
import install as installer
from distribution import inventory,read_install
ROOT=Path(__file__).resolve().parents[1]

class ReleaseContract(unittest.TestCase):
    def route(self,path,*flags):
        out,err=io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err),patch.object(r,'call_codex',side_effect=AssertionError('unexpected cloud')):
            code=r.main(['router.py','heavy_code',str(path),*flags])
        statuses=[json.loads(s.split('] ',1)[1]) for s in err.getvalue().splitlines() if s.startswith('[token-router status]')]
        return code,out.getvalue(),statuses[-1]
    def test_options_and_default_no_return_work(self):
        self.assertEqual(r.parse_args(['r','heavy_code','a.py']).return_context,'off')
        self.assertEqual(r.parse_args(['r','heavy_code','a.py','--return-target','A.f']).return_context,'bounded')
        for flags in (['--return-context','off','--return-target','f'],['--policy-version','v2.5','--read-scope','whole','--return-target','f']):
            with self.assertRaises(SystemExit):r.parse_args(['r','heavy_code','a.py',*flags])
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'large.py';p.write_text('# neutral\n'*13000)
            original=r.complete_python_statements
            def complete(*args,**kw):
                self.assertIsNone(kw.get('return_spans'));self.assertIsNone(kw.get('return_definitions'));return original(*args,**kw)
            with patch.object(r,'complete_python_statements',side_effect=complete),patch.object(r,'bounded_return_supplement',side_effect=AssertionError('disabled')):self.route(p)
    def test_usage_error_is_distinct(self):
        code,out,status=self.route('a.py','--unknown')
        self.assertEqual((code,out,status['status']),(2,'','usage_error'))
    def test_limits_never_return_partial_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'large.py';p.write_text('x'*13000+'\n'+'y\n'*20)
            for attr,value in [('MAX_SOURCE_BYTES',20),('MAX_LINE_CHARS',20),('MAX_SOURCE_LINES',2)]:
                with patch.object(sg,attr,value):
                    code,out,status=self.route(p)
                self.assertEqual((code,out,status['status']),(2,'','needs_targeted_read'));self.assertFalse(status['scan_complete'])
    @unittest.skipUnless(hasattr(os,'mkfifo'),'POSIX FIFO')
    def test_fifo_fails_without_open_or_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'fifo';os.mkfifo(p)
            result=subprocess.run([sys.executable,str(ROOT/'scripts/router.py'),'error_log',str(p)],capture_output=True,text=True,timeout=2)
            self.assertEqual(result.returncode,1);self.assertEqual(result.stdout,'')
    def test_default_has_no_socket_or_subprocess(self):
        with patch('socket.socket',side_effect=AssertionError('network')),patch('subprocess.Popen',side_effect=AssertionError('process')):
            self.assertEqual(self.route(ROOT/'samples/service.py')[0],0)
    def test_mutation_invalidates_previous_success_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source.py';source.write_text('old text')
            report=Path(tmp)/'decision.json';report.write_text('{"status":"auto_full"}')
            original=r.SourceGuard.probe
            def mutate(guard,limit):
                value=original(guard,limit);source.write_text('new text');return value
            with patch.object(r.SourceGuard,'probe',mutate):
                code,out,status=self.route(source,'--report-json',str(report))
            self.assertEqual((code,out),(1,''));self.assertFalse(report.exists())
    def test_install_update_rollback_and_local_edits(self):
        with tempfile.TemporaryDirectory(prefix='router 한글 space ') as tmp:
            dest=Path(tmp)/'skills/token-router';installer.install(ROOT,dest);before=inventory(dest)
            updated=installer.install(ROOT,dest);backup=Path(updated['backup']);self.assertEqual(before,inventory(backup))
            installer.install(backup,dest);self.assertEqual(before,inventory(dest))
            (dest/'SKILL.md').write_text('user edits')
            with self.assertRaises(ValueError):installer.install(ROOT,dest)
            self.assertEqual((dest/'SKILL.md').read_text(),'user edits')
    def test_failed_staging_and_swap_preserve_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'skill';installer.install(ROOT,dest);before=inventory(dest)
            with patch.object(installer,'smoke',side_effect=ValueError('smoke failure')):
                with self.assertRaises(ValueError):installer.install(ROOT,dest)
            self.assertEqual(before,inventory(dest))
            replace=os.replace
            def fail_stage(src,dst):
                if '-stage-' in str(src):raise OSError('injected swap failure')
                return replace(src,dst)
            with patch.object(installer.os,'replace',side_effect=fail_stage):
                with self.assertRaises(OSError):installer.install(ROOT,dest)
            self.assertEqual(before,inventory(dest))
    def test_extra_files_and_unmanaged_dest_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'skill';dest.mkdir();(dest/'AGENTS.md').write_text('personal')
            with self.assertRaises(ValueError):installer.install(ROOT,dest)
            self.assertEqual((dest/'AGENTS.md').read_text(),'personal')
            dest2=Path(tmp)/'managed';installer.install(ROOT,dest2);(dest2/'custom.txt').write_text('keep')
            with self.assertRaises(ValueError):read_install(dest2)
    @unittest.skipUnless(os.name=='posix','POSIX process group')
    def test_timeout_kills_spawned_process_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);pidfile=root/'pid';fake=root/'fake'
            fake.write_text('#!'+sys.executable+'\nimport subprocess,sys,time\nfrom pathlib import Path\np=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"])\nPath('+repr(str(pidfile))+').write_text(str(p.pid))\ntime.sleep(60)\n');fake.chmod(0o755)
            with patch.object(r,'CODEX_BIN',str(fake)),patch.object(r,'TIMEOUT_SECONDS',0.5),patch.dict(os.environ,{'ROUTER_MOCK_RESPONSE':''}):
                os.environ.pop('ROUTER_MOCK_RESPONSE',None)
                with self.assertRaises(RuntimeError):r.call_codex('test')
            pid=int(pidfile.read_text());state=subprocess.run(['ps','-o','stat=','-p',str(pid)],capture_output=True,text=True).stdout.strip()
            self.assertTrue(not state or state.startswith('Z'),state)

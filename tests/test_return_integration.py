import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import router as r


class ReturnIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'source.py';self.report=Path(self.tmp.name)/'report.json'
        self.path.write_text('# neutral padding abcdefghijklmnopqrstuvwxyz\n'*1500+
            'def lookup():\n    """\n'+'    documentation\n'*40+'    """\n    return stored_value\n'+
            '# neutral padding abcdefghijklmnopqrstuvwxyz\n'*1500)

    def run_route(self,flags=(),baseline=False):
        out,err=io.StringIO(),io.StringIO()
        with contextlib.ExitStack() as stack:
            if baseline:
                stack.enter_context(patch.object(r,'bounded_return_supplement',
                    side_effect=lambda text,targets,packet,*a:(targets,packet,{'applied':False})))
            stack.enter_context(patch.object(r,'call_codex',return_value={
                'targets':[{'start_line':1501,'end_line':1501,'reason':'selected'}]}))
            stack.enter_context(contextlib.redirect_stdout(out));stack.enter_context(contextlib.redirect_stderr(err))
            code=r.main(['router.py','heavy_code',str(self.path),'--query','lookup',
                         '--report-json',str(self.report),*flags])
        status=json.loads(next(line.split('] ',1)[1] for line in err.getvalue().splitlines() if line.startswith('[token-router status] ')))
        if self.report.exists():status=json.loads(self.report.read_text())
        return code,out.getvalue(),err.getvalue(),status

    def test_adds_return_after_baseline_action_and_sidecar_only(self):
        base=self.run_route(baseline=True);new=self.run_route()
        self.assertEqual(base[0],0);self.assertEqual(new[0],0)
        self.assertNotIn('return stored_value',base[1]);self.assertIn('return stored_value',new[1])
        self.assertTrue(new[3]['return_supplement']['applied'])
        self.assertNotIn('return_supplement',new[2]);self.assertFalse(new[3]['model_called'])
        self.assertEqual(new[3]['status'],base[3]['status'])

    def test_output_cap_cancels_to_exact_baseline_input(self):
        base=self.run_route(baseline=True)
        with patch.object(r,'MAX_OUTPUT_CHARS',len(base[1])):
            new=self.run_route()
        self.assertEqual(new[:3],base[:3])
        self.assertFalse(new[3]['return_supplement']['applied'])

    def test_reduction_threshold_cancels_to_exact_baseline_input(self):
        base=self.run_route(baseline=True);original=r.token_first_strategy
        with patch.object(r,'token_first_strategy',side_effect=lambda s,f,c,h:original(s,len(base[1])/.85,c,h)):
            new=self.run_route()
        self.assertEqual(new[:3],base[:3])
        self.assertFalse(new[3]['return_supplement']['applied'])

    def test_optional_policy_cap_preserves_baseline(self):
        flags=['--policy-version','v2.5'];base=self.run_route(flags,baseline=True)
        with patch.object(r,'MAX_OUTPUT_CHARS',len(base[1])):
            new=self.run_route(flags)
        self.assertEqual(new[:3],base[:3])

    def test_source_change_after_patch_withholds_old_and_new_source(self):
        original=r.bounded_return_supplement
        def mutate(*args,**kwargs):
            result=original(*args,**kwargs)
            self.path.write_text(self.path.read_text()+'# changed\n')
            return result
        with patch.object(r,'bounded_return_supplement',side_effect=mutate):
            code,out,_,status=self.run_route()
        self.assertEqual(code,1);self.assertEqual(out,'')
        self.assertIn('source_changed',status['reason_codes'])

    def test_explicit_modes_never_invoke_supplement(self):
        for flags in [['--deterministic'],['--force-model'],['--optimize','latency']]:
            with self.subTest(flags=flags),patch.object(r,'bounded_return_supplement',side_effect=AssertionError('unexpected supplement')):
                self.run_route(flags)

    def test_full_and_abstention_paths_do_not_supplement(self):
        with patch.object(r,'bounded_return_supplement',side_effect=AssertionError('unexpected supplement')):
            self.path.write_text('def lookup():\n    """docs"""\n    return value\n')
            self.assertEqual(self.run_route()[3]['status'],'auto_full')
            self.path.write_text('x'*150000)
            self.assertEqual(self.run_route()[0],2)

if __name__=='__main__':unittest.main()

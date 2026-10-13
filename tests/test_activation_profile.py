"""Conservative activation is task eligibility, not a token prediction."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_literal_search import r
from routing_policy import plan_activation


class HostActivationTests(unittest.TestCase):
    def test_only_native_dispersed_failure_context_is_eligible(self):
        request=dict(mode='error_log',purpose='failure_context',selectors=('ERROR: first','Total test files:'),native_guide=True)
        self.assertEqual(plan_activation(**request).action,'activate')
        for changes in ({'native_guide':False},{'visible_sufficient':True},{'purpose':'literal_lookup'},
                        {'mode':'heavy_code'},{'selectors':('one',)},{'selectors':('one','one')},
                        {'selectors':('one','')},{'purpose':'unknown'}):
            self.assertEqual(plan_activation(**{**request,**changes}).action,'bypass')


class RuntimeActivationTests(unittest.TestCase):
    def fixture(self):
        lines=['padding abcdefghijklmnopqrstuvwxyz\n']*2500
        lines[100]='ERROR: first\n';lines[103]='Traceback (most recent call last):\n'
        lines[104]='  File "a.py", line 2, in run\n';lines[105]='ValueError: first failure\n'
        lines[2000]='Total test files: 9, failed 1\n'
        return ''.join(lines)

    def call(self,text,*options):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'incident.log';p.write_text(text,encoding='utf-8')
            out,err=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                code=r.main(['router.py','error_log',str(p),'--search-term','ERROR: first',
                             '--search-term','Total test files:','--line-numbers','--compact-status',*options])
            status=json.loads(next(l.split('] ',1)[1] for l in err.getvalue().splitlines() if l.startswith('[token-router status]')))
            return code,out.getvalue(),status

    def test_admitted_packet_is_identical_without_extra_read_or_model(self):
        with patch.object(r,'call_codex',side_effect=AssertionError('model')):
            manual=self.call(self.fixture())
            gated=self.call(self.fixture(),'--activation-profile','log-context')
        self.assertEqual(gated[:2],manual[:2]);self.assertEqual(gated[0],0)
        self.assertEqual(gated[2]['activation'],'activate')
        self.assertIn('106: ValueError: first failure',gated[1])

    def test_small_single_nearby_missing_and_unstructured_are_bypassed(self):
        text=self.fixture()
        variants=[text[:7000]+'Total test files: 9\n',
                  text.replace('Total test files: 9, failed 1','no summary'),
                  text.replace('Traceback (most recent call last):','ordinary message'),
                  text.replace('Total test files: 9, failed 1','').replace('ValueError: first failure','ValueError: first failure\nTotal test files: 9')]
        for value in variants:
            with patch.object(r,'packet_from_guard',side_effect=AssertionError('no second read')):
                code,out,s=self.call(value,'--activation-profile','log-context')
            self.assertEqual((code,out),(2,''));self.assertEqual(s['activation'],'bypass')
            self.assertEqual(s['next_action'],'ordinary_search')

    def test_source_change_still_withholds_output(self):
        check=r.SourceGuard.check
        def changed(guard):
            check(guard)
            if guard.open_count>=2:raise r.SourceChanged('mutation')
        with patch.object(r.SourceGuard,'check',changed):
            code,out,s=self.call(self.fixture(),'--activation-profile','log-context')
        self.assertEqual((code,out),(1,''));self.assertEqual(s['source_consistency'],'changed')

    def test_profile_cli_conflicts_and_final_cap(self):
        for options in (['--force-model'],['--deterministic'],['--optimize','latency']):
            self.assertEqual(self.call(self.fixture(),'--activation-profile','log-context',*options)[2]['status'],'usage_error')
        with patch.object(r,'MAX_OUTPUT_CHARS',20):
            code,out,s=self.call(self.fixture(),'--activation-profile','log-context')
        self.assertEqual((code,out),(2,''));self.assertTrue(s['final_output_capped'])

    def test_default_manual_behavior_remains_unrestricted(self):
        code,out,s=self.call('ERROR: first\nTotal test files: 9\n')
        self.assertEqual(code,0);self.assertNotIn('activation',s)
        for argv in (['heavy_code','x','--symbol','f'],['heavy_code','x','--search-term','x'],['error_log','x']):
            self.assertEqual(r.main(['router.py',*argv,'--activation-profile','log-context']),2)

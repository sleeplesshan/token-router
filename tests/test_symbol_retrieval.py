import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_literal_search import r


class SymbolRetrievalTests(unittest.TestCase):
    def call(self,text,args):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.py';path.write_text(text,encoding='utf-8')
            out,err=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                code=r.main(['router.py','heavy_code',str(path),*args])
            status=json.loads(next(l.split('] ',1)[1] for l in err.getvalue().splitlines() if l.startswith('[token-router status]')))
            return code,out.getvalue(),status

    def test_complete_decorated_async_and_nested_definitions(self):
        text='class C:\n    @decorate\n    async def work(self):\n        def nested():\n            return 3\n        return nested()\n\ndef unrelated():\n    pass\n'
        with patch.object(r,'ranked_candidates',side_effect=AssertionError('no ranking')),patch.object(r,'call_codex',side_effect=AssertionError('no model')):
            code,out,status=self.call(text,['--symbol','C.work','--symbol','C.work.nested','--line-numbers'])
        self.assertEqual(code,0);self.assertIn('2:     @decorate',out)
        self.assertIn('6:         return nested()',out);self.assertNotIn('unrelated',out)
        self.assertEqual(status['output_lines'],5)
        self.assertEqual(out.count('def nested'),1)

    def test_missing_ambiguous_and_parse_failure_withhold_batch(self):
        for text,names in [('def f():\n pass\n',['f','missing']),('def f():\n pass\ndef f():\n pass\n',['f']),('@overload\ndef f():\n pass\ndef f():\n pass\n',['f']),('not valid python !',['f'])]:
            opts=[item for n in names for item in ['--symbol',n]]
            code,out,status=self.call(text,opts)
            self.assertEqual((code,out),(2,''));self.assertFalse(status['model_called'])

    def test_complete_aggregate_cap_never_truncates_definition(self):
        text='def f():\n'+'    value = 1\n'*40+'    return value\n'
        with patch.object(r,'MAX_OUTPUT_CHARS',100):
            code,out,status=self.call(text,['--symbol','f','--line-numbers'])
        self.assertEqual((code,out),(2,''));self.assertTrue(status['final_output_capped'])

    def test_probe_budget_and_line_limits(self):
        code,out,status=self.call('#'+'x'*1000001,['--symbol','f'])
        self.assertEqual((code,out),(2,''));self.assertIn('symbol_parse_budget',status['reason_codes'])
        code,out,status=self.call('\n'*250001,['--symbol','f'])
        self.assertEqual((code,out),(2,''));self.assertIn('input_limit',status['reason_codes'])

    def test_incompatible_options(self):
        for opts in [['--search-term','f'],['--search-context','0'],['--deterministic'],['--force-model'],['--optimize','latency'],['--return-context','bounded'],['--return-target','f']]:
            code,out,status=self.call('def f():\n pass\n',['--symbol','f',*opts])
            self.assertEqual((code,out),(2,''));self.assertEqual(status['status'],'usage_error')

    def test_source_change_withholds_reused_probe(self):
        check=r.SourceGuard.check
        def changed(guard):
            check(guard)
            if guard.open_count:raise r.SourceChanged('injected change')
        with patch.object(r.SourceGuard,'check',changed):
            code,out,status=self.call('def f():\n pass\n',['--symbol','f'])
        self.assertEqual((code,out),(1,''));self.assertEqual(status['source_consistency'],'changed')

    def test_compact_status_retains_actions_and_full_sidecar(self):
        text='def f():\n return 3\n'
        full=self.call(text,['--symbol','f','--line-numbers'])
        compact=self.call(text,['--symbol','f','--line-numbers','--compact-status'])
        self.assertEqual(full[:2],compact[:2]);self.assertNotIn('source_stamp',compact[2])
        self.assertFalse(compact[2]['model_called']);self.assertEqual(compact[2]['semantic_sufficiency'],'unknown')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'full.json'
            self.call(text,['--symbol','f','--compact-status','--report-json',str(path)])
            self.assertIn('source_stamp',json.loads(path.read_text()))


class PytestBlockTests(unittest.TestCase):
    def test_selected_pytest_block_completes_to_location_not_other_block(self):
        lines=['padding\n']*200
        lines[40]='2026-10-13T00:00:00Z ______ TestCase.test_selected ______\n'
        for i in range(41,60):lines[i]='2026-10-13T00:00:00Z     intermediate evidence\n'
        lines[60]='2026-10-13T00:00:00Z tests/test_case.py:42: ValueError\n'
        lines[80]='______ TestCase.test_other ______\n';lines[90]='other.py:55: TypeError\n'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'log.txt';path.write_text(''.join(lines));out,err=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                code=r.main(['router.py','error_log',str(path),'--search-term','TestCase.test_selected','--line-numbers'])
        self.assertEqual(code,0);self.assertIn('61: ',out.getvalue());self.assertNotIn('other.py',out.getvalue())

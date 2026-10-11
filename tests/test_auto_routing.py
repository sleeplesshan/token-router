"""Automatic call-elision must preserve raw evidence and explicit overrides."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('auto_router',Path(__file__).resolve().parents[1]/'scripts/router.py')
r=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(r)

class AutomaticRoutingTests(unittest.TestCase):
    def test_small_source_boundary(self):
        self.assertEqual(r.automatic_strategy(12000,0,'',[],True,[]),'auto_full')
        self.assertEqual(r.automatic_strategy(12001,0,'',[],True,[]),'model')

    def test_dense_source_uses_raw_character_ratio_and_upper_bound(self):
        self.assertEqual(r.automatic_strategy(100000,65000,'',[1],True,[]),'auto_full')
        self.assertEqual(r.automatic_strategy(100001,100001,'',[1],False,[]),'model')
        self.assertEqual(r.automatic_strategy(50000,32499,'',list(range(999)),True,[]),'model')

    def test_candidates_require_no_cut_query_match_and_both_limits(self):
        args=(200000,200,'10: needle\n',[10],False,['needle'])
        self.assertEqual(r.automatic_strategy(*args),'auto_candidates')
        for candidate,visible,truncated,terms in [('10: needle\n',[10],True,['needle']),
                ('10: needle\n',list(range(161)),False,['needle']),
                ('10: needle'+' '*12000,[10],False,['needle']),
                ('10: other\n',[10],False,['needle']),('10: needle\n',[10],False,[])]:
            self.assertEqual(r.automatic_strategy(200000,200,candidate,visible,truncated,terms),'model')

    def test_query_cannot_match_injected_line_numbers_or_gap_labels(self):
        self.assertEqual(r.automatic_strategy(200000,20,'123: other\n',[123],False,['123']),'model')
        self.assertEqual(r.automatic_strategy(200000,20,'123: value = 123\n',[123],False,['123']),'auto_candidates')
        self.assertEqual(r.automatic_strategy(200000,20,'1: other\n--- [omitted unrelated lines] ---\n',[1],False,['omitted']),'model')

    def test_small_source_more_than_output_cap_is_returned_whole(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'short.log';p.write_text('x\n'*500+'final evidence\n')
            out,err=io.StringIO(),io.StringIO()
            with patch.object(r,'call_codex',side_effect=AssertionError('unexpected model')),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                result=r.main(['router.py','error_log',str(p)])
            self.assertEqual(result,0)
            self.assertIn('RAW CONTENT FROM LINE 1 TO 501',out.getvalue())
            self.assertIn('final evidence',out.getvalue())
            self.assertIn('"model_called": false',err.getvalue())
            self.assertIn('"coverage_guaranteed": true',err.getvalue())

    def test_force_model_overrides_small_file_bypass(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'short.py';p.write_text('def target():\n    return 42\n')
            with patch.object(r,'call_codex',return_value={'targets':[{'start_line':1,'end_line':2,'reason':'target'}]}) as call,contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                result=r.main(['router.py','heavy_code',str(p),'--force-model'])
            self.assertEqual(result,0);call.assert_called_once()

    def test_sparse_large_source_returns_all_candidates_without_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source.py'
            lines=['neutral '+'.'*190+'\n']*1100
            lines[500]='def precise_symbol():\n'
            p.write_text(''.join(lines))
            out,err=io.StringIO(),io.StringIO()
            with patch.object(r,'call_codex',side_effect=AssertionError('unexpected model')),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                status=r.main(['router.py','heavy_code',str(p),'--query','precise_symbol'])
            self.assertEqual(status,0)
            self.assertIn('"status": "auto_candidates"',err.getvalue())
            self.assertIn('"coverage_guaranteed": false',err.getvalue())
            self.assertIn('def precise_symbol():',out.getvalue())

    def test_force_flags_are_mutually_exclusive(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
            r.parse_args(['router.py','heavy_code','file','--force-model','--deterministic'])

if __name__=='__main__':unittest.main()

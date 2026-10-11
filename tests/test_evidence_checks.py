import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('evidence_router',Path(__file__).resolve().parents[1]/'scripts/router.py')
r=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(r)
from evidence_checks import assess_query_evidence, complete_python_statements

class EvidenceTests(unittest.TestCase):
    def test_no_query_missing_and_partial_match_are_distinct(self):
        self.assertEqual(assess_query_evidence([],[])['query_anchor'],'unknown')
        self.assertEqual(assess_query_evidence(['missing'],[])['query_anchor'],'missing')
        checks=assess_query_evidence(['found','missing'],[0])
        self.assertEqual(checks['query_anchor'],'satisfied')
        self.assertEqual(checks['unmatched_terms'],['missing'])
        self.assertEqual(checks['semantic_sufficiency'],'unknown')

    def test_no_match_abstains_instead_of_offering_unrelated_tail(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'file.txt';p.write_text('ordinary = 1234567890123456789012345\n'*5000)
            out,err=io.StringIO(),io.StringIO()
            with patch.object(r,'call_codex',side_effect=AssertionError('cloud forbidden')), contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                code=r.main(['router.py','heavy_code',str(p),'--query','missing_symbol'])
            self.assertEqual(code,2);self.assertEqual(out.getvalue(),'')
            self.assertIn('search_query_terms',err.getvalue())
            self.assertIn('"suggested_ranges": []',err.getvalue())

    def test_small_no_match_still_reads_full(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'file.txt';p.write_text('x = 1\n')
            out,err=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                code=r.main(['router.py','heavy_code',str(p),'--query','missing_symbol'])
            self.assertEqual(code,0);self.assertIn('auto_full',err.getvalue())

    def test_multiline_statement_completes_from_middle(self):
        text='value = call(\n    first,\n    second,\n)\nafter = 1\n'
        targets=[{'start_line':2,'end_line':2,'reason':'core'}]
        expanded,checks=complete_python_statements(text,targets)
        self.assertEqual((expanded[0]['start_line'],expanded[0]['end_line']),(1,4))
        self.assertEqual(checks['added_lines'],3)

    def test_long_statement_stays_partial_and_budget_is_respected(self):
        text='value = [\n'+''.join(f'    {i},\n' for i in range(20))+']\n'
        core=[{'start_line':5,'end_line':5,'reason':'core'}]
        out,checks=complete_python_statements(text,core)
        self.assertEqual(checks['added_lines'],0)
        self.assertEqual(checks['boundary_status'],'partial')
        out,checks=complete_python_statements(text,core,max_span=30,max_added=2)
        self.assertLessEqual(checks['added_lines'],2)

    def test_many_overlapping_nodes_respect_aggregate_limit(self):
        text = ''.join(f'v{i} = call(\n    {i},\n    second,\n)\n' for i in range(100))
        cores = [{'start_line':i*4+2,'end_line':i*4+2,'reason':'core'} for i in range(100)]
        expanded,checks=complete_python_statements(text,cores)
        kept={n for t in expanded for n in range(t['start_line'],t['end_line']+1)}
        self.assertTrue({i*4+2 for i in range(100)} <= kept)
        self.assertLessEqual(checks['added_lines'],128)
        self.assertEqual(len(kept)-100,checks['added_lines'])
        self.assertEqual(checks['boundary_status'],'partial')

    def test_syntax_output_is_rechecked_against_admission_budget(self):
        with patch.object(r,'MAX_PROMPT_CHARS',1000):
            self.assertEqual(r.token_first_strategy(500000,500100,1001,True),'needs_targeted_read')
            self.assertEqual(r.token_first_strategy(500000,500100,999,True),'auto_candidates')

    def test_invalid_python_preserves_original_ranges(self):
        core=[{'start_line':1,'end_line':1,'reason':'core'}]
        out,checks=complete_python_statements('def broken(',core)
        self.assertEqual(out,core);self.assertEqual(checks['syntax'],'unknown')

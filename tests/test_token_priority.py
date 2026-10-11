"""Token-first policy avoids speculative extra model calls and opaque truncation."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('token_priority',Path(__file__).resolve().parents[1]/'scripts/router.py')
r=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(r)

class TokenPriorityTests(unittest.TestCase):
    def test_reduction_threshold_and_rendered_packet_budget(self):
        self.assertEqual(r.token_first_strategy(50000,51000,43350,True),'auto_candidates')
        self.assertEqual(r.token_first_strategy(50000,51000,43351,True),'auto_full')
        self.assertEqual(r.token_first_strategy(500000,500200,120001,True),'needs_targeted_read')
        self.assertEqual(r.token_first_strategy(500000,500200,0,False),'needs_targeted_read')

    def test_small_source_preserves_whole_input(self):
        self.assertEqual(r.token_first_strategy(12000,12150,100,True),'auto_full')

    def test_candidate_output_can_exceed_160_without_losing_admitted_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source.py';lines=['neutral '+'.'*80+'\n']*2000
            for i in range(300,550):lines[i]='def evidence_%d(): pass\n'%i
            p.write_text(''.join(lines));out,err=io.StringIO(),io.StringIO()
            with patch.object(r,'call_codex',side_effect=AssertionError('token-first must not call model')),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                code=r.main(['router.py','heavy_code',str(p),'--query','evidence'])
            self.assertEqual(code,0)
            self.assertIn('"status": "auto_candidates"',err.getvalue())
            self.assertIn('def evidence_300(): pass',out.getvalue())
            self.assertIn('def evidence_549(): pass',out.getvalue())

    def test_large_unhelpful_source_requires_targeted_read_without_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'one-line.txt';p.write_text('x'*150000)
            out,err=io.StringIO(),io.StringIO()
            with patch.object(r,'call_codex',side_effect=AssertionError('unexpected model')),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                code=r.main(['router.py','heavy_code',str(p)])
            self.assertEqual(code,2)
            self.assertEqual(out.getvalue(),'')
            self.assertIn('needs_targeted_read',err.getvalue())
            self.assertIn('"model_called": false',err.getvalue())

    def test_single_pass_renderer_preserves_disjoint_ranges_exactly(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source.txt';text=''.join(f'line {i}\n' for i in range(1,100));p.write_text(text)
            targets=[{'start_line':2,'end_line':3,'reason':'a'},{'start_line':80,'end_line':82,'reason':'b'}]
            self.assertEqual(r.render_slices_from_file(p,targets),r.render_slices(text,targets))

    def test_candidate_neighbors_keep_boundary_cleanup_and_merge(self):
        targets = [{'start_line':10,'end_line':20,'reason':'a'},
                   {'start_line':24,'end_line':28,'reason':'b'}]
        expanded = r.expand_candidate_context(targets, 29)
        self.assertEqual([(t['start_line'],t['end_line']) for t in expanded],[(8,29)])

    def test_default_and_compatibility_objectives_are_explicit(self):
        self.assertEqual(r.parse_args(['router.py','heavy_code','file']).optimize,'tokens')
        self.assertEqual(r.parse_args(['router.py','heavy_code','file','--optimize','latency']).optimize,'latency')

if __name__=='__main__':unittest.main()

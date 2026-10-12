"""Boundary counterexamples for the shared v2.5 emission contract."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('boundary_router',Path(__file__).resolve().parents[1]/'scripts/router.py')
r=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(r)

class BoundaryContracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'source.txt';self.path.write_text('alpha\nbeta')
    def run_cli(self, *flags):
        out,err=io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err),patch.object(r,'call_codex',side_effect=AssertionError('unexpected cloud')):
            code=r.main(['router','heavy_code',str(self.path),*flags])
        statuses=[json.loads(s.split('] ',1)[1]) for s in err.getvalue().splitlines() if s.startswith('[token-router status] ')]
        return code,out.getvalue(),statuses[-1] if statuses else None
    def test_output_budget_exact_rendered_boundary(self):
        code,out,_=self.run_cli('--policy-version','v2.5');self.assertEqual(code,0)
        with patch.object(r,'MAX_OUTPUT_CHARS',len(out)):
            self.assertEqual(self.run_cli('--policy-version','v2.5')[0],0)
        with patch.object(r,'MAX_OUTPUT_CHARS',len(out)-1):
            code,raw,status=self.run_cli('--policy-version','v2.5')
            self.assertEqual((code,raw),(2,''));self.assertTrue(status['final_output_capped'])
    def test_small_probe_exact_boundary(self):
        for length,expected in ((12,False),(13,True)):
            self.path.write_text('x'*length)
            original=r.ranked_candidates
            with patch.object(r,'AUTO_SMALL_CHARS',12),patch.object(r,'ranked_candidates',wraps=original) as scan:
                self.run_cli('--policy-version','v2.5')
                self.assertEqual(scan.called,expected)
    def test_literal_unicode_underscore_case_and_single_character(self):
        for literal,yes,no in [('한',' 한 ','대한 한글 _한'),('A','(A)','a AA A_'),('the',' the ','other'),('한_글',' 한_글 ','한_글자')]:
            pattern=r.required_pattern(literal)
            self.assertIsNotNone(pattern.search(yes));self.assertIsNone(pattern.search(no))
    def test_headers_do_not_supply_packet_evidence(self):
        checks=r.assess_packet_evidence(['needle'],('needle',),('needle',),('plain\n',),(),{})
        self.assertEqual(checks.packet_query_anchor,'missing')
        self.assertEqual(checks.semantic_sufficiency,'unknown')
    def test_explicit_modes_reject_auto_policy_options(self):
        for mode in (['--force-model'],['--deterministic'],['--optimize','latency']):
            for option in (['--policy-version','v2.4'],['--read-scope','focused'],['--require-term','A']):
                self.assertEqual(self.run_cli(*(mode+option))[0],2)
    def test_source_change_after_report_write_never_leaves_success_report(self):
        dest=self.path.with_name('report.json');original=r.os.replace
        def replace(src,target):
            original(src,target)
            if Path(target)==dest:self.path.write_text('ALPHA\nBETA')
        with patch.object(r.os,'replace',side_effect=replace):
            code,out,status=self.run_cli('--policy-version','v2.5','--report-json',str(dest))
        self.assertEqual((code,out),(1,''));self.assertIn('source_changed',status['reason_codes'])
        if dest.exists():
            report=json.loads(dest.read_text());self.assertEqual(report['status'],'error');self.assertEqual(report['output_chars'],0)
    def test_existing_report_survives_failed_replacement(self):
        dest=self.path.with_name('report.json');dest.write_text('previous report')
        with patch.object(r.os,'replace',side_effect=OSError('cannot replace')):
            code,out,_=self.run_cli('--policy-version','v2.5','--report-json',str(dest))
        self.assertEqual((code,out),(1,''));self.assertEqual(dest.read_text(),'previous report')
    def test_whole_cap_retains_absence_diagnostic(self):
        self.path.write_text('alpha\n'*100)
        with patch.object(r,'AUTO_SMALL_CHARS',0),patch.object(r,'MAX_OUTPUT_CHARS',30):
            code,out,status=self.run_cli('--policy-version','v2.5','--read-scope','whole','--require-term','missing')
        self.assertEqual((code,out),(2,''));self.assertEqual(status['absent_required'],['missing'])
    def test_required_occurrence_counts_are_not_witness_truncation(self):
        stats={}
        r.ranked_candidates(lambda:iter(['B B B\n']),'heavy_code',[],120000,diagnostics=stats,required_terms=['B'])
        self.assertEqual(stats['source_required']['B']['count'],3)
        self.assertFalse(stats['source_required']['B']['witnesses_truncated'])
    def test_packet_coordinate_contract_rejects_invented_lines(self):
        with self.assertRaises(ValueError):r.Packet((r.Span(1,2),),('one\n',),'rendered')
        with self.assertRaises(ValueError):r.Packet((r.Span(2,2),r.Span(1,1)),('two\n','one\n'),'rendered')
    def test_merged_model_reason_is_bounded_without_cutting_source(self):
        mapping={'targets':[{'start_line':1,'end_line':1,'reason':'a'*256},{'start_line':2,'end_line':2,'reason':'b'*256}]}
        out=io.StringIO()
        with patch.object(r,'call_codex',return_value=mapping),contextlib.redirect_stdout(out),contextlib.redirect_stderr(io.StringIO()):
            code=r.main(['router','heavy_code',str(self.path),'--force-model'])
        self.assertEqual(code,0)
        reason=out.getvalue().splitlines()[0].split(': ',1)[1]
        self.assertLessEqual(len(reason),256);self.assertIn('alpha\nbeta',out.getvalue())
    def test_append_and_truncate_guard(self):
        for change in ('append','truncate'):
            self.path.write_text('alpha\nbeta\n');guard=r.SourceGuard(self.path)
            with guard.open() as f:self.assertTrue(f.read())
            if change=='append':
                with self.path.open('a') as f:f.write('tail\n')
            else:self.path.write_text('a')
            with self.assertRaises(r.SourceChanged):guard.check()

if __name__=='__main__':unittest.main()

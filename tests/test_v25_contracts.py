"""No-cloud end-to-end invariants for the v2.5 evidence and emission contract."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('contracts_router',Path(__file__).resolve().parents[1]/'scripts/router.py')
r=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(r)

class V25Contracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'source.txt';self.path.write_text('alpha\nbeta\n')

    def run_cli(self,flags=(),model=None):
        flags=list(flags)
        if not any(x in flags for x in ("--force-model","--deterministic","--optimize","--policy-version")):
            flags=["--policy-version","v2.5",*flags]
        out,err=io.StringIO(),io.StringIO()
        with patch.object(r,'call_codex',side_effect=model or AssertionError('cloud forbidden')),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            code=r.main(['router.py','heavy_code',str(self.path),*flags])
        statuses=[json.loads(line.split('] ',1)[1]) for line in err.getvalue().splitlines() if line.startswith('[token-router status] ')]
        self.assertTrue(statuses,err.getvalue())
        return code,out.getvalue(),statuses[-1]

    def test_require_literal_validation_case_boundary_and_dedup(self):
        args=r.parse_args(['router.py','heavy_code','x','--policy-version','v2.5','--require-term','Foo.bar','--require-term','Foo.bar'])
        self.assertEqual(args.require_term,['Foo.bar'])
        p=r.required_pattern('Foo.bar')
        self.assertTrue(p.search('call Foo.bar()'))
        self.assertFalse(p.search('foo.bar xFoo.bar Foo.bar_more'))
        for term in ('','two words','x\ny'):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                r.parse_args(['router.py','heavy_code','x','--policy-version','v2.5','--require-term',term])

    def test_model_target_rejects_mixed_invalid_types_and_hidden_gaps(self):
        valid={'start_line':1,'end_line':1,'reason':'okay'}
        for invalid in [dict(valid,start_line=True),dict(valid,end_line='1'),dict(valid,start_line=0),dict(valid,start_line=2,end_line=1),dict(valid,end_line=3),dict(valid,reason=42),dict(valid,extra=1)]:
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                r.validate_model_targets({'targets':[valid,invalid]},3,[1,3])
        clean=r.validate_model_targets({'targets':[dict(valid,reason='x'*1000)]},3,[1])
        self.assertEqual(len(clean['targets'][0]['reason']),256)

    def test_every_output_path_obeys_final_character_budget(self):
        self.path.write_text('alpha '+('z'*100)+'\n')
        valid=lambda prompt:{'targets':[{'start_line':1,'end_line':1,'reason':'selected'}]}
        for flags,model in [((),None),(('--deterministic',),None),(('--optimize','latency'),None),(('--force-model',),valid),(('--force-model',),lambda prompt:{'targets':[]})]:
            with self.subTest(flags=flags,model=model),patch.object(r,'MAX_OUTPUT_CHARS',30):
                code,out,status=self.run_cli(flags,model)
                self.assertEqual(code,2);self.assertEqual(out,'')
                self.assertTrue(status['final_output_capped'])
                self.assertFalse(status['full_source_returned'])

    def test_source_mutation_before_finalization_emits_no_raw(self):
        original=r.SourceGuard.probe
        def mutate(guard,limit):
            text=original(guard,limit)
            self.path.write_text('ALPHA\nBETA\n')
            return text
        with patch.object(r.SourceGuard,'probe',mutate):
            code,out,status=self.run_cli()
        self.assertEqual(code,1);self.assertEqual(out,'')
        self.assertIn('source_changed',status['reason_codes'])

    def test_sidecar_aliases_and_write_failure_do_not_emit_or_destroy_source(self):
        original=self.path.read_bytes()
        link=self.path.with_name('link');link.symlink_to(self.path)
        hard=self.path.with_name('hard');os.link(self.path,hard)
        for dest in (self.path,link,hard,self.path.parent/'missing'/'report.json'):
            with self.subTest(dest=dest):
                code,out,status=self.run_cli(['--report-json',str(dest)])
                self.assertEqual(code,1);self.assertEqual(out,'')
                self.assertEqual(self.path.read_bytes(),original)

    def test_report_has_final_status_without_raw_source(self):
        dest=self.path.with_name('report.json')
        code,out,status=self.run_cli(['--report-json',str(dest)])
        self.assertEqual(code,0)
        report=json.loads(dest.read_text())
        self.assertEqual(report['output_chars'],len(out))
        self.assertEqual(report['status'],status['status'])
        self.assertNotIn('alpha\nbeta',dest.read_text())

    def test_final_packet_anchor_can_be_present_without_core_anchor(self):
        evidence=r.assess_packet_evidence(['cleanup'],(),('cleanup',),('cleanup()\n',),(),{})
        self.assertEqual(evidence.packet_query_anchor,'satisfied')
        self.assertEqual(evidence.core_terms,())

    def test_required_absent_lost_and_full_source_are_distinct(self):
        evidence=r.assess_packet_evidence([],(),(),('other\n',),('absent','lost'),{'absent':{'count':0},'lost':{'count':1}})
        self.assertEqual(evidence.absent_required,('absent',));self.assertEqual(evidence.lost_required,('lost',))
        code,out,status=self.run_cli(['--require-term','absent'])
        self.assertEqual(code,0);self.assertTrue(status['full_source_returned'])
        self.assertEqual(status['absent_required'],['absent']);self.assertEqual(status['lost_required'],[])

    def test_required_present_but_unadmitted_abstains_with_witness(self):
        self.path.write_text('important_symbol '+('x'*125000)+'\n'+('neutral payload\n'*8000))
        code,out,status=self.run_cli(['--require-term','important_symbol'])
        self.assertEqual(code,2);self.assertEqual(out,'')
        self.assertEqual(status['lost_required'],['important_symbol'])
        self.assertEqual(status['absent_required'],[])
        self.assertTrue(status['suggested_ranges'])
        self.assertFalse(status['model_called'])

if __name__=='__main__':unittest.main()

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('literal_router',Path(__file__).resolve().parents[1]/'scripts/router.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class LiteralSearchTests(unittest.TestCase):
    def run_cli(self,text,options):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.py';path.write_text(text,encoding='utf-8')
            out,err=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                code=r.main(['router.py','heavy_code',str(path),*options])
            status=json.loads(next(x.split('] ',1)[1] for x in err.getvalue().splitlines() if x.startswith('[token-router status]')))
            self.assertEqual(path.read_text(),text)
            return code,out.getvalue(),status
    def test_disjoint_numbered_windows_preserve_only_original_source(self):
        lines=[f'padding_{n}\n' for n in range(2000)]
        lines[100]='needle A\n';lines[1800]='needle B\n';text=''.join(lines)
        with patch.object(r,'ranked_candidates',side_effect=AssertionError('ranking forbidden')),patch.object(r,'call_codex',side_effect=AssertionError('model forbidden')):
            code,out,status=self.run_cli(text,['--search-term','needle A','--search-term','needle B','--line-numbers'])
        self.assertEqual(code,0);self.assertEqual(status['search_match_lines'],{'needle A':1,'needle B':1})
        self.assertIn('101: needle A',out);self.assertIn('1801: needle B',out);self.assertNotIn('padding_800',out)
        self.assertEqual(status['output_lines'],50);self.assertEqual(status['output_format'],'numbered')
    def test_broad_search_abstains_before_collecting_source(self):
        with patch.object(r,'packet_from_guard',side_effect=AssertionError('unneeded collection')):
            code,out,status=self.run_cli('match abcdefghijklmnopqrstuvwxyz\n'*3000,['--search-term','match'])
        self.assertEqual((code,out),(2,''));self.assertTrue(status['final_output_capped'])
    def test_case_sensitive_unicode_and_missing_term(self):
        code,out,status=self.run_cli('δ_value\nAlpha\n',['--search-term','δ_','--search-term','alpha','--line-numbers'])
        self.assertEqual(code,0);self.assertEqual(status['missing_search_terms'],['alpha']);self.assertIn('1: δ_value',out)
    def test_no_match_never_returns_irrelevant_source(self):
        code,out,status=self.run_cli('unrelated\n',['--search-term','needle'])
        self.assertEqual((code,out),(2,''));self.assertEqual(status['reason_codes'],['literal_not_found'])
    def test_cli_incompatible_combinations_and_invalid_terms(self):
        for options in [['--force-model'],['--deterministic'],['--optimize','latency'],['--return-context','bounded'],['--return-target','f'],['--policy-version','v2.5','--read-scope','whole'],['--search-term','\n']]:
            code,out,status=self.run_cli('needle\n',['--search-term','needle',*options])
            self.assertEqual((code,out),(2,''));self.assertEqual(status['status'],'usage_error')
    def test_numbered_final_cap_counts_headers(self):
        with patch.object(r,'MAX_OUTPUT_CHARS',5):
            code,out,status=self.run_cli('needle\n',['--search-term','needle','--line-numbers'])
        self.assertEqual((code,out),(2,''));self.assertTrue(status['final_output_capped'])
    def test_numbered_render_preserves_raw_slices_and_last_line(self):
        packet=r.Packet((r.Span(7,8),),('abc\nlast',),'unused')
        out=r.numbered_packet(packet)
        self.assertEqual(out.raw_slices,packet.raw_slices);self.assertEqual(out.ranges,packet.ranges)
        self.assertIn('7: abc\n8: last\n',out.rendered)
    def test_mutation_still_withholds_search_output(self):
        check=r.SourceGuard.check
        def changed(guard):
            check(guard)
            if guard.open_count>=2:raise r.SourceChanged('injected mutation')
        with patch.object(r.SourceGuard,'check',changed):
            code,out,status=self.run_cli('needle\n',['--search-term','needle','--line-numbers'])
        self.assertEqual((code,out),(1,''));self.assertEqual(status['source_consistency'],'changed')

class SelectedTracebackTests(unittest.TestCase):
    def test_selected_timestamped_traceback_completes_without_unrelated_block(self):
        lines=['padding\n']*300
        lines[100]='2026-10-12T01:00:00Z \x1b[31mERROR\x1b[0m: worker\n'
        lines[103]='2026-10-12T01:00:00Z Traceback (most recent call last):\n'
        for i in range(104,130):lines[i]='2026-10-12T01:00:00Z   File x, line 2\n'
        lines[130]='2026-10-12T01:00:00Z \x1b[31mValueError\x1b[0m: failed\n'
        lines[200]='Traceback (most recent call last):\n';lines[201]='RuntimeError: unrelated\n'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'incident.log';path.write_text(''.join(lines))
            out,err=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                code=r.main(['router.py','error_log',str(path),'--search-term','ERROR: worker','--line-numbers'])
            self.assertEqual(code,0);self.assertIn('131: ',out.getvalue());self.assertNotIn('unrelated',out.getvalue())
            status=json.loads(err.getvalue().split('] ',1)[1]);self.assertEqual(status['traceback_completed_blocks'],1)
    def test_long_traceback_does_not_expand_without_a_bounded_terminator(self):
        lines=['padding\n']*300;lines[20]='ERROR: selected\n';lines[23]='Traceback (most recent call last):\n';lines[110]='ValueError: outside bound\n'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'incident.log';path.write_text(''.join(lines))
            out,err=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                code=r.main(['router.py','error_log',str(path),'--search-term','ERROR: selected','--line-numbers'])
            self.assertEqual(code,0);self.assertNotIn('outside bound',out.getvalue())

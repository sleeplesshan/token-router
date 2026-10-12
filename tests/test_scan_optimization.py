import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('scan_router',Path(__file__).resolve().parents[1]/'scripts/router.py')
r=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(r)

class ScanOptimizationTests(unittest.TestCase):
    def test_small_probe_preserves_newline_semantics_and_skips_ranking(self):
        for raw in [b'a\r\nb\r\nc', 'a\u2028b\nc'.encode(), b'a\xff\nb\n']:
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'small.py';p.write_bytes(raw)
                out,err=io.StringIO(),io.StringIO()
                with patch.object(r,'ranked_candidates',side_effect=AssertionError('must bypass')),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                    code=r.main(['router','heavy_code',str(p),'--policy-version','v2.5'])
                text=p.read_text(errors='replace');lines=list(io.StringIO(text,newline=''))
                expected=r.render_slices(text,[dict(start_line=1,end_line=len(lines),reason='automatic full-source bypass; no model call; raw source preserved')])
                # render_slices uses splitlines, so assert the actual source text independently.
                self.assertEqual(code,0);self.assertIn(text,out.getvalue())
                self.assertIn(f'TO {len(lines)}]',out.getvalue())
                self.assertIn('"open_count": 1',err.getvalue())

    def test_scan_collects_counts_without_additional_pass(self):
        opened=[];lines=['first needle\n','plain\n','last\n'];stats={}
        def source():
            opened.append(1);yield from lines
        _,_,_,_,visible=r.ranked_candidates(source,'heavy_code',['needle'],120000,diagnostics=stats)
        self.assertEqual(len(opened),2)
        self.assertEqual(stats['source_chars'],sum(map(len,lines)))
        self.assertEqual(stats['candidate_raw_chars'],sum(len(lines[n-1]) for n in visible))

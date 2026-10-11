"""Behavioral regressions from distributed-evidence and noisy-query failures."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('evidence_router', Path(__file__).resolve().parents[1]/'scripts/router.py')
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)


class EvidenceSelectionTests(unittest.TestCase):
    def test_context_padding_retains_core_and_file_line_header(self):
        targets=[{'start_line':20,'end_line':21,'reason':'raise expression'}]
        padded=r.add_output_context(targets,100)
        self.assertEqual((padded[0]['start_line'],padded[0]['end_line']),(18,23))
        with patch.object(r,'MAX_OUTPUT_LINES',3):
            padded=r.add_output_context(targets,100)
        visible={n for t in padded for n in range(t['start_line'],t['end_line']+1)}
        self.assertTrue({20,21} <= visible)
        self.assertEqual(len(visible),3)

    def test_context_padding_merges_overlap_and_respects_file_edges(self):
        targets=[{'start_line':1,'end_line':2,'reason':'a'}, {'start_line':4,'end_line':5,'reason':'b'}]
        result=r.add_output_context(targets,5)
        self.assertEqual(len(result),1)
        self.assertEqual((result[0]['start_line'],result[0]['end_line']),(1,5))

    def test_question_words_do_not_select_unrelated_source(self):
        terms = r.normalize_query_terms('What is the exact alpha_lookup function and where does it fail?')
        self.assertTrue(r.query_matches('def alpha_lookup(value):', terms))
        self.assertFalse(r.query_matches('within another generic statement', terms))
        self.assertFalse(r.query_matches('this line is unrelated', terms))

    def test_query_preserves_korean_and_identifier_components(self):
        terms = r.normalize_query_terms('토큰 만료 session_token')
        self.assertTrue(r.query_matches('토큰 만료 처리', terms))
        self.assertTrue(r.query_matches('session_token = refresh()', terms))
        self.assertFalse(r.query_matches('tokenizer session_tokenizer', terms))
        self.assertTrue(r.query_matches('session_token_expires_at', ['token']))

    def test_named_first_traceback_keeps_distant_assertion_and_footer(self):
        lines = ['ordinary progress\n']*200
        lines += ['_____ TestWidget.test_conversion[1] _____\n']
        lines += ['    intermediate local value\n']*20
        lines += ['> assert convert(value) == expected\n', 'E ValueError: conversion failed\n']
        lines += ['    remaining diagnostic context\n']*15
        lines += ['tests/test_widget.py:77: ValueError\n']
        lines += ['_____ TestWidget.test_conversion[2] _____\n']
        lines += ['ValueError: repeated conversion failed\n']*300
        with patch.object(r, 'MAX_PROMPT_CHARS', 12000):
            prompt=r.build_prompt(''.join(lines), 'error_log', 'first TestWidget.test_conversion')
        content=prompt.split('[Line-numbered content]:\n',1)[1]
        self.assertIn('> assert convert(value) == expected',content)
        self.assertIn('tests/test_widget.py:77: ValueError',content)
        self.assertLessEqual(len(content),12000)

    def test_budget_preserves_distributed_log_evidence(self):
        lines = ['ordinary progress ' + 'x'*100 + '\n']*1800
        lines[12] = 'runtime_marker: engine version 7\n'
        lines[820] = 'Traceback: unique_marker processing failed\n'
        lines[-3] = 'FATAL: shutdown_marker terminated\n'
        with patch.object(r, 'MAX_PROMPT_CHARS', 6000):
            prompt = r.build_prompt(''.join(lines), 'error_log', 'runtime_marker unique_marker shutdown_marker')
        for marker in ('runtime_marker: engine version 7', 'unique_marker processing failed', 'shutdown_marker terminated'):
            self.assertIn(marker, prompt.split('[Line-numbered content]:\n', 1)[1])
        self.assertLessEqual(len(prompt.split('[Line-numbered content]:\n',1)[1]), 6000)

    def test_streaming_and_inmemory_both_keep_late_error_under_cap(self):
        content = ('error: repeated build probe\n'*1000 + 'FATAL: final_unique_shutdown\n')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'job.log'; path.write_text(content)
            rendered, truncated, count, total = r.streaming_log_candidate_content(path, 2500, [])
        self.assertIn('final_unique_shutdown', rendered)
        self.assertLessEqual(len(rendered), 2500)
        self.assertTrue(truncated)
        self.assertEqual(total, 1001)
        with patch.object(r,'MAX_PROMPT_CHARS',2500):
            prompt=r.build_prompt(content,'error_log')
        self.assertIn('final_unique_shutdown',prompt)

    def test_output_cap_does_not_drop_every_early_target(self):
        mapping={'targets':[{'start_line':a,'end_line':a+19,'reason':'evidence'} for a in (10,100,1000)]}
        with patch.object(r,'MAX_OUTPUT_LINES',9):
            targets=r.normalize_targets(mapping,1100,'error_log')
        self.assertLessEqual(sum(t['end_line']-t['start_line']+1 for t in targets),9)
        for a in (10,100,1000):
            self.assertTrue(any(t['start_line']<=a+19 and t['end_line']>=a for t in targets))

    def test_deterministic_cli_does_not_launch_model_and_preserves_raw(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.py'
            content='unrelated\n'*40+'def exact_symbol():\n    return 42\n'+'unrelated\n'*40
            path.write_text(content)
            out=io.StringIO()
            with patch.object(r,'call_codex',side_effect=AssertionError('model must not be called')), contextlib.redirect_stdout(out):
                status=r.main(['router.py','heavy_code',str(path),'--query','exact_symbol','--deterministic'])
        self.assertEqual(status,0)
        self.assertIn('def exact_symbol():\n    return 42\n',out.getvalue())
        self.assertIn('RAW CONTENT FROM LINE',out.getvalue())

    def test_empty_cloud_selection_returns_late_raw_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'job.log'
            path.write_text('ordinary progress\n'*400+'Traceback: late_specific_failure\n')
            out,err=io.StringIO(),io.StringIO()
            with patch.object(r,'call_codex',return_value={'targets':[]}), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status=r.main(['router.py','error_log',str(path),'--query','late_specific_failure'])
        self.assertIn('late_specific_failure',out.getvalue())
        self.assertIn('RAW CONTENT FROM LINE',out.getvalue())
        self.assertIn('fallback',(out.getvalue()+err.getvalue()).lower())


if __name__=='__main__': unittest.main()

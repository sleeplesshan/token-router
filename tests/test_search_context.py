"""Explicit context width must preserve evidence and shared safety contracts."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_literal_search import r


class SearchContextTests(unittest.TestCase):
    def run_cli(self, text, options, mode='heavy_code'):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'source.txt'
            path.write_text(text, encoding='utf-8')
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = r.main(['router.py', mode, str(path), *options])
            status = json.loads(next(line.split('] ', 1)[1] for line in err.getvalue().splitlines()
                                     if line.startswith('[token-router status]')))
            return code, out.getvalue(), status

    def test_explicit_widths_and_default_compatibility(self):
        lines = [f'padding_{n}\n' for n in range(300)]
        lines[100] = 'needle δ\n'
        text = ''.join(lines)
        opts = ['--search-term', 'needle', '--line-numbers']
        default = self.run_cli(text, opts)
        for width in (0, 1, 12):
            code, out, status = self.run_cli(text, opts + ['--search-context', str(width)])
            self.assertEqual(code, 0)
            self.assertEqual(status['output_lines'], 2 * width + 1)
            self.assertEqual(status['context_lines'], width)
            self.assertIn('101: needle δ\n', out)
            self.assertFalse(status['model_called'])
            if width == 12:
                self.assertEqual(out, default[1])
        for mode, width in [('heavy_code', 12), ('agent_context', 12), ('error_log', 4)]:
            self.assertEqual(self.run_cli(text, opts, mode)[1],
                             self.run_cli(text, opts + ['--search-context', str(width)], mode)[1])

    def test_zero_keeps_all_hits_without_neighbors_and_final_newline(self):
        code, out, status = self.run_cli('needle\nneighbor\nneedle',
            ['--search-term', 'needle', '--search-term', 'absent', '--search-context', '0', '--line-numbers'])
        self.assertEqual(code, 0)
        self.assertEqual(status['output_lines'], 2)
        self.assertEqual(status['search_match_lines']['needle'], 2)
        self.assertEqual(status['missing_search_terms'], ['absent'])
        self.assertNotIn('neighbor', out)
        self.assertIn('3: needle', out)

    def test_invalid_width_and_non_literal_modes_are_usage_errors(self):
        for options in [['--search-term', 'needle', '--search-context', n] for n in ('-1', '13', '1.5', 'true')] + [
                ['--query', 'needle', '--search-context', '1'],
                ['--deterministic', '--search-context', '1']]:
            code, out, status = self.run_cli('needle\n', options)
            self.assertEqual((code, out), (2, ''))
            self.assertEqual(status['status'], 'usage_error')

    def test_zero_still_completes_selected_traceback_not_adjacent_one(self):
        text = ('ERROR: preceding\nTraceback (most recent call last):\n'
                '  File "x.py", line 2, in worker\nValueError: selected\n'
                'gap\nTraceback (most recent call last):\nRuntimeError: unrelated\n')
        for term in ['Traceback (most recent call last):', 'in worker']:
            code, out, status = self.run_cli(text,
                ['--search-term', term, '--search-context', '0', '--line-numbers'], 'error_log')
            self.assertEqual(code, 0)
            self.assertIn('4: ValueError: selected', out)
            self.assertNotIn('ERROR: preceding', out)
            if term == 'in worker':
                self.assertNotIn('unrelated', out)
                self.assertEqual(status['traceback_completed_blocks'], 1)
        code, out, status = self.run_cli(text,
            ['--search-term', 'ERROR: preceding', '--search-context', '0'], 'error_log')
        self.assertEqual(code, 0)
        self.assertNotIn('ValueError', out)
        self.assertEqual(status['traceback_completed_blocks'], 0)

    def test_zero_does_not_bypass_cap_or_source_change(self):
        options = ['--search-term', 'needle', '--search-context', '0']
        with patch.object(r, 'MAX_OUTPUT_CHARS', 10):
            code, out, status = self.run_cli('needle' + 'x' * 10000, options)
            self.assertEqual((code, out), (2, ''))
            self.assertTrue(status['final_output_capped'])
        check = r.SourceGuard.check
        def changed(guard):
            check(guard)
            if guard.open_count >= 2:
                raise r.SourceChanged('injected change')
        with patch.object(r.SourceGuard, 'check', changed):
            code, out, status = self.run_cli('needle\n', options)
            self.assertEqual((code, out), (1, ''))
            self.assertEqual(status['source_consistency'], 'changed')

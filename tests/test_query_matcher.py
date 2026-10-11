"""Differential tests against the router's documented matching semantics."""
import importlib.util
from pathlib import Path
import random
import re
import unittest

SPEC = importlib.util.spec_from_file_location('query_matcher', Path(__file__).resolve().parents[1] / 'scripts/query_matcher.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def reference(terms, line):
    return tuple(i for i, term in enumerate(terms)
                 if re.search(r'(?<![^\W_])' + re.escape(term) + r'(?![^\W_])', line, re.I))


class QueryMatcherTests(unittest.TestCase):
    def test_overlapping_complex_duplicates_and_boundaries(self):
        terms = ['foo', 'foo.bar', 'bar', 'foo_bar', 'FOO', '', 'a/b', '.x', '123']
        match = m.compile_matcher(terms)
        for line in ['foo.bar foo_bar a/b .x 123', 'foobar xfoo 1234', '_foo_ BAR', '', 'foo.bar.baz']:
            self.assertEqual(match(line), reference(terms, line))

    def test_unicode_ignorecase_and_word_boundaries(self):
        terms = ['i', 's', 'k', 'I', '토큰', '만료', 'é', 'foo', 'ß', 'İ', 'ſ']
        match = m.compile_matcher(terms)
        for line in ['İ ı ſ K', 'i S K', '토큰_만료', '토큰만료', 'éfoo fooé', 'ＦＯＯ', 'ß ss', 'foo\u0301']:
            self.assertEqual(match(line), reference(terms, line))

    def test_randomized_differential(self):
        rng = random.Random(90210)
        alphabet = 'abZ019_./:- ()' + '한éİıſKß\u0301'
        for _ in range(200):
            terms = [''.join(rng.choices(alphabet, k=rng.randrange(0, 7))) for _ in range(15)]
            match = m.compile_matcher(terms)
            for _ in range(5):
                line = ''.join(rng.choices(alphabet, k=rng.randrange(0, 120)))
                self.assertEqual(match(line), reference(terms, line))

    def test_ascii_index_differential(self):
        rng = random.Random(13)
        terms = ['alpha', 'beta', 'x1', '1', 'a.b', 'beta_alpha', 'ALPHA']
        match = m.compile_matcher(iter(terms))
        for _ in range(500):
            line = ' '.join(rng.choices(['alpha', 'ALPHA', 'beta', 'x1', '_alpha_', 'alphabeta', 'a.b', 'beta_alpha', '12'], k=20))
            self.assertEqual(match(line), reference(terms, line))

    def test_empty_terms(self):
        self.assertEqual(m.compile_matcher([])('anything 한글'), ())


if __name__ == '__main__':
    unittest.main()

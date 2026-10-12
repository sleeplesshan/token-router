"""Regression: selected accessor header, long docstring, omitted sole return.

Motivated by pinned Click core.py:get_parameter_source (header970,return986),
recorded in the separate v2.5.1 cause audit. Fixtures do not encode gold hints.
"""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from evidence_checks import complete_python_statements, bounded_return_supplement
from router import packet_from_guard


def completed_with_supplement(text, targets):
    spans=[]
    base,checks=complete_python_statements(text,targets,return_spans=spans)
    render=lambda ranges:packet_from_guard(None,ranges,text)
    result,_,_=bounded_return_supplement(text,base,render(base),spans,render,lambda packet:True)
    return result,checks


def fixture(body='    return self._parameter_source.get(name)\n',doc_lines=15):
    return 'def get_parameter_source(self, name):\n    """Lookup metadata.\n'+('    Documentation, not executable source.\n'*(doc_lines-2))+'    """\n'+body


def selected(targets):
    return {n for t in targets for n in range(t['start_line'],t['end_line']+1)}


class DocstringReturnTests(unittest.TestCase):
    def test_long_docstring_does_not_hide_sole_return(self):
        text=fixture();line=len(text.splitlines())
        result,checks=completed_with_supplement(text,[dict(start_line=1,end_line=10,reason='selected')])
        self.assertIn(line,selected(result))
        self.assertFalse(set(range(11,line)) & selected(result))
        self.assertEqual(checks['semantic_sufficiency'],'unknown')
    def test_multiline_return_and_async_variant(self):
        for prefix in ('','async '):
            text=prefix+fixture('    return (\n        value\n    )\n')
            result,_=completed_with_supplement(text,[dict(start_line=1,end_line=1,reason='header')])
            self.assertTrue(set(range(17,20))<=selected(result))
    def test_non_accessor_and_unselected_header_are_not_bridged(self):
        for body in ('    x = source\n    return x\n','    raise ValueError()\n','    return (\n'+('        item,\n'*12)+'    )\n'):
            text=fixture(body);result,_=complete_python_statements(text,[dict(start_line=1,end_line=1,reason='header')])
            self.assertEqual(selected(result),{1})
        result,_=complete_python_statements(fixture(),[dict(start_line=3,end_line=3,reason='doc only')])
        self.assertNotIn(17,selected(result))
    def test_global_added_budget_and_zero_budget(self):
        text=fixture()+'\n'+fixture().replace('get_parameter_source','other_accessor')
        result,_=complete_python_statements(text,[dict(start_line=1,end_line=1,reason='first'),dict(start_line=19,end_line=19,reason='second')],max_added=1)
        self.assertLessEqual(len(selected(result)),3)
        result,_=complete_python_statements(fixture(),[dict(start_line=1,end_line=1,reason='header')],max_added=0)
        self.assertEqual(selected(result),{1})
    def test_invalid_syntax_and_no_docstring_are_unchanged(self):
        targets=[dict(start_line=1,end_line=1,reason='header')]
        result,_=complete_python_statements('def broken(:\n',targets)
        self.assertEqual(result,targets)
        # Long decorator/signature alternatives must not invent docstring returns.
        text='def plain():\n'+('    # comment\n'*20)+'    return value\n'
        result,_=complete_python_statements(text,targets)
        self.assertEqual(selected(result),{1})

if __name__=='__main__':unittest.main()

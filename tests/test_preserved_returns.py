"""Preserved-baseline, atomic short-return supplementation contracts."""
import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evidence_checks as e
from routing_policy import Packet,Span


def renderer(text):
    lines=text.splitlines(keepends=True)
    def render(targets):
        ranges=tuple(Span(t['start_line'],t['end_line']) for t in targets)
        raw=tuple(''.join(lines[s.start-1:s.end]) for s in ranges)
        return Packet(ranges,raw,''.join(f'[{s.start}:{s.end}]\n'+r for s,r in zip(ranges,raw)))
    return render


def target(a,b=None):return {'start_line':a,'end_line':a if b is None else b,'reason':'base'}
def line_set(packet):return {n for s in packet.ranges for n in range(s.start,s.end+1)}
def line_text(packet):
    return {n:line for span,raw in zip(packet.ranges,packet.raw_slices) for n,line in enumerate(raw.splitlines(keepends=True),span.start)}


class PreservedReturnTests(unittest.TestCase):
    def supplement(self,text,targets,spans,accept=lambda p:True,**kw):
        render=renderer(text);base=render(targets)
        output,packet,report=e.bounded_return_supplement(text,targets,base,spans,render,accept,**kw)
        self.assertTrue(line_set(base)<=line_set(packet))
        for n,value in line_text(base).items():self.assertEqual(line_text(packet)[n],value)
        return targets,base,output,packet,report

    def test_collects_unicode_async_using_single_parse_and_preserves_baseline(self):
        text='async def 조회():\n    """\n'+'    docs\n'*20+'    """\n    return result\n'
        baseline,_=e.complete_python_statements(text,[target(1)],max_added=0)
        spans=[]
        with patch.object(e.ast,'parse',wraps=ast.parse) as parse:
            result,_=e.complete_python_statements(text,[target(1)],max_added=0,return_spans=spans)
        self.assertEqual(parse.call_count,1)
        self.assertEqual(result,baseline)
        self.assertEqual(spans,[(24,24)])

    def test_collector_requires_original_header_and_sole_return(self):
        text='def outer():\n    """docs"""\n    x = 1\n    return x\n\ndef getter():\n    """docs"""\n    return x\n'
        spans=[];e.complete_python_statements(text,[target(1),target(7)],return_spans=spans)
        self.assertEqual(spans,[])

    def test_generic_budget_zero_boundary_sufficient_is_unchanged(self):
        text='value = call(\n    first,\n    second,\n)\n'
        for budget in (0,2,3,128):
            with self.subTest(budget=budget):
                old,_=e.complete_python_statements(text,[target(2)],max_added=budget)
                spans=[];new,_=e.complete_python_statements(text,[target(2)],max_added=budget,return_spans=spans)
                self.assertEqual(new,old);self.assertEqual(spans,[])

    def test_multiline_return_added_whole_and_sorted(self):
        text='header\ngap\nreturn (\n    value\n)\ntail\n'
        _,base,_,packet,_=self.supplement(text,[target(1)],[(3,5)])
        self.assertEqual(line_set(packet)-line_set(base),{3,4,5})

    def test_multiline_does_not_fit_remaining_lines_is_not_partial(self):
        text='header\ngap\nreturn (\n    value\n)\n'
        targets,base,output,packet,_=self.supplement(text,[target(1)],[(3,5)],max_lines=2)
        self.assertIs(output,targets);self.assertIs(packet,base)

    def test_raw_character_budget_skips_entire_long_return(self):
        text='header\nreturn '+('x'*1100)+'\n'
        targets,base,output,packet,_=self.supplement(text,[target(1)],[(2,2)])
        self.assertIs(output,targets);self.assertIs(packet,base)

    def test_already_present_and_empty_candidates_return_exact_objects(self):
        for spans in ([],[(1,1)]):
            targets,base,output,packet,_=self.supplement('return x\n',[target(1)],spans)
            self.assertIs(output,targets);self.assertIs(packet,base)

    def test_competing_returns_deterministic_and_total_budget(self):
        text=''.join(f'line {i}\n' for i in range(1,30))
        _,base,_,packet,_=self.supplement(text,[target(1)],[(20,20),(4,5),(10,11),(4,5)],max_lines=3)
        added=line_set(packet)-line_set(base)
        self.assertLessEqual(len(added),3)
        self.assertEqual(added,{4,5,20})
        self.assertLessEqual(sum(len(line_text(packet)[n]) for n in added),1024)
        self.assertLessEqual(len(packet.rendered)-len(base.rendered),1024)

    def test_final_render_budget_rolls_back_all_additions(self):
        targets,base,output,packet,_=self.supplement('head\nreturn x\n',[target(1)],[(2,2)],max_rendered_chars=1)
        self.assertIs(output,targets);self.assertIs(packet,base)

    def test_policy_rejection_rolls_back_all_additions(self):
        targets,base,output,packet,_=self.supplement('head\nreturn x\n',[target(1)],[(2,2)],accept=lambda p:False)
        self.assertIs(output,targets);self.assertIs(packet,base)

    def test_supplement_does_not_parse_or_chain_expand(self):
        with patch.object(e.ast,'parse',side_effect=AssertionError('no second AST parse')):
            _,_,_,packet,_=self.supplement('head\nreturn x\nother context\n',[target(1)],[(2,2)])
        self.assertEqual(line_set(packet),{1,2})

    def test_parse_failure_collects_nothing(self):
        spans=[];targets=[target(1)]
        result,info=e.complete_python_statements('def broken(',targets,return_spans=spans)
        self.assertEqual(spans,[]);self.assertEqual(result,targets)
        self.assertEqual(info['syntax'],'unknown')

if __name__=='__main__':unittest.main()

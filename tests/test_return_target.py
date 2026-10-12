import ast
import unittest
from unittest.mock import patch
from test_preserved_returns import renderer,target,line_set,line_text
import evidence_checks as e

class ReturnTargetTests(unittest.TestCase):
    def definitions(self,text,selected):
        defs=[];spans=[]
        with patch.object(e.ast,'parse',wraps=ast.parse) as parse:
            e.complete_python_statements(text,selected,max_added=0,return_spans=spans,return_definitions=defs)
        self.assertEqual(parse.call_count,1)
        return defs
    def test_entire_file_duplicates_even_unselected_or_ineligible(self):
        text='class A:\n def get(self):\n  """doc"""\n  return 1\nclass B:\n def get(self):\n  x=2\n  return x\n'
        defs=self.definitions(text,[target(2)])
        self.assertEqual(len([d for d in defs if d['name']=='get']),2)
        self.assertEqual([d['qualname'] for d in defs if d['name']=='get'],['A.get','B.get'])
    def test_nested_async_unicode_conditional_and_property_duplicates(self):
        text='def outer():\n async def 조회():\n  """doc"""\n  return 1\nif condition:\n def same():\n  pass\nelse:\n def same():\n  pass\nclass P:\n @property\n def value(self):\n  """doc"""\n  return 1\n @value.setter\n def value(self,v):\n  self.v=v\n'
        defs=self.definitions(text,[target(2),target(13)])
        self.assertIn('outer.조회',[d['qualname'] for d in defs]);self.assertEqual(sum(d['qualname']=='P.value' for d in defs),2)
        self.assertEqual(sum(d['name']=='same' for d in defs),2)
    def setup_packets(self,base_lines=(1,),m_lines=(1,3,5)):
        text='base\ngap\nreturn first\ngap\nreturn second\n'
        render=renderer(text);b=[target(n) for n in base_lines];m=[target(n) for n in m_lines]
        defs=[dict(name='first',qualname='A.first',eligible=True,span=(3,3)),dict(name='second',qualname='B.second',eligible=True,span=(5,5))]
        return b,render(b),m,render(m),defs,render
    def apply(self,name,b,base,m,mp,defs,render,approved=((3,3),(5,5)),accept=lambda p:True):
        out,packet,info=e.limit_return_target(name,defs,b,base,m,mp,approved,render,accept)
        self.assertTrue(line_set(base)<=line_set(packet)<=line_set(mp))
        for n,v in line_text(packet).items():self.assertEqual(line_text(mp)[n],v)
        return out,packet,info
    def test_preserve_target_supplement_no_refill(self):
        b,base,m,mp,defs,render=self.setup_packets()
        _,p,info=self.apply('A.first',b,base,m,mp,defs,render)
        self.assertEqual(line_set(p),{1,3});self.assertTrue(info['applied'])
    def test_target_already_in_base(self):
        b,base,m,mp,defs,render=self.setup_packets(base_lines=(1,3))
        _,p,info=self.apply('first',b,base,m,mp,defs,render)
        self.assertIs(p,base);self.assertTrue(info['applied'])
    def test_unresolved_casefold_partial_ambiguous_and_ineligible_keep_m(self):
        b,base,m,mp,defs,render=self.setup_packets()
        for name in ['FIRST','fir','not_there']:
            self.assertIs(self.apply(name,b,base,m,mp,defs,render)[1],mp)
        defs.append(dict(name='first',qualname='C.first',eligible=False,span=None))
        self.assertIs(self.apply('first',b,base,m,mp,defs,render)[1],mp)
        defs[0]['eligible']=False
        self.assertIs(self.apply('A.first',b,base,m,mp,defs,render)[1],mp)
    def test_incomplete_or_unapproved_target_keeps_m(self):
        b,base,m,mp,defs,render=self.setup_packets(m_lines=(1,5))
        self.assertIs(self.apply('first',b,base,m,mp,defs,render)[1],mp)
        b,base,m,mp,defs,render=self.setup_packets()
        self.assertIs(self.apply('first',b,base,m,mp,defs,render,approved=((5,5),))[1],mp)
    def test_render_growth_or_policy_cancels(self):
        b,base,m,mp,defs,render=self.setup_packets()
        def costly(t):
            p=render(t)
            from dataclasses import replace
            return replace(p,rendered=p.rendered+'header'*100)
        self.assertIs(self.apply('first',b,base,m,mp,defs,costly)[1],mp)
        self.assertIs(self.apply('first',b,base,m,mp,defs,render,accept=lambda p:False)[1],mp)
    def test_real_slice_headers_can_cancel_a_line_reduction(self):
        import router
        from routing_policy import Packet,Span
        text='x\n'*9
        def render(ts):
            spans=tuple(Span(t['start_line'],t['end_line']) for t in ts)
            return Packet(spans,tuple('x\n'*(s.end-s.start+1) for s in spans),router.render_slices(text,ts))
        b=[target(1),target(5)];m=[target(1,9)];base,mp=render(b),render(m)
        defs=[dict(name='goal',qualname='goal',eligible=True,span=(9,9))]
        _,p,info=self.apply('goal',b,base,m,mp,defs,render,approved=((9,9),))
        self.assertIs(p,mp);self.assertEqual(info['reason'],'rendered_growth')

    def test_no_second_parse(self):
        args=self.setup_packets()
        with patch.object(e.ast,'parse',side_effect=AssertionError('no parse')):
            self.apply('first',*args)
    def test_parse_failure_has_no_definitions(self):
        defs=[];e.complete_python_statements('def broken(',[],return_definitions=defs)
        self.assertEqual(defs,[])

if __name__=='__main__':unittest.main()

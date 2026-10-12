import importlib.util
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('workflow',Path(__file__).parents[1]/'scripts/run_workflow_bench.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)

class WorkflowTests(unittest.TestCase):
    def test_duplicate_turn_and_subset_counts(self):
        event={'type':'turn.completed','turn_id':'a','usage':{'input_tokens':100,'output_tokens':20,'cached_input_tokens':80,'reasoning_output_tokens':7}}
        result=w.usage_from_events('\n'.join([json.dumps(event)]*2))
        self.assertEqual(result['input_tokens']+result['output_tokens'],120)
        self.assertEqual(result['cached_input_tokens'],80)
    def test_distinct_turns_equal_counts_not_deduplicated(self):
        events=[{'type':'turn.completed','turn_id':n,'usage':{'input_tokens':100,'output_tokens':20}} for n in ['a','b']]
        self.assertEqual(w.usage_from_events('\n'.join(map(json.dumps,events)))['input_tokens'],200)
    def test_cumulative_replaces_increments(self):
        events=[{'type':'turn.completed','usage':{'input_tokens':100,'output_tokens':20}},
                {'type':'token_count','info':{'total_token_usage':{'input_tokens':200,'output_tokens':40,'cached_input_tokens':50}}},
                {'type':'token_count','info':{'total_token_usage':{'input_tokens':200,'output_tokens':40,'cached_input_tokens':50}}}]
        u=w.usage_from_events('\n'.join(map(json.dumps,events)))
        self.assertEqual(u['input_tokens']+u['output_tokens'],240)
    def test_out_of_order_cumulative_snapshot(self):
        events=[{'info':{'total_token_usage':{'input_tokens':200,'output_tokens':40}}},
                {'info':{'total_token_usage':{'input_tokens':100,'output_tokens':20}}}]
        self.assertEqual(w.usage_from_events('\n'.join(map(json.dumps,events)))['input_tokens'],200)
    def test_tools_and_missing_usage_rejected(self):
        with self.assertRaises(ValueError):w.usage_from_events('{}')
        with self.assertRaises(ValueError):w.usage_from_events(json.dumps({'item':{'type':'command_execution'}}))
    def test_related_file_and_budget(self):
        files={'primary.py':['x\n']*300,'related.py':['y\n']*250}
        r,_=w.admit_read({'file':'related.py','start_line':1,'end_line':250},files)
        self.assertEqual(r['end_line'],200)
        self.assertIsNone(w.admit_read({'file':'../secret','start_line':1,'end_line':2},files)[0])
        self.assertIsNone(w.admit_read({'file':'primary.py','start_line':True,'end_line':2},files)[0])
    def test_read_character_budget(self):
        r,_=w.admit_read({'file':'a','start_line':1,'end_line':20},{'a':['x'*3000+'\n']*20})
        self.assertLess(r['end_line'],20)
    def test_full_evidence_not_overlap(self):
        task={'facts':[{'id':'x','accepted_answers':['yes'],'required_evidence':[{'file':'a','start_line':10,'end_line':14}]}]}
        visible=[{'file':'a','start_line':1,'end_line':20}]
        answer={'answers':[{'id':'x','answer':'yes','evidence':[{'file':'a','start_line':10,'end_line':10}]}]}
        score=w.grade(task,answer,visible)[0]
        self.assertTrue(score['factual']);self.assertFalse(score['sufficient_evidence'])
        answer['answers'][0]['evidence'][0]['end_line']=14
        self.assertTrue(w.grade(task,answer,visible)[0]['sufficient_evidence'])
        self.assertFalse(w.grade(task,answer,[{'file':'a','start_line':10,'end_line':12}])[0]['sufficient_evidence'])
    def test_disjoint_citations_can_cover_whole_requirement(self):
        self.assertTrue(w.covered('a',10,14,[{'file':'a','start_line':10,'end_line':11},{'file':'a','start_line':12,'end_line':14}]))
        self.assertFalse(w.covered('a',10,14,[{'file':'a','start_line':10,'end_line':11},{'file':'a','start_line':13,'end_line':14}]))
    def test_partial_and_duplicate_recovery(self):
        files={'a':['x\n']*30};visible=[{'file':'a','start_line':1,'end_line':10}]
        ranges,reason=w.recovery_action({'kind':'read','file':'a','start_line':5,'end_line':15},files,visible,set())
        self.assertEqual(ranges,[{'file':'a','start_line':11,'end_line':15}])
        self.assertEqual(w.recovery_action({'kind':'read','file':'a','start_line':1,'end_line':10},files,visible,set())[1],'no_new_evidence')
    def test_search_shared_budget_and_duplicate(self):
        files={'a':['match\n']*400};seen=set()
        ranges,_=w.recovery_action({'kind':'search','file':'a','query':'match'},files,[],seen)
        self.assertEqual(sum(r['end_line']-r['start_line']+1 for r in ranges),200)
        self.assertEqual(w.recovery_action({'kind':'search','file':'a','query':'match'},files,[],seen)[1],'duplicate_search_blocked')
    def test_alternative_sufficient_evidence(self):
        r=lambda a,b:dict(file='a',start_line=a,end_line=b)
        task={'facts':[{'id':'x','accepted_answers':['yes'],'sufficient_evidence_sets':[[r(1,3)],[r(8,9)]]}]}
        response={'answers':[{'id':'x','answer':'yes','evidence':[r(8,9)]}]}
        self.assertTrue(w.grade(task,response,[r(8,9)])[0]['sufficient_evidence'])
    def test_diagnostics_whitelist(self):
        d=w.compact_diagnostic('[token-router status] '+json.dumps({'status':'needs_targeted_read','reason_codes':['x'],'suggested_ranges':[[2,5]],'secret':'must not expose'}))
        self.assertNotIn('secret',d);self.assertEqual(d['suggested_ranges'],[[2,5]])
    def test_duplicate_answer_ids_are_not_silently_selected(self):
        task={'facts':[{'id':'x','accepted_answers':['yes'],'required_evidence':[dict(file='a',start_line=1,end_line=1)]}]}
        answer=dict(id='x',answer='yes',evidence=[dict(file='a',start_line=1,end_line=1)])
        self.assertFalse(w.grade(task,{'answers':[answer,answer]},answer['evidence'])[0]['factual'])
    def test_failed_and_missing_usage_are_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'a.txt').write_text('x\n')
            task=dict(id='failure',primary='a',files={'a':'a.txt'},query='x',facts=[],split='dev')
            for unknown in (False,True):
                call=dict(returncode=1,seconds=.01,answer={},usage={k:0 for k in w.FIELDS})
                call['usage'].update(input_tokens=40,output_tokens=10)
                if unknown:call['usage_unknown']=True
                with patch.object(w,'main_call',return_value=call):
                    result=w.episode(task,'full',1,root,{},root/'runs')
                self.assertEqual(len(result['calls']),1)
                self.assertEqual(result['total_tokens'],None if unknown else 50)
                self.assertEqual(result['usage_complete'],not unknown)
    def test_search_only_task_terms(self):
        lines=['neutral\n']*50;lines[25]='some_symbol()\n'
        spans=w.search_ranges(lines,['some_symbol'])
        self.assertEqual(spans,[[20,32]])

if __name__=='__main__':unittest.main()

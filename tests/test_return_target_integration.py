import unittest
from unittest.mock import patch
import test_return_integration as prior
import router as r

class ReturnTargetIntegration(unittest.TestCase):
    def fixture(self):
        helper=prior.ReturnIntegration();helper.setUp();self.addCleanup(helper.doCleanups)
        helper.path.write_text(helper.path.read_text()+'\ndef other():\n    """lookup\n'+'    docs\n'*40+'    """\n    return unrelated\n'+'# neutral\n'*1500)
        return helper
    def test_unresolved_preserves_stdout_stderr_and_compact_input(self):
        f=self.fixture();m=f.run_route();n=f.run_route(['--return-target','missing'])
        self.assertEqual(m[:3],n[:3]);self.assertNotIn('return_target',n[2])
    def test_applied_preserves_target_and_no_model(self):
        f=self.fixture();m=f.run_route();n=f.run_route(['--return-target','lookup'])
        self.assertEqual(n[0],0);self.assertIn('return stored_value',n[1]);self.assertLessEqual(len(n[1]),len(m[1]));self.assertFalse(n[3]['model_called'])
        self.assertTrue(n[3]['return_target']['applied'])
    def test_source_change_after_filter_is_failure(self):
        f=self.fixture();original=r.limit_return_target
        def mutate(*a,**kw):
            result=original(*a,**kw);f.path.write_text(f.path.read_text()+'# mutation\n');return result
        with patch.object(r,'limit_return_target',side_effect=mutate):code,out,_,status=f.run_route(['--return-target','lookup'])
        self.assertEqual(code,1);self.assertEqual(out,'');self.assertIn('source_changed',status['reason_codes'])
    def test_explicit_modes_reject_new_option_without_model_call(self):
        for flag in ['--force-model','--deterministic']:
            with self.subTest(flag=flag),self.assertRaises(SystemExit):r.parse_args(['router.py','heavy_code','a.py',flag,'--return-target','x'])
        with self.assertRaises(SystemExit):r.parse_args(['router.py','heavy_code','a.py','--optimize','latency','--return-target','x'])

if __name__=='__main__':unittest.main()

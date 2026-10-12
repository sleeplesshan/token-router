import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import bench_process as b


class BenchProcessTests(unittest.TestCase):
    def call(self, code, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            result = b.capture([sys.executable, '-u', '-c', code], tmp,
                               idle_timeout=2, absolute_timeout=3, grace=.1, **kwargs)
            self.assertTrue((Path(tmp)/'events.jsonl').exists())
            return result

    def test_partial_chunks_and_stderr_are_drained(self):
        event = json.dumps(dict(type='turn.completed', usage=dict(input_tokens=12, output_tokens=3)))
        code = f"import sys,time;sys.stdout.write({event[:20]!r});sys.stdout.flush();sys.stderr.write('x'*70000);sys.stderr.flush();time.sleep(.05);print({event[20:]!r})"
        r = self.call(code)
        self.assertTrue(r['usage_complete'])
        self.assertEqual(r['usage']['input_tokens']+r['usage']['output_tokens'],15)

    def test_stderr_noise_does_not_hide_stdout_silence(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=b.capture([sys.executable,'-u','-c',"import sys,time\nwhile True: print('noise',file=sys.stderr,flush=True);time.sleep(.02)"],tmp,
                        idle_timeout=.25,absolute_timeout=2,grace=.1)
        self.assertEqual(r['termination_reason'],'idle_timeout')
        self.assertIsNone(r['usage'])

    def test_activity_does_not_hide_absolute_deadline(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=b.capture([sys.executable,'-u','-c',"import time\nwhile True: print('{}',flush=True);time.sleep(.03)"],tmp,
                        idle_timeout=1,absolute_timeout=.3,grace=.1)
        self.assertEqual(r['termination_reason'],'absolute_timeout')

    def test_incomplete_cumulative_usage_is_lower_bound(self):
        event=dict(info=dict(total_token_usage=dict(input_tokens=10,output_tokens=2)))
        r=self.call(f'print({json.dumps(event)!r})')
        self.assertFalse(r['usage_complete'])
        self.assertIsNone(r['usage'])
        self.assertEqual(b.aggregate([r])['known_lower_bound'],12)
        self.assertIsNone(b.aggregate([r])['total_tokens'])
        self.assertFalse(b.retry_admissible([r]))

    def test_known_failed_attempt_and_retry_both_count(self):
        event=dict(type='turn.completed',usage=dict(input_tokens=10,output_tokens=2,cached_input_tokens=8,reasoning_output_tokens=1))
        failed=self.call(f'import sys;print({json.dumps(event)!r});sys.exit(1)')
        self.assertTrue(b.retry_admissible([failed]))
        success=self.call(f'print({json.dumps(event)!r})')
        total=b.aggregate([failed,success])
        self.assertEqual(total['total_tokens'],24)
        self.assertEqual(total['usage']['cached_input_tokens'],16)
        self.assertFalse(b.retry_admissible([failed,success]))

    def test_duplicate_usage_is_not_double_counted(self):
        event=dict(type='turn.completed',usage=dict(input_tokens=10,output_tokens=2))
        r=self.call(f'print({json.dumps(event)!r});print({json.dumps(event)!r})')
        self.assertEqual(b.aggregate([r])['total_tokens'],12)

    def test_new_incomplete_turn_invalidates_prior_complete_bill(self):
        event=dict(type='turn.completed',usage=dict(input_tokens=10,output_tokens=2))
        r=self.call(f'print({json.dumps(event)!r});print(\'{{"type":"turn.started"}}\')')
        self.assertFalse(r['usage_complete'])
        self.assertEqual(r['known_usage_lower_bound']['input_tokens'],10)

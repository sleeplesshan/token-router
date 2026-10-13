import unittest
from native_client import reconcile
class ClientTests(unittest.TestCase):
 def test_usage_is_cumulative_and_duplicate_items_not_double_counted(self):
  cmd={'method':'item/completed','params':{'threadId':'t','turnId':'u','item':{'id':'x','type':'commandExecution','command':'rg x','aggregatedOutput':'','exitCode':1}}}
  ev=[{'method':'thread/tokenUsage/updated','params':{'threadId':'t','tokenUsage':{'total':{'inputTokens':10,'outputTokens':2,'cachedInputTokens':4,'reasoningOutputTokens':1}}}},cmd,cmd,{'method':'thread/tokenUsage/updated','params':{'threadId':'t','tokenUsage':{'total':{'inputTokens':50,'outputTokens':9,'cachedInputTokens':30,'reasoningOutputTokens':7}}}},{'method':'turn/completed','params':{'turn':{'id':'u','status':'failed'}}}]
  d=reconcile(ev,'t','u');self.assertEqual(len(d['commands']),1);self.assertEqual(d['usage']['input_tokens'],50);self.assertTrue(d['usage_complete'])
 def test_missing_and_stale_usage_stays_incomplete(self):
  for ev in ([],[{'method':'turn/completed','params':{'turn':{'id':'u','status':'completed'}}}]):self.assertFalse(reconcile(ev,'t','u')['usage_complete'])
if __name__=='__main__':unittest.main()

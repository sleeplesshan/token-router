from pathlib import Path
import hashlib,json,statistics as st
R=Path(__file__).parent;roots=[R,R.parent/'native-auto-code-negative-20261013'];sha=lambda b:hashlib.sha256(b).hexdigest()
rows=[json.loads(p.read_text())for root in roots for p in sorted((root/'run').glob('*/result.json'))]
assert len(rows)==20 and all(r['usage_complete']for r in rows)
def stats(rs):
 def med(k):return st.median(r[k]for r in rs)if rs else None
 return dict(episodes=len(rs),strict=sum(r['strict']for r in rs),facts=sum(r['facts']for r in rs),success=sum(r['success']for r in rs),total_tokens=sum(r['total_tokens']for r in rs),tokens_median=med('total_tokens'),whole_wall=sum(r['whole_wall']for r in rs),wall_median=med('whole_wall'),cpu=sum(r['cpu']for r in rs),remote_wait_proxy=sum(r['remote_wait_proxy']for r in rs),router_calls=sum(r['router_calls']for r in rs),guide_reads=sum(r['guide_reads']for r in rs),source_calls=sum(r['source_commands']for r in rs),runtime_bypasses=sum(r['runtime_bypasses']for r in rs),failed=sum(r['returncode']!=0 for r in rs),usage_unknown=sum(not r['usage_complete']for r in rs),local_tool_wall_ms=sum(c['duration_ms']or 0 for r in rs for c in r['commands']if c.get('kind')=='mcp'))
s={'measurement':'16 paired main trial episodes plus separately pre-locked 4 code exclusion episodes; descriptive combined total, not new unified holdout','groups':{},'tasks':{},'paired':[],'execution_locks':[json.loads((root/'run/execution-lock.json').read_text())for root in roots]}
for label,pred in [('admitted_logs',lambda r:r['expected']=='activate'),('excluded',lambda r:r['expected']=='bypass'),('all',lambda r:True)]:s['groups'][label]={a:stats([r for r in rows if pred(r)and r['arm']==a])for a in ('plain','implicit')}
for t in sorted({r['task']for r in rows}):
 s['tasks'][t]={a:stats([r for r in rows if r['task']==t and r['arm']==a])for a in ('plain','implicit')}
 for rep in (1,2):
  p,g=[next(r for r in rows if r['task']==t and r['repeat']==rep and r['arm']==a)for a in ('plain','implicit')]
  s['paired'].append(dict(task=t,repeat=rep,token_delta=g['total_tokens']-p['total_tokens'],wall_delta=g['whole_wall']-p['whole_wall'],strict_delta=g['strict']-p['strict']))
(R/'combined-summary.json').write_text(json.dumps(s,indent=2)+'\n');(R/'combined-episodes.json').write_text(json.dumps([{k:v for k,v in r.items()if k!='events'}for r in rows],indent=2,ensure_ascii=False)+'\n')
ledger=[]
for name in ('implicit-default-20261013','implicit-narrow-20261013','native-auto-20261013','native-auto-guidance-20261013','native-auto-direct-20261013','native-auto-code-negative-20261013'):
 root=R.parent/name;term=json.loads((root/'run/terminal.json').read_text());rs=[json.loads(p.read_text())for p in (root/'run').glob('*/result.json')];tokens=sum(r['known_usage_lower_bound'] for r in rs);assert tokens==term['budget']['known_tokens']
 ledger.append(dict(experiment=name,episodes=len(rs),known_input_output=tokens,usage_unknown=term['budget']['unknown_usage'],termination=term['status'],manifest_sha256=sha((root/'manifest.json').read_bytes()),execution_lock_sha256=sha((root/'run/execution-lock.json').read_bytes()),commit=json.loads((root/'manifest.json').read_text())['commit']))
(R/'all-attempt-ledger.json').write_text(json.dumps(dict(experiments=ledger,total_main_turns=sum(x['episodes']for x in ledger),known_input_output=sum(x['known_input_output']for x in ledger),usage_unknown=sum(x['usage_unknown']for x in ledger),note='Research iteration costs. Do not mix different candidates into the final paired causal comparison; all stopped/failed candidates retained. Historical pre-task unknown-usage experiments remain separate.'),indent=2)+'\n')
for k,a in s['groups'].items():
 p,g=a['plain'],a['implicit'];print(k,p['total_tokens'],g['total_tokens'],round((g['total_tokens']/p['total_tokens']-1)*100,3),'wall',p['whole_wall'],g['whole_wall'],'facts',g['strict'],g['facts'])

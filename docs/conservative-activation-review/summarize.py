from pathlib import Path
import hashlib,json,statistics as st,zipfile
R=Path(__file__).parent;rows=[json.loads(p.read_text())for p in sorted((R/'run').glob('*/result.json'))];sha=lambda b:hashlib.sha256(b).hexdigest()
assert len(rows)==16,len(rows)
summary={'manifest_sha256':sha((R/'manifest.json').read_bytes()),'measurement':json.loads((R/'run/execution-lock.json').read_text()),'terminal':json.loads((R/'run/terminal.json').read_text()),'tasks':{},'groups':{}}
def stats(rs):
 return dict(episodes=len(rs),strict=sum(x['strict']for x in rs),facts=sum(x['facts']for x in rs),successful=sum(x['success']for x in rs),total_tokens=sum(x['total_tokens']for x in rs),tokens_median=st.median(x['total_tokens']for x in rs),whole_wall=sum(x['whole_wall']for x in rs),wall_median=st.median(x['whole_wall']for x in rs),cpu=sum(x['cpu']for x in rs),remote_wait_proxy=sum(x['remote_wait_proxy']for x in rs),router_calls=sum(x['router_calls']for x in rs),profile_calls=sum(x['profile_calls']for x in rs),guide_reads=sum(x['guide_reads']for x in rs),skill_attached=sum(x['skill_attached']for x in rs),runtime_bypasses=sum(x['runtime_bypasses']for x in rs),recovery_commands=sum(max(0,x['source_commands']-1)for x in rs if x['skill_attached']),usage_unknown=sum(not x['usage_complete']for x in rs))
for label,ts in [('admitted_logs',['cpython_trace','scipy_failure_blocks']),('excluded',['pandas_dispatch','visible_summary']),('all',sorted({x['task']for x in rows}))]:
 summary['groups'][label]={arm:stats([x for x in rows if x['task']in ts and x['arm']==arm])for arm in ('plain','gated')}
for t in sorted({x['task']for x in rows}):summary['tasks'][t]={arm:stats([x for x in rows if x['task']==t and x['arm']==arm])for arm in ('plain','gated')}
summary['paired']=[dict(task=t,repeat=rep,token_delta=g['total_tokens']-p['total_tokens'],wall_delta=g['whole_wall']-p['whole_wall'],strict_delta=g['strict']-p['strict'])for t in summary['tasks']for rep in (1,2)for p in rows if p['task']==t and p['repeat']==rep and p['arm']=='plain'for g in rows if g['task']==t and g['repeat']==rep and g['arm']=='gated']
(R/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(R/'episodes.json').write_text(json.dumps([{k:v for k,v in x.items()if k!='events'}for x in rows],indent=2,ensure_ascii=False)+'\n')
for group,arms in summary['groups'].items():
 p,g=arms['plain'],arms['gated'];print(group,p['total_tokens'],g['total_tokens'],'tokens%',100*(g['total_tokens']/p['total_tokens']-1),'wall',p['whole_wall'],g['whole_wall'],'wall%',100*(g['whole_wall']/p['whole_wall']-1),g['strict'],'/',g['facts'])

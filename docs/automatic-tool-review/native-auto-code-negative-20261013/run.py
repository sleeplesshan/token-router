from pathlib import Path
import hashlib,json,sys,time
from native_client import episode
from grade import grade
R=Path(__file__).parent;REPO=Path('<workspace>/token-router');sys.path.insert(0,str(REPO/'scripts'))
from run_workflow_bench import SCHEMA
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((R/'manifest.json').read_text());prompts=json.loads((R/'prompts.json').read_text());common=(R/'instructions.md').read_text();OUT=R/'run';OUT.mkdir()
limits=dict(main_turns=4,total_tokens=160000,per_episode_token_cap=60000,absolute_timeout=240,idle_timeout=90,grace_timeout=10,additional_source_commands=3,total_wall=1800)
payload=R/'workspaces/implicit/.agents/skills/token-router'
lock=dict(limits=limits,**{k:m[k]for k in ('package_version','candidate','commit','policy_version','model','reasoning')},manifest_hash=sha((R/'manifest.json').read_bytes()),prompt_hashes={t:sha(p.encode())for t,p in prompts.items()},common_hash=sha(common.encode()),grader_hash=sha((R/'grade.py').read_bytes()),seed_hashes={t['id']:sha((R/(t['id']+'-seed.txt')).read_bytes())for t in m['tasks']},client_hash=sha((R/'native_client.py').read_bytes()),harness_hash=sha(Path(__file__).read_bytes()),payload_hashes={str(p.relative_to(payload)):sha(p.read_bytes())for p in payload.rglob('*')if p.is_file()},schedule=[(t['id'],rep)for rep in (1,2)for t in m['tasks']],criteria='Code exclusions must make no guide/reader calls; no token-saving criterion for this exclusion-only check. No fixed-rubric loss/new insufficient approval. Positive implicit actual reader/profile 4/4, negative guide/reader0/4; all billed costs complete; Each positive-task aggregate AND positive-group/whole tokens reduced; per-repeat increases reported. No universal guarantee. Stop pilot after first repeat if no aggregate or log savings, missing activation or quality issue. No retuning or forced attachment.',measurement='Directly exposed local MCP reader (deferred discovery excluded by server setting) plus installed setup skill enabled on ALL tasks. Identical text-only tasks, no force or skill attachment; schema/context and all main usage counted. Actual native MCP calls required on positives; guide loads forbidden. No header seed except negative visible. Known sources, not new holdout; all-attempt input+output; cached/reasoning subsets not added.')
(OUT/'execution-lock.json').write_text(json.dumps(lock,indent=2)+'\n')
for arm,enabled in [('plain',False),('implicit',True)]:
 d=episode(R/'preflight'/arm,R/'workspaces'/arm,'No model turns are authorized during preflight.','',{},enabled,True);assert d['returncode']==0,d['errors']
rows=[];budget=dict(main_turns=0,known_tokens=0,unknown_usage=0);terminal='completed';start=time.monotonic();tasks={t['id']:t for t in m['tasks']}
try:
 for i,(tid,rep)in enumerate(lock['schedule']):
  if budget['known_tokens']+60000>limits['total_tokens']:raise RuntimeError('pair_admission_budget')
  for arm in (('plain','implicit')if i%2==0 else('implicit','plain')):
   if budget['main_turns']>=4 or time.monotonic()-start>1800:raise RuntimeError('global_budget')
   t=tasks[tid];name=f'{tid}-{rep}-{arm}';d=OUT/name;d.mkdir();prompt=prompts[tid];(d/'prompt.txt').write_text(prompt);budget['main_turns']+=1
   print('START',name,flush=True)
   result=episode(d/'attempt-1',R/'workspaces'/arm,common,prompt,SCHEMA,arm=='implicit')
   (d/'attempt-1/result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
   u=result['usage'];known=None if u is None else u['input_tokens']+u['output_tokens'];budget['known_tokens']+=known or 0
   if not result['usage_complete']:budget['unknown_usage']+=1
   commands=result['commands'];readers=[c for c in commands if 'scripts/router.py'in c['command'] or c.get('kind')=='mcp'];guide_reads=[c for c in commands if 'SKILL.md'in c['command']];sources=[c for c in commands if t['file']in c['command']]
   row=dict(name=name,task=tid,family=t['family'],expected=t['expected'],arm=arm,repeat=rep,**result,whole_wall=result['wall'],total_tokens=known if result['usage_complete']else None,known_usage_lower_bound=known,router_calls=len(readers),profile_calls=sum(c.get('kind')=='mcp' or ('--activation-profile'in c['command']and'log-context'in c['command'])for c in readers),guide_reads=len(guide_reads),source_commands=len(sources),runtime_bypasses=sum(c['exit_code']!=0 or '"status": "not_returned"'in c['aggregated_output'] for c in readers),**{k:m[k]for k in ('package_version','commit','policy_version','model','reasoning')},source_sha256=t['source_sha256'],prompt_sha256=sha(prompt.encode()),instructions_sha256=sha(common.encode()))
   row['scores']=grade(row,t);row['strict']=sum(x['grounded']for x in row['scores']);row['facts']=len(t['facts']);row['success']=row['strict']==row['facts']and row['returncode']==0
   (d/'result.json').write_text(json.dumps(row,indent=2,ensure_ascii=False)+'\n');rows.append(row);(OUT/'budget.json').write_text(json.dumps(budget,indent=2)+'\n')
   print('DONE',name,'tokens',row['total_tokens'],'strict',row['strict'],'/',row['facts'],'router',row['router_calls'],'guide',row['guide_reads'],'wall',round(row['whole_wall'],2),flush=True)
   if not result['usage_complete'] or result['returncode']:raise RuntimeError('failed_or_unknown:'+name)
   if len(sources)>3:raise RuntimeError('source_budget:'+name)
   if arm=='implicit' and t['expected']=='activate' and (row['guide_reads'] or row['router_calls']!=1 or row['profile_calls']!=1 or row['runtime_bypasses']):raise RuntimeError('activation_contract:'+name)
   if (arm=='plain' or t['expected']=='bypass') and (readers or guide_reads):raise RuntimeError('bypass_contract:'+name)
   if sha((R/'workspaces'/arm/t['file']).read_bytes())!=t['source_sha256']:raise RuntimeError('source_changed')
   if budget['known_tokens']>limits['total_tokens']:raise RuntimeError('token_limit')
   if not row['success']:raise RuntimeError('quality_stop:'+name)
  if i==3:
   for subset in (rows,[r for r in rows if r['expected']=='activate']):
    totals={a:sum(r['total_tokens'] for r in subset if r['arm']==a)for a in ('plain','implicit')}
    if totals['implicit']>=totals['plain']:raise RuntimeError('pilot_no_savings:'+str(totals))
except Exception as exc:terminal=type(exc).__name__+':'+str(exc)
finally:
 (OUT/'terminal.json').write_text(json.dumps(dict(status=terminal,budget=budget,wall=time.monotonic()-start,episodes=len(rows)),indent=2)+'\n');print('TERMINAL',terminal,budget,flush=True)

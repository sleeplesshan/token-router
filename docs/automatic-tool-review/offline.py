from pathlib import Path
import json,os,subprocess,sys,time,statistics as st,hashlib
R=Path(__file__).parent;P=Path('<workspace>/token-router');sys.path.insert(0,str(P/'scripts'));from mcp_server import Server
rows=[json.loads(p.read_text())for p in (R/'run').glob('*/result.json')];out=[]
for r in rows:
 for c in r['commands']:
  if c.get('kind')!='mcp':continue
  args=json.loads(c['command'].split(' ',1)[1]);root=R/'workspaces/implicit';path=Path(args['path']);path=path if path.is_absolute()else root/path;args={**args,'path':str(path)}
  timings={'manual':[],'mcp':[]};env={k:v for k,v in os.environ.items()if not k.startswith('ROUTER_')};env['PYTHONDONTWRITEBYTECODE']='1'
  cmd=[sys.executable,str(P/'scripts/router.py'),'error_log',str(path)]
  for term in [*args['failure_headers'],args.get('result_term',' failed')]:cmd+=['--search-term',term]
  cmd+=['--activation-profile','log-context','--line-numbers','--compact-status']
  for rep in range(5):
   start=time.perf_counter();manual=subprocess.run(cmd,env=env,capture_output=True,text=True,check=True);timings['manual'].append(time.perf_counter()-start)
   start=time.perf_counter();packet=Server([root]).call(args);timings['mcp'].append(time.perf_counter()-start)
   assert not packet['isError'];assert manual.stdout==packet['content'][0]['text']==c['aggregated_output']
  diagnostic=subprocess.run([a for a in cmd if a!='--compact-status'],env=env,capture_output=True,text=True,check=True)
  status=json.loads(next(x for x in diagnostic.stderr.splitlines()if x.startswith('[token-router status]')).partition('] ')[2]);out.append(dict(episode=r['name'],stdout_sha256=hashlib.sha256(manual.stdout.encode()).hexdigest(),rendered_chars=len(manual.stdout),open_count=status['open_count'],unchanged_packet=True,repetitions=5,median_local_wall={k:st.median(v)for k,v in timings.items()},all_local_wall=timings))
assert not (R/'offline-ablation.json').exists(),'Choose a fresh output location; never overwrite prior measurements'
(R/'offline-ablation.json').write_text(json.dumps(out,indent=2)+'\n');print('4 original MCP packets equal guarded CLI;5 repeats each; no model calls')

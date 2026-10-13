from pathlib import Path
import hashlib,json,subprocess,sys,time,resource
R=Path(__file__).parent;REPO=Path('/Users/han/Documents/Token/token-router');sys.path.insert(0,str(REPO/'scripts'))
from routing_policy import plan_activation
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((R/'manifest.json').read_text());rows=[]
for t in m['tasks']:
 d=plan_activation(**t['activation_request']);row=dict(task=t['id'],host_action=d.action,reason_codes=d.reason_codes,source_sha256=t['source_sha256'])
 if d.action=='activate':
  opts=['error_log',str(R/'sources'/t['file']),'--line-numbers','--compact-status']
  for term in t['terms']:opts+=['--search-term',term]
  outputs=[];times=[]
  for profile in (False,True):
   sample=[]
   for n in range(5):
    report=R/f'offline-{t["id"]}-{profile}-{n}.json';cmd=[sys.executable,str(REPO/'scripts/router.py'),*opts,'--report-json',str(report)]+(['--activation-profile','log-context']if profile else[])
    start=time.perf_counter();cpu0=resource.getrusage(resource.RUSAGE_CHILDREN);p=subprocess.run(cmd,capture_output=True,text=True);wall=time.perf_counter()-start;cpu1=resource.getrusage(resource.RUSAGE_CHILDREN)
    assert p.returncode==0;outputs.append(p.stdout);sample.append(dict(wall=wall,cpu=(cpu1.ru_utime+cpu1.ru_stime)-(cpu0.ru_utime+cpu0.ru_stime),status=json.loads(report.read_text())))
   times.append(sample)
  assert len({sha(s.encode())for s in outputs})==1
  row.update(stdout_sha256=sha(outputs[0].encode()),rendered_chars=len(outputs[0]),manual=times[0],gated=times[1],stdout_unchanged=True)
 rows.append(row)
(R/'offline.json').write_text(json.dumps(dict(commit=m['commit'],package_version=m['package_version'],policy_version=m['policy_version'],rows=rows),indent=2)+'\n')
print([(r['task'],r['host_action'],r.get('stdout_unchanged'))for r in rows])

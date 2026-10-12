import contextlib,hashlib,io,json,os,re,subprocess,sys,time
from pathlib import Path
R=Path(__file__).parent;REPO=Path(os.environ['TOKEN_ROUTER_REPO'])
def worker():
 j=json.load(sys.stdin);sys.path.insert(0,str(R/'baseline/scripts' if j['arm']=='B' else REPO/'scripts'));import router as r
 r.call_codex=lambda p:(_ for _ in ()).throw(AssertionError('network/model forbidden'))
 out,err=io.StringIO(),io.StringIO();args=['router.py',j['mode'],str(R/j['file']),'--query',j['query']]
 if j['arm']=='bounded':args+=['--return-context','bounded']
 if j['arm']=='target':args+=['--return-target',j['target']]
 start=time.perf_counter();cpu=time.process_time()
 with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):code=r.main(args)
 wall=time.perf_counter()-start;cpu=time.process_time()-cpu;text=out.getvalue();status=json.loads(next(x.split('] ',1)[1] for x in err.getvalue().splitlines() if x.startswith('[token-router status]')))
 spans=[(int(a),int(b)) for a,b in re.findall(r'--- \[RAW CONTENT FROM LINE (\d+) TO (\d+)\] ---',text)]
 lines=(R/j['file']).read_text(encoding='utf-8',errors='replace').splitlines(keepends=True)
 pieces=re.findall(r'--- \[RAW CONTENT FROM LINE (\d+) TO (\d+)\] ---\n(.*?)\n--- \[END OF SLICE\] ---',text,re.S)
 assert len(pieces)==len(spans) and all(raw==''.join(lines[int(a)-1:int(b)]) for a,b,raw in pieces)
 print(json.dumps(dict(code=code,stdout_sha256=hashlib.sha256(text.encode()).hexdigest(),chars=len(text),spans=spans,status=status['status'],model_called=status.get('model_called',False),wall=wall,cpu=cpu,raw_valid=True)))
def run(t,arm):
 return json.loads(subprocess.check_output([sys.executable,__file__,'--worker'],input=json.dumps(dict(arm=arm,mode=t['mode'],file=t['files'][t['primary']],query=t['query'],target=t.get('return_target'))),text=True))
def main():
 m=json.loads((R/'mixed-manifest.json').read_text());rows=[]
 for t in m['tasks']:
  arms=['B','default']+(['bounded'] if t['mode']=='heavy_code' else [])+(['target'] if t['return_target'] else [])
  results={a:run(t,a) for a in arms};sets={a:{i for x,y in z['spans'] for i in range(x,y+1)} for a,z in results.items()};assert results['B']['stdout_sha256']==results['default']['stdout_sha256'];assert all(sets['B']<=s for s in sets.values());assert all(not z['model_called'] for z in results.values())
  for a,z in results.items():
   z['initial_all_facts_covered']=all(any(all(e['file']==t['primary'] and set(range(e['start_line'],e['end_line']+1))<=sets[a] for e in es) for es in f.get('sufficient_evidence_sets',[f['required_evidence']])) for f in t['facts'])
  rows.append(dict(id=t['id'],group=t['group'],arms=results));print(t['id'],{a:(v['status'],v['chars'],v['initial_all_facts_covered']) for a,v in results.items()},flush=True)
 stress=[]
 for q in m['stress_queries']:
  t=dict(m['tasks'][12],query=q,return_target=None);z={a:run(t,a) for a in ['B','default']};assert z['B']['stdout_sha256']==z['default']['stdout_sha256'];stress.append(dict(query=q,arms=z))
 (R/'mixed-results.json').write_text(json.dumps(dict(rows=rows,stress=stress,scope='local packet coverage, not model answer accuracy',product_modules={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (REPO/'scripts').glob('*.py') if p.name in ['router.py','evidence_checks.py','source_guard.py','routing_policy.py','query_matcher.py']}),indent=2)+'\n')
if __name__=='__main__':worker() if '--worker' in sys.argv else main()

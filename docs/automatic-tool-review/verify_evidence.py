"""Reconcile public counters/inputs/packets/frozen scores without a model call."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,tempfile,zipfile
D=Path(__file__).resolve().parent
ledger=json.loads((D/'all-attempt-ledger.json').read_text());total=0;turns=0
for entry in ledger['experiments']:
 root=D/entry['experiment'];rows=json.loads((root/'episodes.json').read_text());m=json.loads((root/'manifest.json').read_text());tasks={t['id']:t for t in m['tasks']};bill=0
 for task in tasks.values():
  assert hashlib.sha256((D/'sources'/task['file']).read_bytes()).hexdigest()==task['source_sha256']
 spec=importlib.util.spec_from_file_location('frozen_grader',root/'grade.py');grader=importlib.util.module_from_spec(spec);spec.loader.exec_module(grader)
 with tempfile.TemporaryDirectory() as temp,zipfile.ZipFile(root/'events.zip')as z:
  tmp=Path(temp);shutil.copytree(D/'sources',tmp/'sources');grader.R=tmp
  for p in root.glob('*-seed.txt'):shutil.copyfile(p,tmp/p.name)
  prompts={}
  for row in rows:
   events=[json.loads(l)for l in z.read(row['name']+'/events.jsonl').decode().splitlines()];usage=[e['params']['tokenUsage']['total']for e in events if e.get('method')=='thread/tokenUsage/updated'][-1]
   amount=usage['inputTokens']+usage['outputTokens'];assert amount==row['total_tokens']==row['known_usage_lower_bound'];bill+=amount;turns+=1
   assert row['usage_complete'] and row['drain_complete'] and not row['capture_truncated']
   usage_index=max(i for i,e in enumerate(events)if e.get('method')=='thread/tokenUsage/updated');last=max(i for i,e in enumerate(events)if e.get('method')=='item/completed' and e['params']['item']['type']in ('commandExecution','mcpToolCall','agentMessage'));assert usage_index>last
   seen=set();commands=[]
   for e in events:
    if e.get('method')!='item/completed':continue
    item=e['params']['item'];key=item.get('id')
    if key in seen:continue
    seen.add(key)
    if item['type']=='commandExecution':commands.append((item['command'],item.get('aggregatedOutput')or ''))
    if item['type']=='mcpToolCall':commands.append(('mcp://'+item['server']+'/'+item['tool']+' '+json.dumps(item['arguments'],ensure_ascii=False),'\n'.join(b.get('text','')for b in (item.get('result')or{}).get('content',[])if isinstance(b,dict)and b.get('type')=='text')))
   assert commands==[(c['command'],c['aggregated_output'])for c in row['commands']]
   assert grader.grade(row,tasks[row['task']])==row['scores']
   sent=json.loads(z.read(row['name']+'/main-input.json'));assert len(sent)==1;items=sent[0]['params']['input'];assert all(i['type']=='text'for i in items)
   pair=(row['task'],row['repeat']);text=''.join(i['text']for i in items)
   if pair in prompts:assert prompts[pair]==text
   else:prompts[pair]=text
 assert bill==entry['known_input_output'];total+=bill
 print(entry['experiment'],len(rows),bill,'PASS')
assert total==ledger['known_input_output']==917402 and turns==42
print('PASS:42 known main turns;917402 input+output; all raw scores preserved; no models/network')

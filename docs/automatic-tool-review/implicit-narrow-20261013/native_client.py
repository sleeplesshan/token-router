"""Bounded native main-turn driver; all notifications retained, including RPC/grace/shutdown."""
from pathlib import Path
import json, os, queue, resource, signal, subprocess, threading, time, tomllib
R=Path(__file__).parent

def settings(cwd, attach):
    c={'model_reasoning_effort':'medium','model_provider':'openai','forced_login_method':'chatgpt','approval_policy':'never','features.multi_agent':False,'features.apps':False,'features.hooks':False,'features.memories':False,'agents.enabled':False,'apps._default.enabled':False,'web_search':'disabled','project_doc_max_bytes':0,'skills.include_instructions':True,'developer_instructions':'','analytics.enabled':False}
    data=tomllib.loads((R/'skill-config.txt').read_text())
    skills=data['skills']['config']
    skills.append({'path':str(cwd/'.agents/skills/token-router/SKILL.md'),'enabled':attach})
    skillconf='skills.config=['+','.join('{path='+json.dumps(s['path'])+',enabled='+str(s['enabled']).lower()+'}' for s in skills)+']'
    user=Path.home()/'.codex/config.toml'
    if user.exists():
        for name in tomllib.loads(user.read_text()).get('mcp_servers',{}):c['mcp_servers.'+name+'.enabled']=False
    cmd=['codex','app-server','--stdio']
    for k,v in c.items():cmd+=['-c',k+'='+json.dumps(v)]
    return cmd+['-c',skillconf]

class Client:
    def __init__(self,directory,cwd,attach):
        self.d=Path(directory);self.d.mkdir(parents=True);self.cwd=Path(cwd);self.seq=0;self.events=[];self.q=queue.Queue();self.size=0;self.truncated=False
        self.start=time.monotonic();self.activity=self.start;self.grace=False;self.cpu0=self.cpu()
        cmd=settings(self.cwd,attach);(self.d/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
        env=os.environ.copy()
        for k in list(env):
            if k.startswith('ROUTER_') or k in ('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL'):env.pop(k)
        env.update(PYTHONDONTWRITEBYTECODE='1',TOKEN_ROUTER_ACTIVE='1')
        self.p=subprocess.Popen(cmd,cwd=cwd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        self.log=(self.d/'events.jsonl').open('wb');self.err=(self.d/'stderr.txt').open('wb');self.requests=(self.d/'requests.jsonl').open('w')
        def reader(stream,name):
            for data in iter(stream.readline,b''):self.q.put((name,data))
            self.q.put((name+'_eof',b''))
        self.readers=[threading.Thread(target=reader,args=(self.p.stdout,'stdout')),threading.Thread(target=reader,args=(self.p.stderr,'stderr'))]
        for t in self.readers:t.start()
    def cpu(self):
        a=resource.getrusage(resource.RUSAGE_CHILDREN);return a.ru_utime+a.ru_stime
    def send(self,obj):
        self.requests.write(json.dumps(obj,ensure_ascii=False)+'\n');self.requests.flush()
        self.p.stdin.write((json.dumps(obj,ensure_ascii=False)+'\n').encode());self.p.stdin.flush()
    def consume(self,name,data):
        if name.endswith('_eof'):return None
        room=max(0,4000000-self.size);kept=data[:room];self.size+=len(kept)
        f=self.log if name=='stdout' else self.err;f.write(kept);f.flush()
        if len(kept)<len(data):self.truncated=True
        if name!='stdout':return None
        try:e=json.loads(data)
        except ValueError:return None
        self.events.append(e);self.activity=time.monotonic();return e
    def next(self,wait_deadline=None):
        while True:
            now=time.monotonic()
            if wait_deadline and now>wait_deadline:raise TimeoutError('grace_timeout')
            if not self.grace and (now-self.start>240 or now-self.activity>90):raise TimeoutError('turn_timeout')
            try:name,data=self.q.get(timeout=.05)
            except queue.Empty:
                if self.p.poll() is not None:raise RuntimeError('appserver exited')
                continue
            if name=='stdout_eof':raise RuntimeError('appserver EOF')
            e=self.consume(name,data)
            if self.truncated:raise RuntimeError('capture_limit')
            if not self.grace and e and e.get('method')=='thread/tokenUsage/updated':
                u=e['params']['tokenUsage']['total']
                if u['inputTokens']+u['outputTokens']>60000:raise RuntimeError('episode_token_cap')
            if e:return e
    def rpc(self,method,params):
        self.seq+=1;id=self.seq;self.send(dict(id=id,method=method,params=params))
        while True:
            e=self.next()
            if e.get('id')==id:
                if 'error' in e:raise RuntimeError('RPC '+method+': '+str(e['error']))
                return e['result']
    def close(self):
        try:self.p.stdin.close();self.p.wait(timeout=3)
        except (OSError,subprocess.TimeoutExpired):
            try:os.killpg(self.p.pid,signal.SIGTERM);self.p.wait(timeout=3)
            except (ProcessLookupError,subprocess.TimeoutExpired):
                try:os.killpg(self.p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                self.p.wait()
        for t in self.readers:t.join(timeout=2)
        while True:
            try:name,data=self.q.get_nowait()
            except queue.Empty:break
            self.consume(name,data)
        self.drain_complete=all(not t.is_alive() for t in self.readers)
        self.log.close();self.err.close();self.requests.close()

def reconcile(events,thread,turn):
    commands=[];answer=None;usage=None;usage_i=-1;last_item=-1;terminal=None;errors=[];ids=set()
    for i,e in enumerate(events):
        p=e.get('params',{});method=e.get('method')
        if p.get('threadId') not in (None,thread):continue
        if method=='thread/tokenUsage/updated':
            u=p['tokenUsage']['total'];usage={k:u[v] for k,v in [('input_tokens','inputTokens'),('output_tokens','outputTokens'),('cached_input_tokens','cachedInputTokens'),('reasoning_output_tokens','reasoningOutputTokens')]};usage_i=i
        if method=='item/completed' and p.get('turnId')==turn:
            item=p['item'];key=item.get('id')
            if key in ids:continue
            ids.add(key)
            if item['type']=='commandExecution':
                commands.append(dict(command=item['command'],aggregated_output=item.get('aggregatedOutput')or'',exit_code=item.get('exitCode'),duration_ms=item.get('durationMs')));last_item=i
            if item['type']=='agentMessage':
                try:answer=json.loads(item['text']);last_item=i
                except ValueError:pass
        if method=='turn/completed' and p['turn']['id']==turn:terminal=p['turn'];errors+=[terminal['error']] if terminal.get('error') else []
        if method=='error':errors.append(p)
    complete=terminal is not None and usage is not None and usage_i>=last_item
    return dict(commands=commands,answer=answer,usage=usage,usage_complete=complete,errors=errors,terminal=terminal,
                usage_event_index=usage_i,last_item_event_index=last_item)

def episode(directory,cwd,common,prompt,schema,enabled,preflight=False):
    attach=False
    c=Client(directory,cwd,enabled);thread=None;turn=None;failure=None
    try:
        c.rpc('initialize',dict(clientInfo=dict(name='token-router-gate-eval',version='1.1'),capabilities=dict(experimentalApi=True)));c.send(dict(method='initialized'))
        skills=c.rpc('skills/list',dict(cwds=[str(c.cwd)],forceReload=True));names=[s['name']for entry in skills['data']for s in entry['skills']if s.get('enabled')]
        assert names==(['token-router']if enabled else[]),names
        (c.d/'skills-audit.json').write_text(json.dumps(skills,indent=2)+'\n')
        reply=c.rpc('thread/start',dict(model='gpt-6.1-sol',modelProvider='openai',cwd=str(c.cwd),approvalPolicy='never',sandbox='read-only',ephemeral=True,baseInstructions=common,developerInstructions=''))
        assert reply['model']=='gpt-6.1-sol' and reply['modelProvider']=='openai' and reply['sandbox']['type']=='readOnly'
        thread=reply['thread']['id'];(c.d/'thread-start.json').write_text(json.dumps(reply,indent=2)+'\n')
        if not preflight:
            items=[dict(type='text',text=prompt)]
            if attach:items.append(dict(type='skill',name='token-router',path=str(c.cwd/'.agents/skills/token-router/SKILL.md')))
            reply=c.rpc('turn/start',dict(threadId=thread,input=items,model='gpt-6.1-sol',effort='medium',outputSchema=schema));turn=reply['turn']['id']
            while True:
                e=c.next()
                if e.get('method')=='turn/completed' and e['params']['turn']['id']==turn:break
    except Exception as exc:
        failure=type(exc).__name__+':'+str(exc)
        if turn:
            try:
                c.grace=True;c.send(dict(id=10000,method='turn/interrupt',params=dict(threadId=thread,turnId=turn)))
                end=time.monotonic()+10
                while True:
                    e=c.next(end)
                    if e.get('method')=='turn/completed':break
            except Exception:pass
    finally:c.close()
    data=reconcile(c.events,thread,turn);complete=data.pop('usage_complete')and c.drain_complete and not c.truncated
    terminal=data.pop('terminal');success=terminal is not None and terminal['status']=='completed' and failure is None
    if preflight:success=failure is None
    if failure:data['errors'].append(failure)
    wall=time.monotonic()-c.start;cpu=c.cpu()-c.cpu0
    return dict(**data,events=c.events,usage_complete=complete,wall=wall,cpu=cpu,remote_wait_proxy=max(0,wall-cpu),termination_reason=failure,capture_truncated=c.truncated,drain_complete=c.drain_complete,returncode=0 if success else 1,skill_attached=attach,skill_enabled=enabled)

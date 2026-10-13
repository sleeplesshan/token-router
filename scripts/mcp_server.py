#!/usr/bin/env python3
"""Small synchronous stdio MCP adapter for guarded local pytest-log retrieval."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

VERSIONS=('2025-11-25','2025-06-18','2025-03-26','2024-11-05')
MAX_REQUEST=65536
TOOL='read_pytest_failures'
DESCRIPTION=('Read complete dispersed pytest failure blocks plus distant final results from a local log. '
             'Use only when at least two known distinct failure headers need surrounding context. '
             'Skip single tracebacks, code, literal-only questions and evidence already visible. '
             'Returns original numbered source, not semantic conclusions; a rejection requires ordinary targeted reading.')
SCHEMA={'type':'object','properties':{'path':{'type':'string'},'failure_headers':{'type':'array','items':{'type':'string','maxLength':256},'minItems':2,'maxItems':8,'uniqueItems':True},'result_term':{'type':'string','default':' failed','maxLength':256}},'required':['path','failure_headers'],'additionalProperties':False}

def failure(code):
    return {'isError':True,'content':[{'type':'text','text':json.dumps({'status':'not_returned','reason':code,'next_action':'ordinary_targeted_read'})}]}

def literal(value):
    return isinstance(value,str) and bool(value.strip()) and len(value)<=256 and not any(c in value for c in ('\n','\r','\0'))

class Server:
    def __init__(self,roots):
        self.roots=tuple(Path(p).expanduser().resolve(strict=True) for p in roots)
        if not self.roots or any(not p.is_dir() for p in self.roots):raise ValueError('invalid allowed root')
        self.initialized=False
    def source(self,value):
        if not isinstance(value,str) or not value or len(value)>4096 or '\0' in value:raise ValueError('invalid path')
        p=Path(value).expanduser().resolve(strict=True)
        if p.suffix.lower() not in ('.log','.txt','.out') or not p.is_file():raise ValueError('invalid source')
        if not any(p.is_relative_to(root) for root in self.roots):raise ValueError('outside allowed roots')
        return p
    def call(self,args):
        if not isinstance(args,dict) or set(args)-{'path','failure_headers','result_term'}:return failure('invalid_arguments')
        headers=args.get('failure_headers');term=args.get('result_term',' failed')
        if not isinstance(headers,list) or not 2<=len(headers)<=8 or not all(literal(t) for t in headers) or len(set(headers))!=len(headers) or not literal(term):return failure('invalid_arguments')
        try:
            source=self.source(args.get('path'));before=source.stat()
            cmd=[sys.executable,str(Path(__file__).with_name('router.py')),'error_log',str(source)]
            for value in [*headers,term]:cmd+=['--search-term',value]
            cmd+=['--activation-profile','log-context','--line-numbers','--compact-status']
            env={k:v for k,v in os.environ.items() if not k.startswith('ROUTER_') and k not in ('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL')}
            env.update(TOKEN_ROUTER_ACTIVE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
            done=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=5,env=env)
            after=self.source(args['path'])
            stamp=lambda st:(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
            if after!=source or stamp(after.stat())!=stamp(before):return failure('source_changed')
            if done.returncode:return failure('reader_rejected')
            if not done.stdout or len(done.stdout)>12000:return failure('output_limit')
            statuses=[json.loads(line.partition('] ')[2]) for line in done.stderr.splitlines() if line.startswith('[token-router status] ')]
            if not statuses or statuses[-1].get('status')!='auto_candidates' or statuses[-1].get('activation')!='activate':return failure('reader_rejected')
            return {'isError':False,'content':[{'type':'text','text':done.stdout}]}
        except subprocess.TimeoutExpired:return failure('reader_timeout')
        except (OSError,ValueError,TypeError):return failure('invalid_or_changed_source')
    def dispatch(self,request):
        if not isinstance(request,dict) or request.get('jsonrpc')!='2.0' or not isinstance(request.get('method'),str):return error(None,-32600,'Invalid Request')
        ident=request.get('id');method=request['method'];params=request.get('params',{})
        if 'id' in request and type(ident) not in (str,int):return error(None,-32600,'Invalid request id')
        if 'id' not in request:return None
        if not isinstance(params,dict):return error(ident,-32602,'Invalid params')
        if method=='initialize':
            self.initialized=True
            result={'protocolVersion':params.get('protocolVersion') if params.get('protocolVersion') in VERSIONS else VERSIONS[0],'capabilities':{'tools':{'listChanged':False}},'serverInfo':{'name':'token-router-local','version':'0.1.0'}}
        elif method=='ping':result={}
        elif not self.initialized:return error(ident,-32000,'Initialize first')
        elif method=='tools/list':result={'tools':[{'name':TOOL,'description':DESCRIPTION,'inputSchema':SCHEMA,'annotations':{'readOnlyHint':True,'destructiveHint':False,'openWorldHint':False}}]}
        elif method=='tools/call':result=self.call(params.get('arguments')) if params.get('name')==TOOL else failure('unknown_tool')
        else:return error(ident,-32601,'Method not found')
        return {'jsonrpc':'2.0','id':ident,'result':result}

def error(ident,code,message):return {'jsonrpc':'2.0','id':ident,'error':{'code':code,'message':message}}

def serve(server,source,sink):
    while True:
        line=source.readline(MAX_REQUEST+1)
        if not line:break
        if len(line)>MAX_REQUEST:
            while line and not line.endswith(b'\n'):line=source.readline(MAX_REQUEST+1)
            response=error(None,-32600,'Request too large')
        else:
            try:response=server.dispatch(json.loads(line))
            except (ValueError,UnicodeError):response=error(None,-32700,'Parse error')
        if response is not None:sink.write(json.dumps(response,ensure_ascii=False)+'\n');sink.flush()

def default_root_allowed(cwd, home):
    return cwd.parent != cwd and cwd != home

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--allow-root',action='append',default=[]);args=parser.parse_args()
    roots=args.allow_root or [str(Path.cwd())]
    if not args.allow_root and not default_root_allowed(Path.cwd().resolve(),Path.home().resolve()):parser.error('explicit --allow-root required for home or filesystem root')
    try:server=Server(roots)
    except (OSError,ValueError):parser.error('allowed roots must be existing directories')
    serve(server,sys.stdin.buffer,sys.stdout)

if __name__=='__main__':main()

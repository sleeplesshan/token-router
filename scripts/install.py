#!/usr/bin/env python3
"""Explicit-destination, verified staging; never edits AGENTS or authentication."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid
from distribution import FILES, MARKER, inventory, read_install, verify

def smoke(root):
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    for key in list(env):
        if key.startswith('ROUTER_') or key in ('OPENAI_API_KEY','CODEX_API_KEY'):env.pop(key)
    env['ROUTER_CODEX_BIN']='token-router-no-cloud-executable'
    for args in (['--version'],['heavy_code',str(root/'samples/service.py'),'--query','retry_delay']):
        p=subprocess.run([sys.executable,str(root/'scripts/router.py'),*args],cwd=root.parent,
                         env=env,capture_output=True,text=True,timeout=20)
        if p.returncode or (args[0]!='--version' and 'return min' not in p.stdout):
            raise ValueError('Staged CLI smoke failed')

def replace(stage,dest):
    backup=None
    if dest.exists():
        backup_root=dest.parent
        if dest.parent.name=='skills' and dest.parent.parent.name in ('.agents','.codex'):
            backup_root=dest.parent.parent/'skill-backups'
            backup_root.mkdir(parents=True,exist_ok=True)
        backup=backup_root/(dest.name+'.backup-'+uuid.uuid4().hex[:12]);os.replace(dest,backup)
    try:os.replace(stage,dest)
    except BaseException:
        if backup is not None:os.replace(backup,dest)
        raise
    return backup

def install(source,dest):
    if dest.is_symlink():raise ValueError('Destination must not be a symlink')
    previous=read_install(dest) if dest.exists() else {}
    hashes=inventory(source);verify(source,hashes)
    if previous.get('codex_mcp') and 'scripts/mcp_server.py' not in hashes:
        raise ValueError('Disconnect Codex before restoring a payload without its MCP server')
    release=source/'release-manifest.json'
    if release.exists():
        manifest=json.loads(release.read_text(encoding='utf-8'));verify(source,manifest['files'])
    dest.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.'+dest.name+'-stage-',dir=dest.parent))
    try:
        for name in hashes:
            target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,target)
        record=dict(product='token-router',schema_version=1,files=hashes)
        if previous.get('codex_mcp'):record['codex_mcp']=previous['codex_mcp']
        (stage/MARKER).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        read_install(stage);smoke(stage)
        backup=replace(stage,dest)
        return dict(status='installed',destination=str(dest),backup=None if backup is None else str(backup))
    finally:
        if stage.exists():shutil.rmtree(stage)

def codex_mcp(args):
    """Use the supported CLI; never rewrite unrelated TOML or print its contents."""
    executable=shutil.which('codex')
    if not executable:raise ValueError('Codex CLI is required for connection; local installation is still usable')
    result=subprocess.run([executable,'mcp',*args],capture_output=True,text=True,encoding='utf-8',timeout=20)
    if result.returncode:
        if args[0]=='get' and "No MCP server named 'token-router' found" in result.stderr:return None
        raise ValueError('Codex MCP '+args[0]+' failed; inspect the CLI separately')
    return json.loads(result.stdout) if args[0]=='get' else None

def transport_matches(current,record):
    if not isinstance(current,dict) or not isinstance(record,dict):return False
    t=(current or {}).get('transport',{})
    return (isinstance(t,dict) and t.get('type')=='stdio' and t.get('command')==record.get('command') and
            t.get('args')==record.get('args') and not t.get('cwd') and not t.get('env') and not t.get('env_vars'))

def save_marker(dest,record):
    fd,name=tempfile.mkstemp(prefix='.token-router-record-',dir=dest.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(record,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(name,dest/MARKER)
    finally:
        if os.path.exists(name):os.unlink(name)

def connect_codex(dest,roots):
    data=read_install(dest)
    if 'scripts/mcp_server.py' not in data['files']:raise ValueError('Update the installation before connecting Codex')
    args=[str(dest/'scripts/mcp_server.py')]
    for value in roots:
        path=Path(value).expanduser().resolve()
        if not path.is_dir():raise ValueError('Allowed roots must be existing directories')
        args+=['--allow-root',str(path)]
    record=dict(command=str(Path(sys.executable).absolute()),args=args)
    current=codex_mcp(['get','token-router','--json'])
    previous=data.get('codex_mcp',{}).get('configuration')
    if previous is not None and current is not None and current!=previous:
        raise ValueError('Managed Codex server settings changed; preserve them and reconfigure explicitly')
    if current and not transport_matches(current,record):
        raise ValueError('Existing token-router MCP configuration differs; preserve it and disconnect/reconfigure explicitly')
    created=current is None
    if created:codex_mcp(['add','token-router','--',record['command'],*args])
    try:
        actual=codex_mcp(['get','token-router','--json'])
        if not transport_matches(actual,record):raise ValueError('Codex registration verification failed')
        if actual.get('enabled',True) is not True or actual.get('disabled_reason'):
            raise ValueError('Codex server is disabled; enable it in Codex settings before connecting')
        allowed=actual.get('enabled_tools');denied=actual.get('disabled_tools') or []
        if (allowed is not None and 'read_pytest_failures' not in allowed) or 'read_pytest_failures' in denied:
            raise ValueError('Codex tool filters exclude read_pytest_failures; preserve or update them explicitly')
        record['configuration']=actual
        data['codex_mcp']=record;save_marker(dest,data)
    except BaseException:
        if created:codex_mcp(['remove','token-router'])
        raise
    return dict(status='connected',server='token-router',scope='startup_workspace' if not roots else 'explicit_roots',restart_required=True)

def disconnect_codex(dest):
    data=read_install(dest);record=data.get('codex_mcp')
    if not record:raise ValueError('No managed Codex connection; use Codex settings for a manually registered server')
    current=codex_mcp(['get','token-router','--json'])
    if current:
        if not transport_matches(current,record):raise ValueError('Codex server was changed; preserve it and disconnect manually')
        if record.get('configuration') is not None and current!=record['configuration']:
            raise ValueError('Codex server settings were changed; preserve them and disconnect manually')
        codex_mcp(['remove','token-router'])
    data.pop('codex_mcp');save_marker(dest,data)
    return dict(status='disconnected',server='token-router',restart_required=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('install','update','restore','uninstall','verify','connect-codex','disconnect-codex'))
    p.add_argument('--dest',type=Path,required=True);p.add_argument('--backup',type=Path)
    p.add_argument('--connect-codex',action='store_true',help='Register the installed local read-only tool with Codex')
    p.add_argument('--allow-root',action='append',default=[],help='Explicit MCP root; default follows each local Codex workspace')
    a=p.parse_args();dest=a.dest.expanduser().absolute();source=Path(__file__).resolve().parents[1]
    try:
        if a.connect_codex and a.action not in ('install','update'):raise ValueError('--connect-codex requires install/update')
        if a.allow_root and not (a.connect_codex or a.action=='connect-codex'):raise ValueError('--allow-root requires Codex connection')
        if dest==dest.parent or dest.resolve()==Path.home().resolve():raise ValueError('Unsafe destination')
        if a.action in ('install','update'):
            if dest.resolve()==source or source in dest.resolve().parents:raise ValueError('Choose a destination outside the source checkout')
            if a.action=='update' and not dest.exists():raise ValueError('Update requires an existing managed installation')
            result=install(source,dest)
            if a.connect_codex:
                try:result['codex']=connect_codex(dest,a.allow_root)
                except (OSError,ValueError,subprocess.SubprocessError) as exc:
                    print(json.dumps(dict(status='installed_connection_failed',installation=result,
                                          next_action='connect-codex --dest '+str(dest),reason=str(exc))),file=sys.stderr)
                    return 1
        elif a.action=='restore':
            if a.backup is None:raise ValueError('restore requires --backup')
            backup=a.backup.expanduser().absolute();read_install(backup)
            result=install(backup,dest)
        elif a.action=='connect-codex':result=connect_codex(dest,a.allow_root)
        elif a.action=='disconnect-codex':result=disconnect_codex(dest)
        else:
            read_install(dest)
            if a.action=='uninstall':
                if read_install(dest).get('codex_mcp'):disconnect_codex(dest)
                shutil.rmtree(dest)
            result=dict(status=a.action+'ed',destination=str(dest))
        print(json.dumps(result));return 0
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        print(json.dumps(dict(status='error',reason=str(exc))),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""Explicit-destination, verified staging; never edits AGENTS or authentication."""
import argparse
import json
import os
import queue
import threading
import time
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

class CodexConfigError(RuntimeError):
    """Safe diagnostic without server/config contents."""


class ConfigRPC:
    def __init__(self, command=None, *, env=None, timeout=10, total_timeout=25):
        self.deadline = time.monotonic() + total_timeout
        self.timeout = timeout
        self.seq = 0
        self.q = queue.Queue()
        self.process = subprocess.Popen(command or ['codex', 'app-server', '--stdio'],
            env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        def reader():
            size = 0
            try:
                while True:
                    line = self.process.stdout.readline(4_000_001)
                    if not line:
                        self.q.put(None)
                        return
                    size += len(line)
                    if size > 4_000_000:
                        self.q.put(CodexConfigError('response_limit'))
                        return
                    self.q.put(line)
            except OSError:
                self.q.put(CodexConfigError('read_failed'))
        self.reader = threading.Thread(target=reader, daemon=True)
        self.reader.start()
        try:
            self.call('initialize', {'clientInfo': {'name': 'token-router-config', 'version': '1'}})
            self._send({'method': 'initialized'})
        except Exception:
            self.close()
            raise

    def _send(self, value):
        data = (json.dumps(value) + '\n').encode()
        if len(data) > 65536:
            raise CodexConfigError('request_limit')
        # Config requests are small; a writer thread also bounds an unresponsive pipe.
        outcome = queue.Queue()
        def write():
            try:
                self.process.stdin.write(data)
                self.process.stdin.flush()
                outcome.put(None)
            except (OSError, ValueError):
                outcome.put(CodexConfigError('write_failed'))
        threading.Thread(target=write, daemon=True).start()
        try:
            result = outcome.get(timeout=max(.001, min(self.timeout, self.deadline-time.monotonic())))
        except queue.Empty:
            raise CodexConfigError('timeout') from None
        if result:
            raise result

    def call(self, method, params):
        if method not in ('initialize', 'config/read', 'config/value/write'):
            raise CodexConfigError('unsupported_method')
        self.seq += 1
        self._send({'id': self.seq, 'method': method, 'params': params})
        deadline = min(self.deadline, time.monotonic() + self.timeout)
        while True:
            try:
                raw = self.q.get(timeout=max(.001, deadline-time.monotonic()))
            except queue.Empty:
                raise CodexConfigError('timeout') from None
            if raw is None:
                raise CodexConfigError('unexpected_eof')
            if isinstance(raw, Exception):
                raise raw
            try:
                reply = json.loads(raw)
            except (ValueError, UnicodeError):
                raise CodexConfigError('malformed_response') from None
            if not isinstance(reply, dict):
                raise CodexConfigError('malformed_response')
            if reply.get('id') == self.seq:
                if 'error' in reply:
                    raise CodexConfigError('rpc_error')
                if 'result' not in reply:
                    raise CodexConfigError('malformed_response')
                return reply['result']
            if time.monotonic() >= deadline:
                raise CodexConfigError('timeout')

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=2)
        self.reader.join(timeout=1)
        self.process.stdin.close()
        self.process.stdout.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def read_codex_slot(rpc=None):
    """Return token-router user slot (possibly None) and file/version CAS metadata."""
    if rpc is None:
        with ConfigRPC() as client:
            return read_codex_slot(client)
    result = rpc.call('config/read', {'includeLayers': True})
    try:
        layers = [x for x in result['layers'] if x['name']['type'] == 'user'
                  and not x['name'].get('profile') and not x.get('disabledReason')]
        if len(layers) != 1:
            raise CodexConfigError('ambiguous_user_layer')
        layer = layers[0]
        server = layer['config'].get('mcp_servers', {}).get('token-router')
        if (server is not None and not isinstance(server, dict)) or not isinstance(layer['version'], str) or not isinstance(layer['name']['file'], str):
            raise CodexConfigError('invalid_user_layer')
        effective=result.get('config',{}).get('mcp_servers',{}).get('token-router',{})
        return {'server': server, 'filePath': layer['name']['file'], 'version': layer['version'],
                'effective_omit_tools_from':effective.get('omit_tools_from')}
    except (KeyError, TypeError, AttributeError):
        raise CodexConfigError('invalid_user_layer') from None


def read_codex_server(rpc=None):
    """Compatibility view: absent server returns None."""
    slot = read_codex_slot(rpc)
    return slot if slot['server'] is not None else None


def write_codex_slot(expected_server, value, rpc=None):
    """Compare the exact user slot, then CAS-write only that server key."""
    if rpc is None:
        with ConfigRPC() as client:
            return write_codex_slot(expected_server, value, client)
    slot = read_codex_slot(rpc)
    if slot['server'] != expected_server:
        raise CodexConfigError('server_changed')
    result = rpc.call('config/value/write', {
        'keyPath': 'mcp_servers.token-router', 'value': value,
        'mergeStrategy': 'replace', 'filePath': slot['filePath'],
        'expectedVersion': slot['version']})
    if result.get('status') != 'ok':
        raise CodexConfigError('config_write_overridden')
    return True


def set_direct_exposure(expected_server, rpc=None):
    """CAS-write the single exposure key after exact caller-owned stdio matching."""
    if rpc is None:
        with ConfigRPC() as client:
            return set_direct_exposure(expected_server, client)
    record = read_codex_server(rpc)
    if not record or not isinstance(expected_server, dict):
        raise CodexConfigError('server_not_owned')
    server = record['server']
    if (not isinstance(expected_server.get('command'), str)
            or not isinstance(expected_server.get('args'), list)
            or not all(isinstance(x, str) for x in expected_server['args'])
            or any(server.get(k) != expected_server.get(k) for k in ('command', 'args'))
            or server.get('url') is not None):
        raise CodexConfigError('server_not_owned')
    if server.get('omit_tools_from') not in (None, ['deferred']):
        raise CodexConfigError('exposure_setting_changed')
    if server.get('omit_tools_from') == ['deferred']:
        return True
    written=rpc.call('config/value/write', {'keyPath': 'mcp_servers.token-router.omit_tools_from',
        'value': ['deferred'], 'mergeStrategy': 'replace', 'filePath': record['filePath'],
        'expectedVersion': record['version']})
    if written.get('status')!='ok':raise CodexConfigError('config_write_overridden')
    return True


def codex_mcp(args):
    """Use the supported CLI; never rewrite unrelated TOML or print its contents."""
    if args != ['get','token-router','--json']:
        raise ValueError('Only read-only Codex MCP inspection is supported')
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

def validate_codex_tool_policy(current):
    if current.get('enabled',True) is not True or current.get('disabled_reason'):
        raise ValueError('Codex server is disabled; enable it in Codex settings before connecting')
    allowed=current.get('enabled_tools');denied=current.get('disabled_tools') or []
    if (allowed is not None and 'read_pytest_failures' not in allowed) or 'read_pytest_failures' in denied:
        raise ValueError('Codex tool filters exclude read_pytest_failures; preserve or update them explicitly')

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
    if current:validate_codex_tool_policy(current)
    created=current is None
    rollback_user=None
    created_configuration=None
    created_written=False
    try:
        if created:
            # Include exposure in the single creation; do not rewrite other servers.
            rollback_user=dict(record, omit_tools_from=['deferred'])
            write_codex_slot(None, rollback_user)
            created_written=True
            created_configuration=codex_mcp(['get','token-router','--json'])
        user_record=read_codex_server()
        previous_user=data.get('codex_mcp',{}).get('user_configuration')
        if not created and previous_user is not None and (user_record is None or user_record['server']!=previous_user):
            raise ValueError('Codex server exposure or user settings changed; preserve them and reconfigure explicitly')
        set_direct_exposure(record)
        if rollback_user is not None:rollback_user['omit_tools_from']=['deferred']
        user_record=read_codex_server()
        if (not user_record or user_record['server'].get('omit_tools_from')!=['deferred']
                or user_record.get('effective_omit_tools_from')!=['deferred']):
            raise ValueError('Direct tool exposure was not enabled')
        actual=codex_mcp(['get','token-router','--json'])
        if not transport_matches(actual,record):raise ValueError('Codex registration verification failed')
        validate_codex_tool_policy(actual)
        record['configuration']=actual
        record['user_configuration']=user_record['server']
        data['codex_mcp']=record;save_marker(dest,data)
    except BaseException:
        # Do not remove a registration another process modified during setup.
        if created_written and created_configuration is not None:
            try:
                actual=codex_mcp(['get','token-router','--json'])
                user_record=read_codex_server()
                if actual==created_configuration and user_record and user_record['server']==rollback_user:
                    write_codex_slot(rollback_user, None)
            except Exception:
                # Unknown/concurrent state is preserved; retain the original failure.
                pass
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
        previous_user=record.get('user_configuration')
        user_record=read_codex_server()
        if previous_user is not None:
            if user_record is None or user_record['server']!=previous_user:
                raise ValueError('Codex exposure or user settings were changed; preserve them and disconnect manually')
        if user_record is None:
            raise ValueError('Codex server is not in the owned user layer')
        write_codex_slot(user_record['server'], None)
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
                except (OSError,ValueError,CodexConfigError,subprocess.SubprocessError) as exc:
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
    except (OSError,ValueError,CodexConfigError,subprocess.SubprocessError) as exc:
        print(json.dumps(dict(status='error',reason=str(exc))),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())

"""Archive-only install/read/update/restore/uninstall; no cloud access."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

def run(*args,cwd,env):
    p=subprocess.run([sys.executable,*map(str,args)],cwd=cwd,env=env,text=True,capture_output=True,timeout=30)
    if p.returncode:raise AssertionError((args,p.returncode,p.stderr))
    return p.stdout

def main(archive):
    with tempfile.TemporaryDirectory(prefix='router archive 한글 ') as tmp:
        root=Path(tmp);unpack=root/'unpacked';unpack.mkdir()
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                if not name.startswith('token-router/') or '..' in Path(name).parts:raise ValueError('Unsafe archive path')
            z.extractall(unpack)
        source=unpack/'token-router';manifest=json.loads((source/'release-manifest.json').read_text(encoding='utf-8'))
        for name,digest in manifest['files'].items():assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest
        env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONUTF8']='1';env['PATH']=''
        for key in list(env):
            if key.startswith('ROUTER_') or key in ('OPENAI_API_KEY','CODEX_API_KEY'):env.pop(key)
        dest=root/'isolated skills/token-router';installer=source/'scripts/install.py'
        run(installer,'install','--dest',dest,cwd=root,env=env)
        router=dest/'scripts/router.py';assert manifest['version'] in run(router,'--version',cwd=root,env=env)
        run(router,'--help',cwd=root,env=env)
        for mode,name,q in [('heavy_code','service.py','retry_delay'),('error_log','incident.log','payment_timeout'),('agent_context','reference.md','rollback')]:
            path=dest/'samples'/name;before=path.read_bytes();path.chmod(0o444)
            try:output=run(router,mode,path,'--query',q,cwd=root,env=env);assert q in output;assert path.read_bytes()==before
            finally:path.chmod(0o644)
        large=root/'return sample.py'
        large.write_text('# neutral padding abcdefghijklmnopqrstuvwxyz\n'*1500+'def lookup():\n    \"\"\"\n'+'    documentation\n'*40+'    \"\"\"\n    return stored_value\n'+'# neutral padding abcdefghijklmnopqrstuvwxyz\n'*1500,encoding='utf-8')
        base=run(router,'heavy_code',large,'--query','lookup',cwd=root,env=env)
        bounded=run(router,'heavy_code',large,'--query','lookup','--return-context','bounded',cwd=root,env=env)
        target=run(router,'heavy_code',large,'--query','lookup','--return-target','lookup',cwd=root,env=env)
        assert 'return stored_value' not in base and 'return stored_value' in bounded and target==bounded
        # The archive must ship the numbered literal reader and explicit scope.
        incident=root/'literal incident.log'
        incident.write_text('neutral padding\n'*100+'ERROR: worker\nTraceback (most recent call last):\n  File "worker.py", line 7\nValueError: failed\n'+'neutral padding\n'*100,encoding='utf-8')
        literal=run(router,'error_log',incident,'--search-term','File "worker.py"','--search-context','0','--line-numbers',cwd=root,env=env)
        assert '102: Traceback' in literal and '104: ValueError: failed' in literal
        assert 'neutral padding' not in literal
        result=json.loads(run(installer,'update','--dest',dest,cwd=root,env=env));assert Path(result['backup']).is_dir()
        run(installer,'restore','--dest',dest,'--backup',result['backup'],cwd=root,env=env)
        run(installer,'uninstall','--dest',dest,cwd=root,env=env);assert not dest.exists();assert Path(result['backup']).exists()
        print(json.dumps(dict(status='PASS',version=manifest['version'],source_commit=manifest['source_commit'],archive_sha256=hashlib.sha256(Path(archive).read_bytes()).hexdigest(),cloud_calls=0,credential_required=False,other_cwd=True,unicode_space_paths=True,read_only_source=True,update_restore_remove=True)))
if __name__=='__main__':main(sys.argv[1])

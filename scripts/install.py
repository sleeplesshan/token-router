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
    if dest.exists():read_install(dest)
    hashes=inventory(source);verify(source,hashes)
    release=source/'release-manifest.json'
    if release.exists():
        manifest=json.loads(release.read_text(encoding='utf-8'));verify(source,manifest['files'])
    dest.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.'+dest.name+'-stage-',dir=dest.parent))
    try:
        for name in FILES:
            target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,target)
        (stage/MARKER).write_text(json.dumps(dict(product='token-router',schema_version=1,files=hashes),indent=2)+'\n',encoding='utf-8')
        read_install(stage);smoke(stage)
        backup=replace(stage,dest)
        return dict(status='installed',destination=str(dest),backup=None if backup is None else str(backup))
    finally:
        if stage.exists():shutil.rmtree(stage)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('install','update','restore','uninstall','verify'))
    p.add_argument('--dest',type=Path,required=True);p.add_argument('--backup',type=Path)
    a=p.parse_args();dest=a.dest.expanduser().absolute();source=Path(__file__).resolve().parents[1]
    try:
        if dest==dest.parent or dest.resolve()==Path.home().resolve():raise ValueError('Unsafe destination')
        if a.action in ('install','update'):
            if dest.resolve()==source or source in dest.resolve().parents:raise ValueError('Choose a destination outside the source checkout')
            if a.action=='update' and not dest.exists():raise ValueError('Update requires an existing managed installation')
            result=install(source,dest)
        elif a.action=='restore':
            if a.backup is None:raise ValueError('restore requires --backup')
            backup=a.backup.expanduser().absolute();read_install(backup)
            result=install(backup,dest)
        else:
            read_install(dest)
            if a.action=='uninstall':shutil.rmtree(dest)
            result=dict(status=a.action+'ed',destination=str(dest))
        print(json.dumps(result));return 0
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        print(json.dumps(dict(status='error',reason=str(exc))),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""Build a deterministic allowlisted zip from a clean Git commit, no model/network."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile
from distribution import FILES

def build(repo,out):
    for cmd in (['git','diff','--quiet'],['git','diff','--cached','--quiet']):
        subprocess.run(cmd,cwd=repo,check=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    payload={name:subprocess.check_output(['git','show',commit+':'+name],cwd=repo) for name in FILES}
    version=re.search(rb'VERSION = "([^"]+)"',payload['scripts/router.py']).group(1).decode()
    hashes={name:hashlib.sha256(data).hexdigest() for name,data in payload.items()}
    manifest=dict(schema_version=1,product='token-router',version=version,source_commit=commit,files=hashes)
    payload['release-manifest.json']=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()
    out.mkdir(parents=True,exist_ok=True);archive=out/('token-router-'+version+'.zip')
    if archive.exists():raise ValueError('Refusing to overwrite archive')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(payload.items()):
            info=zipfile.ZipInfo('token-router/'+name,date_time=(2020,1,1,0,0,0));info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data,compresslevel=9)
    digest=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n')
    (out/'release-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(archive);print(digest)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(Path(__file__).resolve().parents[1],a.output)

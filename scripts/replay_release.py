#!/usr/bin/env python3
"""Replay pinned local packets. No model calls; downloads only with --fetch."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODULES = ('router.py', 'evidence_checks.py', 'query_matcher.py', 'routing_policy.py', 'source_guard.py')
BASELINE = '1737ae2c360c1b495f627cf61f51b20f27ea806b'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workdir',type=Path,required=True)
    p.add_argument('--fetch',action='store_true',help='Download exact pinned third-party sources; review their licenses')
    a=p.parse_args();work=a.workdir.resolve();work.mkdir(parents=True,exist_ok=True)
    if (work/'mixed-results.json').exists():p.error('Use a fresh workdir; existing results are never replaced')
    manifest=(ROOT/'docs/release-evaluation/mixed-manifest.json').read_bytes()
    m=json.loads(manifest)
    for source in m['sources']:
        path=work/source['file']
        if not path.exists():
            if not a.fetch:p.error('Missing source; supply pinned files or use --fetch: '+source['file'])
            path.parent.mkdir(parents=True,exist_ok=True)
            with urllib.request.urlopen(source['url'],timeout=60) as response:data=response.read()
            if hashlib.sha256(data).hexdigest()!=source['sha256']:raise ValueError('Downloaded source hash mismatch')
            path.write_bytes(data)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:raise ValueError('Source hash mismatch: '+source['file'])
    (work/'mixed-manifest.json').write_bytes(manifest)
    base=work/'baseline/scripts';base.mkdir(parents=True,exist_ok=True)
    for name in MODULES:
        data=subprocess.check_output(['git','show',BASELINE+':scripts/'+name],cwd=ROOT)
        (base/name).write_bytes(data)
    worker=(ROOT/'docs/release-evaluation/replay_worker.py').read_text(encoding='utf-8')
    (work/'mixed.py').write_text(worker,encoding='utf-8')
    import os
    env=os.environ.copy();env['TOKEN_ROUTER_REPO']=str(ROOT)
    subprocess.run([sys.executable,str(work/'mixed.py')],env=env,check=True)
    (work/'replay-provenance.json').write_text(json.dumps({'package_version':subprocess.check_output([sys.executable,str(ROOT/'scripts/router.py'),'--version'],text=True).strip(),'policy_version':'v2.4','baseline':BASELINE,'candidate_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'model':'none','manifest_sha256':hashlib.sha256(manifest).hexdigest()},indent=2)+'\n')
if __name__=='__main__':main()

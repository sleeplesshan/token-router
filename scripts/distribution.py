"""Small explicit runtime payload; research artifacts never enter installations."""
from pathlib import Path
import hashlib
import json

FILES = (
    'README.md', 'SKILL.md', 'CLAUDE.md', 'LICENSE', 'SECURITY.md', 'SUPPORT.md',
    'CHANGELOG.md', 'agents/openai.yaml', 'references/contract.md',
    'scripts/router.py', 'scripts/evidence_checks.py', 'scripts/query_matcher.py',
    'scripts/routing_policy.py', 'scripts/source_guard.py',
    'scripts/install.py', 'scripts/distribution.py',
    'samples/service.py', 'samples/incident.log', 'samples/reference.md',
)
MARKER = '.token-router-install.json'

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inventory(root):
    return {name:digest(root/name) for name in FILES}

def verify(root, hashes):
    if set(hashes) != set(FILES):
        raise ValueError('Unknown installation inventory; use a separate destination for migration')
    for name, expected in hashes.items():
        path=root/name
        if any(p.is_symlink() for p in [path,*path.parents] if p == root or root in p.parents):
            raise ValueError('Symlinks are not managed: '+name)
        if not path.is_file() or digest(path)!=expected:
            raise ValueError('Missing or modified managed file: '+name)

def read_install(root):
    if root.is_symlink() or not (root/MARKER).is_file():
        raise ValueError('Destination is not a managed token-router installation')
    data=json.loads((root/MARKER).read_text(encoding='utf-8'))
    if data.get('product')!='token-router' or data.get('schema_version')!=1:
        raise ValueError('Unsupported installation marker')
    verify(root,data['files'])
    allowed=set(FILES)|{MARKER}
    for path in root.rglob('*'):
        rel=path.relative_to(root).as_posix()
        if path.is_symlink():raise ValueError('Unmanaged symlink: '+rel)
        if path.is_dir() and rel != 'scripts/__pycache__' and not any(n.startswith(rel+'/') for n in FILES):
            raise ValueError('Unmanaged directory: '+rel)
        if path.is_file() and rel not in allowed:
            # Python-generated sibling module caches only, never arbitrary extras.
            cache_ok=(path.parent==root/'scripts/__pycache__' and path.suffix=='.pyc'
                      and 'scripts/'+path.name.split('.')[0]+'.py' in FILES)
            if not cache_ok:raise ValueError('Unmanaged file (preserve/move it first): '+rel)
    return data

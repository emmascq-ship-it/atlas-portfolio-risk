"""Fail-closed audit of the synthetic-only Pages publication directory."""
import hashlib
import json
from pathlib import Path
import re
from risk_engine import generate_synthetic_prices
from static_dashboard import dashboard_payload

ROOT = Path(__file__).resolve().parent


def audit_public(directory=None):
    folder = Path(directory) if directory else ROOT / 'docs'
    expected = {'index.html', '.nojekyll'}
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('Public directory must be a real local directory')
    if {p.name for p in folder.iterdir()} != expected:
        raise ValueError('Public directory must contain only index.html and .nojekyll')
    if any(p.is_symlink() or not p.is_file() for p in folder.iterdir()):
        raise ValueError('Public symlinks and directories are prohibited')
    text = (folder / 'index.html').read_text(encoding='utf-8')
    if re.search(r'<(?:script|link)\b[^>]*(?:src|href)\s*=\s*[\"\x27]https?://', text, re.I):
        raise ValueError('Public demo must not load external scripts or styles')
    if re.search(r'\bsk-proj-[A-Za-z0-9_-]{20,}|\bAKIA[0-9A-Z]{16}\b|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', text):
        raise ValueError('Credential-like material detected')
    if text.count('const DATA = ') != 1:
        raise ValueError('Expected one auditable research payload')
    payload, _ = json.JSONDecoder().raw_decode(text.split('const DATA = ',1)[1])
    expected_payload = json.loads(json.dumps(dashboard_payload(generate_synthetic_prices())))
    if payload != expected_payload or payload.get('synthetic') is not True:
        raise ValueError('Public payload differs from the reproducible synthetic baseline')
    if (folder / '.nojekyll').stat().st_size:
        raise ValueError('.nojekyll must be empty')
    return {'status':'PASSED', 'files':sorted(expected), 'source':'Synthetic only',
            'html_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'scope':'Allowlist, symlinks, external dependencies, credential patterns and exact synthetic payload; not a general secret-scanner certification'}


if __name__ == '__main__':
    print(json.dumps(audit_public(),indent=2))

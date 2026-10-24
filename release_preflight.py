"""Local, no-network pre-publication gate for ATLAS.

Usage:
    python release_preflight.py
    python release_preflight.py --browser  # needs Playwright and Chromium

This script does not certify live market-data accuracy or production readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from public_audit import audit_public

ROOT = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*command: str) -> None:
    print('RUN:', ' '.join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description='Offline unit, artifact, and publication preflight')
    parser.add_argument('--browser', action='store_true', help='Also run real browser smoke checks')
    args = parser.parse_args()
    audit_public()

    prohibited = (ROOT / '.env', ROOT / '.streamlit' / 'secrets.toml')
    exposed = [str(p.relative_to(ROOT)) for p in prohibited if p.exists()]
    if exposed:
        raise RuntimeError('Potential credentials file in release directory: ' + ', '.join(exposed))
    published = ROOT / 'docs'
    unexpected = [str(p.relative_to(published)) for p in published.rglob('*')
                  if p.is_file() and p.name not in ('.nojekyll', 'index.html')]
    if unexpected:
        raise RuntimeError('Unexpected public docs files (review before deployment): ' + ', '.join(unexpected))

    run(sys.executable, '-m', 'compileall', '-q', 'risk_engine.py', 'model_benchmark.py',
        'publish_demo.py', 'static_dashboard.py', 'research_packet.py')
    run(sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-q')

    with tempfile.TemporaryDirectory() as work:
        folder = Path(work)
        run(sys.executable, 'demo_cli.py', '--output-dir', str(folder / 'output'))
        run(sys.executable, 'publish_demo.py', '--output', str(folder / 'index.html'))
        packet = json.loads((folder / 'output' / 'research_packet_UNAPPROVED.json').read_text())
        review = json.loads((folder / 'output' / 'review_bundle_UNAPPROVED.json').read_text())
        html = (folder / 'index.html').read_text(encoding='utf-8')
        assert packet['approval_status'] == 'UNAPPROVED_RESEARCH'
        assert review['status'] == 'UNAPPROVED_DRAFT'
        assert packet['data_quality']['input_controls_passed'] == 8
        assert packet['backtest']['observations'] == 649
        assert abs(packet['scenario']['portfolio_return'] - (-0.13045)) < 1e-12
        assert 'UNAPPROVED RESEARCH DEMO' in html and 'Synthetic demo' in html
        assert '<script src="https://' not in html and '<script src="http://' not in html
        shipped = published / 'index.html'
        if not shipped.exists() or digest(shipped) != digest(folder / 'index.html'):
            raise AssertionError('Public docs/index.html is stale; run python publish_demo.py')
        print('SYNTHETIC RELEASE: 8 input controls; 649 backtest observations; '
              '-13.045% baseline; no external JS; draft-only approval; reproducible HTML SHA-256: '
              + digest(shipped), flush=True)

    if args.browser:
        run(sys.executable, 'tests/browser_smoke_v6.py')
        run(sys.executable, 'tests/browser_smoke_v7.py')
        run(sys.executable, 'tests/browser_streamlit.py')
    print('PASS: offline preflight complete. Live Streamlit and market API remain unverified.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

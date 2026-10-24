"""Compare synthetic HTML from two clean installs with the workspace artifact.

Run with Python 3.12. Environments and logs are confined to the requested work dir.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work-dir', required=True, type=Path)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        raise SystemExit('Reproducible build is supported on Python 3.12')
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    digests = []
    for name in ('fresh-a', 'fresh-b'):
        env = work / name
        if env.exists():
            raise SystemExit(f'Refusing to reuse an existing environment: {env}')
        venv.EnvBuilder(with_pip=True).create(env)
        python = env / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        with (work / f'{name}.log').open('w') as log:
            subprocess.run([str(python), '-m', 'pip', 'install', '--no-cache-dir',
                            '-r', str(ROOT / 'requirements-static.txt')],
                           cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
            target = work / f'{name}.html'
            subprocess.run([str(python), 'publish_demo.py', '--output', str(target)],
                           cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
            subprocess.run([str(python), '-m', 'pip', 'freeze'], stdout=log, check=True)
        digests.append(hashlib.sha256(target.read_bytes()).hexdigest())
    shipped = hashlib.sha256((ROOT / 'docs/index.html').read_bytes()).hexdigest()
    if digests[0] != digests[1] or digests[0] != shipped:
        raise SystemExit(f'Artifact mismatch: fresh={digests}, workspace={shipped}')
    print('PASS: two fresh installs and workspace HTML match SHA-256 ' + shipped)


if __name__ == '__main__':
    main()

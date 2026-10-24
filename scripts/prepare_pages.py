"""Stage audited synthetic Pages files locally. No remote publishing or network."""
import argparse
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from public_audit import audit_public, ROOT

p=argparse.ArgumentParser()
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
report=audit_public()
if a.output.exists():
    raise SystemExit('Choose a new staging directory; existing directories are never overwritten')
a.output.mkdir(parents=True)
for name in report['files']:
    shutil.copyfile(ROOT/'docs'/name,a.output/name)
print(json.dumps(report,indent=2))

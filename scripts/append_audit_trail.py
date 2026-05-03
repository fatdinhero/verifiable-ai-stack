#!/usr/bin/env python3
import sys, yaml, subprocess
from pathlib import Path
from datetime import datetime
p = Path(sys.argv[1])
with open(p) as f: data = yaml.safe_load(f)
sha = subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip()
entry = {"timestamp": datetime.utcnow().isoformat(), "commit_sha": sha,
         "reason": sys.argv[2] if len(sys.argv)>2 else "manual update", "actor": "Fatih Dinc"}
data.setdefault("audit_trail", []).append(entry)
with open(p, "w") as f: yaml.dump(data, f, default_flow_style=False, sort_keys=False)
print(f"Audit: {entry['timestamp']}")

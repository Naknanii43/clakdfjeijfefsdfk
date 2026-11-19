#!/usr/bin/env python3
"""Renders a single POKE of every bank and writes tools/levels.json so that all
banks hit at a similar loudness (momentary RMS)."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import render
TRIM = {"METAL": 0.6, "CLANK": 0.65}  # keep in sync with presets.write
CATS = [l.split()[1] for l in open(os.path.join(os.path.dirname(__file__), "..", "ClonkGoblin", "banks.txt")).read().split(";\n") if l.strip()]
TARGET = 0.30
out = "/tmp/claude-0/cal"
lv_path = os.path.join(os.path.dirname(__file__), "levels.json")
old = json.load(open(lv_path)) if os.path.exists(lv_path) else {}
n = int(sys.argv[1]) if len(sys.argv) > 1 else 520
new = {}
for b in range(n):
    _, x, log = render.render(out, b, secs=1.2, msgs=r"\; cg-poke bang", run=0)
    m = x.mean(axis=1)
    win = 480
    k = len(m) // win
    mom = np.sqrt((m[:k*win].reshape(k, win) ** 2).mean(axis=1)).max()
    cur = old.get(str(b), 1.0)
    # mom was measured with lvl = cur * trim; store the untrimmed level
    g = cur * TARGET / max(mom, 1e-4) * TRIM.get(CATS[b], 1)
    new[str(b)] = float(min(max(g, 0.3), 4.0))
    if b % 52 == 0:
        print(b, f"mom {mom:.3f} lvl {cur:.2f} -> {new[str(b)]:.2f}", log[:200] if "error" in log else "")
json.dump(new, open(lv_path, "w"), indent=0)
v = np.array(list(new.values()))
print("levels: min %.2f median %.2f max %.2f  clamped %d" % (v.min(), np.median(v), v.max(), ((v<=0.3)|(v>=4)).sum()))

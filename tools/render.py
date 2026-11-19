#!/usr/bin/env python3
"""Offline test: render banks to WAV with pd -batch and report levels.
usage: render.py OUTDIR bank [bank ...]   (extra msgs via env CG_MSGS)"""
import os, subprocess, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PLUG = os.path.join(HERE, "..", "ClonkGoblin")

def render(outdir, bank, secs=4.0, msgs="", run=1):
    os.makedirs(outdir, exist_ok=True)
    wav = os.path.join(outdir, f"bank{bank:03d}.wav")
    h = os.path.join(outdir, f"h{bank}.pd")
    m = rf"\; pd dsp 1 \; cg-bank-set {bank} \; cg-sync-set 0 \; cg-run-set {run} {msgs}"
    N = int(secs*48000)
    open(h, "w").write(f"""#N canvas 0 0 400 300 10;
#X obj 10 10 loadbang;
#X obj 10 30 t b b b;
#X msg 10 60 {m};
#X msg 150 60 bang;
#X obj 150 120 tabwrite~ cgL;
#X obj 250 80 r~ cg-master-l;
#X obj 250 100 r~ cg-master-r;
#X obj 10 120 delay {int(secs*1000)+50};
#X msg 10 150 write -wave -bytes 2 {wav} cgL cgR \\; pd quit;
#X obj 10 200 ClonkGoblin;
#X obj 300 120 tabwrite~ cgR;
#X obj 300 200 array define cgL {N};
#X obj 300 230 array define cgR {N};
#X obj 10 180 soundfiler;
#X connect 0 0 1 0;
#X connect 1 2 3 0;
#X connect 1 1 2 0;
#X connect 1 0 7 0;
#X connect 3 0 4 0;
#X connect 3 0 10 0;
#X connect 5 0 4 0;
#X connect 6 0 10 0;
#X connect 7 0 8 0;
#X connect 8 0 13 0;
""")

    r = subprocess.run(["pd", "-batch", "-nogui", "-noaudio", "-nomidi", "-r", "48000",
                        "-path", PLUG, "-stderr", h], capture_output=True, text=True, timeout=120)
    log = (r.stdout + r.stderr).strip()
    with wave.open(wav) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2) / 32768.0
    return wav, x, log

if __name__ == "__main__":
    out = sys.argv[1]
    for b in map(int, sys.argv[2:]):
        wav, x, log = render(out, b, msgs=os.environ.get("CG_MSGS", ""))
        if len(x) == 0:
            print("bank", b, "EMPTY", log[:500]); continue
        peak = np.abs(x).max(); rms = np.sqrt((x**2).mean())
        nan = np.isnan(x).any()
        print(f"bank {b:3d} peak {peak:.3f} rms {rms:.4f} L/R {np.sqrt((x[:,0]**2).mean()):.3f}/{np.sqrt((x[:,1]**2).mean()):.3f}")
        if log: print("   LOG:", log[:1500])

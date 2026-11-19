#!/usr/bin/env python3
"""Offline FOGBANK test render: plays a chord, returns stereo numpy array.
usage: fb_render.py OUTDIR bank [bank...]"""
import os, subprocess, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PLUG = os.path.join(HERE, "..", "Fogbank")

def render(outdir, bank, secs=6.0, msgs="", chord=(48, 55, 63, 70), hold=3.5):
    os.makedirs(outdir, exist_ok=True)
    wav = os.path.join(outdir, f"fb{bank:02d}.wav")
    h = os.path.join(outdir, f"fbh{bank}.pd")
    N = int(secs * 48000)
    on = " ".join(rf"\; fb-note {n} 100" for n in chord)
    off = " ".join(rf"\; fb-note {n} 0" for n in chord)
    open(h, "w").write(rf"""#N canvas 0 0 400 300 10;
#X obj 10 10 loadbang;
#X obj 10 30 t b b b;
#X msg 10 60 \; pd dsp 1 \; fb-bank-set {bank} \; fb-sync-set 0 {msgs} {on};
#X msg 150 60 bang;
#X obj 150 120 tabwrite~ fbL;
#X obj 250 80 r~ fb-master-l;
#X obj 250 100 r~ fb-master-r;
#X obj 10 120 delay {int(secs*1000)+50};
#X msg 10 150 write -wave -bytes 2 {wav} fbL fbR \; pd quit;
#X obj 10 200 Fogbank;
#X obj 300 120 tabwrite~ fbR;
#X obj 300 200 array define fbL {N};
#X obj 300 230 array define fbR {N};
#X obj 10 180 soundfiler;
#X obj 150 160 delay {int(hold*1000)};
#X msg 150 190 {off};
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
#X connect 1 0 14 0;
#X connect 14 0 15 0;
""")
    r = subprocess.run(["pd", "-batch", "-nogui", "-noaudio", "-nomidi", "-r", "48000",
                        "-path", PLUG, "-stderr", h], capture_output=True, text=True, timeout=180)
    log = "\n".join(l for l in (r.stdout + r.stderr).splitlines() if "biggest amplitude" not in l)
    with wave.open(wav) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2) / 32768.0
    return wav, x, log

if __name__ == "__main__":
    for b in map(int, sys.argv[2:]):
        _, x, log = render(sys.argv[1], b, msgs=os.environ.get("FB_MSGS", ""))
        seg = x[int(1.5*48000):int(3.5*48000)]
        print(f"bank {b:2d} peak {np.abs(x).max():.3f} rms(hold) {np.sqrt((seg**2).mean()):.4f} tail {np.sqrt((x[-48000:]**2).mean()):.4f}")
        if log: print("  LOG:", log[:1200])

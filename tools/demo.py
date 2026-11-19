#!/usr/bin/env python3
"""Renders a 'tour' of banks (one per category + extras) into docs/demo.wav"""
import os, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import render
HERE = os.path.dirname(os.path.abspath(__file__))
banks = [0, 13, 2, 1, 4, 30, 6, 7, 8, 35, 10, 11, 12, 5, 9, 3, 44, 20]
names = open(os.path.join(HERE, "..", "ClonkGoblin", "banks.txt")).read().split(";\n")
parts = []
for b in banks:
    _, x, _ = render.render("/tmp/claude-0/demo", b, secs=4.0,
                            msgs=r"\; cg-bpm-set 132")
    f = np.ones(len(x)); n = 2400
    f[:n] = np.linspace(0, 1, n); f[-n:] = np.linspace(1, 0, n)
    parts.append(x * f[:, None])
    print(b, " ".join(names[b].split()[:2]))
y = np.concatenate(parts)
y = (np.clip(y, -1, 1) * 32767).astype(np.int16)
out = os.path.join(HERE, "..", "docs", "demo.wav")
with wave.open(out, "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(48000); w.writeframes(y.tobytes())
print("wrote", out)
import shutil, subprocess
if shutil.which("ffmpeg"):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", out, "-b:a", "192k",
                    out[:-4] + ".mp3"], check=True)
    os.remove(out)
    print("converted to demo.mp3")

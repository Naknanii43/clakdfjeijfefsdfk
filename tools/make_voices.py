#!/usr/bin/env python3
"""Builds VOXEL's sung-word sample sets.

  python3 tools/make_voices.py --piper MODEL.onnx    (real neural voices, used in CI)
  python3 tools/make_voices.py --espeak              (robotic stand-in for offline testing)

For each of 8 voices (chosen automatically to span deep -> high), every word
in tools/voxel_words.py is spoken by a TTS engine, then re-synthesised with the
WORLD vocoder at one steady pitch, with the vowel stretched so it can be held.
Output (Voxel/voices/):
  voice0.wav .. voice7.wav   all words of one voice back to back, 22050 Hz mono
  words.txt                  one line per (voice, word): start susA susB end  (samples)
  voices.txt                 one line per voice: reference pitch in Hz
  credits.txt                where the voices come from
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import pyworld as pw
import soundfile as sf
from scipy.signal import resample_poly

sys.path.insert(0, os.path.dirname(__file__))
from voxel_words import NSPEAKERS, SRC_SR, WORDS, tts_text  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "Voxel", "voices")
FP = 5.0  # WORLD frame period (ms)


# ------------------------------------------------------------------ TTS backends
class Piper:
    def __init__(self, model):
        from piper import PiperVoice, SynthesisConfig
        self.voice = PiperVoice.load(model)
        self.Cfg = SynthesisConfig
        self.nspk = self.voice.config.num_speakers
        self.sr = self.voice.config.sample_rate

    def speakers(self):
        step = max(1, self.nspk // 140)
        return list(range(0, self.nspk, step))

    def say(self, text, spk, slow=1.25):
        cfg = self.Cfg(speaker_id=spk, length_scale=slow, noise_scale=0.5, noise_w_scale=0.6)
        x = np.concatenate([c.audio_float_array for c in self.voice.synthesize(text, syn_config=cfg)])
        return to_src_sr(x.astype(np.float64), self.sr)


class Espeak:
    VOICES = ["en+m3", "en+m1", "en+m2", "en+m5", "en+f5", "en+f2", "en+f1", "en+f4"]
    PITCH = [20, 30, 40, 50, 50, 55, 65, 75]
    sr = SRC_SR

    def speakers(self):
        return list(range(len(self.VOICES)))

    def say(self, text, spk, slow=1.25):
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            subprocess.run(["espeak-ng", "-v", self.VOICES[spk], "-p", str(self.PITCH[spk]),
                            "-s", str(int(150 / slow)), "-w", f.name, text], check=True)
            x, sr = sf.read(f.name)
        return to_src_sr(x.astype(np.float64), sr)


def to_src_sr(x, sr):
    if sr != SRC_SR:
        g = np.gcd(int(sr), SRC_SR)
        x = resample_poly(x, SRC_SR // g, int(sr) // g)
    return x


# ------------------------------------------------------------------ analysis
def trim(x, db=-38, pad=0.015):
    e = np.abs(x)
    th = e.max() * 10 ** (db / 20)
    idx = np.where(e > th)[0]
    if len(idx) == 0:
        return x
    a = max(idx[0] - int(pad * SRC_SR), 0)
    b = min(idx[-1] + int(pad * SRC_SR), len(x))
    return x[a:b]


def median_f0(x):
    f0, t = pw.harvest(x, SRC_SR, f0_floor=55, f0_ceil=500, frame_period=FP)
    v = f0[f0 > 0]
    return (float(np.median(v)) if len(v) else 0.0), (len(v) / max(len(f0), 1))


def longest_run(mask):
    best, cur, start, bs = 0, 0, 0, 0
    for i, m in enumerate(mask):
        if m:
            if cur == 0:
                start = i
            cur += 1
            if cur > best:
                best, bs = cur, start
        else:
            cur = 0
    return bs, bs + best


def sing_word(x, fref, min_sus_s=0.55):
    """WORLD re-synthesis at a steady pitch with a stretched vowel.
    returns audio, sustain start, sustain end (samples, relative)"""
    x = trim(x)
    f0, t = pw.harvest(x, SRC_SR, f0_floor=55, f0_ceil=500, frame_period=FP)
    sp = pw.cheaptrick(x, f0, t, SRC_SR)
    ap = pw.d4c(x, f0, t, SRC_SR)
    a, b = longest_run(f0 > 0)
    if b - a < 4:  # no clear vowel: sustain the loudest middle part
        a, b = len(f0) // 3, max(len(f0) * 2 // 3, len(f0) // 3 + 4)
    # stretch the middle half of the vowel
    n = b - a
    c0, c1 = a + n // 4, b - n // 4
    core = c1 - c0
    want = max(core, int(min_sus_s * 1000 / FP))
    src_idx = np.linspace(c0, c1 - 1, want)
    lo = np.floor(src_idx).astype(int)
    hi = np.minimum(lo + 1, c1 - 1)
    fr = (src_idx - lo)[:, None]
    lsp = np.log(sp + 1e-12)
    sp_core = np.exp(lsp[lo] * (1 - fr) + lsp[hi] * fr)
    ap_core = ap[lo] * (1 - fr) + ap[hi] * fr
    sp2 = np.vstack([sp[:c0], sp_core, sp[c1:]])
    ap2 = np.vstack([ap[:c0], ap_core, ap[c1:]])
    v2 = np.concatenate([f0[:c0] > 0, np.ones(want, bool), f0[c1:] > 0])
    f02 = np.where(v2, fref, 0.0)
    y = pw.synthesize(f02, np.ascontiguousarray(sp2), np.ascontiguousarray(ap2), SRC_SR, FP)
    hop = SRC_SR * FP / 1000
    sa = int((c0 + want * 0.08) * hop)
    sb = int((c0 + want * 0.92) * hop)
    # gentle fade in/out
    f = min(len(y) // 4, int(0.006 * SRC_SR))
    y[:f] *= np.linspace(0, 1, f)
    y[-f:] *= np.linspace(1, 0, f)
    # loudness: sustain RMS -> -18 dBFS
    rms = np.sqrt(np.mean(y[sa:sb] ** 2)) + 1e-9
    y *= 0.125 / rms
    y = np.clip(y, -0.99, 0.99)
    return y, sa, sb


# ------------------------------------------------------------------ main
def pick_speakers(tts, log):
    test = "Hello there, how are you doing today? I hope you are well."
    cands = []
    for spk in tts.speakers():
        x = tts.say(test, spk, slow=1.0)
        f0, vr = median_f0(x)
        if f0 > 0 and vr > 0.35:
            cands.append((f0, spk))
    cands.sort()
    log.append(f"{len(cands)} candidate voices, pitch {cands[0][0]:.0f}-{cands[-1][0]:.0f} Hz")
    if len(cands) <= NSPEAKERS:
        return cands
    qs = np.linspace(0.02, 0.98, NSPEAKERS)
    chosen, used = [], set()
    for q in qs:
        i = int(round(q * (len(cands) - 1)))
        while i in used and i + 1 < len(cands):
            i += 1
        used.add(i)
        chosen.append(cands[i])
    return chosen


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--piper")
    g.add_argument("--espeak", action="store_true")
    args = ap.parse_args()
    tts = Piper(args.piper) if args.piper else Espeak()
    os.makedirs(OUT, exist_ok=True)
    log = []
    speakers = pick_speakers(tts, log)
    words_lines, voices_lines, meta = [], [], []
    for k, (f0, spk) in enumerate(speakers):
        # sing at the voice's own comfortable pitch (rounded to a semitone)
        fref = 440 * 2 ** (round(12 * np.log2(f0 / 440)) / 12)
        buf = [np.zeros(int(0.05 * SRC_SR))]
        pos = len(buf[0])
        for w in WORDS:
            y, sa, sb = sing_word(tts.say(tts_text(w), spk), fref)
            words_lines.append(f"{pos} {pos + sa} {pos + sb} {pos + len(y)};")
            buf.append(y)
            pos += len(y)
            gap = np.zeros(int(0.04 * SRC_SR))
            buf.append(gap)
            pos += len(gap)
        audio = np.concatenate(buf)
        sf.write(os.path.join(OUT, f"voice{k}.wav"), audio, SRC_SR, subtype="PCM_16")
        voices_lines.append(f"{fref:.3f};")
        meta.append(dict(slot=k, speaker_id=spk, speaking_pitch=round(f0, 1), sung_pitch=round(fref, 1),
                         seconds=round(len(audio) / SRC_SR, 1)))
        log.append(f"voice{k}: speaker {spk}, speaks at {f0:.0f} Hz, sings at {fref:.1f} Hz, {len(audio)/SRC_SR:.1f} s")
        print(log[-1], flush=True)
    open(os.path.join(OUT, "words.txt"), "w").write("\n".join(words_lines) + "\n")
    open(os.path.join(OUT, "voices.txt"), "w").write("\n".join(voices_lines) + "\n")
    json.dump(dict(backend="piper" if args.piper else "espeak", words=WORDS, voices=meta),
              open(os.path.join(OUT, "voices.json"), "w"), indent=1)
    credits = ("Voices: synthesised with Piper TTS (MIT, https://github.com/OHF-Voice/piper1-gpl) using the\n"
               "en_US-libritts_r-medium multi-speaker model, trained on the LibriTTS-R corpus\n"
               "(CC BY 4.0, Koizumi et al. 2023, derived from LibriVox public-domain audiobooks).\n"
               "Re-synthesised at a steady pitch with the WORLD vocoder (pyworld, MIT).\n"
               if args.piper else "Voices: espeak-ng stand-in (offline test build).\n")
    open(os.path.join(OUT, "credits.txt"), "w").write(credits)
    print("\n".join(log))


if __name__ == "__main__":
    main()

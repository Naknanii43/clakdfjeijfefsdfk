#!/usr/bin/env python3
"""Generates VOXEL, a singing human-voice instrument (Pure Data -> Camomile VST3).

    python3 tools/make_voices.py --piper MODEL.onnx   (once: builds Voxel/voices/)
    python3 tools/voxel.py                             (writes the Voxel/ plugin patches)

Each note sings a real (neural-TTS) human voice sample of a word or vowel,
pitch-shifted with formant-preserving PSOLA grains: the attack plays, the vowel
is held while the key is down, and the end of the word plays on release.
8 voices span deep to very high (the middle ones are in-between / androgynous).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pdgen import Patch  # noqa: E402
from voxel_words import LYRICS, NSPEAKERS, SRC_SR, VOWELS, WORDS  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "Voxel")
NVOICES = 8
NW = len(WORDS)
NG = 4  # PSOLA grain players per voice

VOICE_NAMES = ["deep", "low", "low-warm", "between-lo", "between-hi", "high-warm", "high", "very-high"]
TEXT_MODES = ["VOWELS", "LYRICS", "RANDOM_WORDS"]

# name, label, lo, hi, log, default
VOICE_P = [("speaker", "VOICE_(LOW->HIGH)", 0, 7, 0, 3), ("body", "BODY", 0.8, 1.25, 0, 1.0),
           ("tune", "OCTAVE/TUNE", -24, 24, 0, 0), ("vowel", "VOWEL/SYLLABLE", 0, len(VOWELS) - 1, 0, 0),
           ("line", "LYRIC_LINE", 0, len(LYRICS) - 1, 0, 0), ("speed", "WORD_SPEED", 0.5, 2, 0, 1)]
EXPR_P = [("vibd", "VIBRATO", 0, 1, 0, 0.5), ("vibr", "VIB-SPEED", 3, 8, 0, 5.5),
          ("vibdel", "VIB-DELAY", 0, 1500, 0, 350), ("jitter", "ROUGHNESS", 0, 1, 0, 0.2),
          ("scoop", "SCOOP", 0, 4, 0, 0.8), ("glide", "GLIDE", 0, 500, 0, 0),
          ("air", "AIR", 0, 1, 0, 0.05)]
AMP_P = [("cast", "CAST-MIX", 0, 1, 0, 0), ("att", "ATTACK", 1, 3000, 1, 12),
         ("rel", "RELEASE", 20, 6000, 1, 450), ("spread", "WIDTH", 0, 1, 0, 0.5)]
FX_P = [("chorus", "CHORUS", 0, 1, 0, 0.15), ("dsync", "ECHO-16THS", 1, 16, 0, 6),
        ("dfb", "ECHO-FB", 0, 0.9, 0, 0.3), ("dmix", "ECHO-MIX", 0, 1, 0, 0.08),
        ("rsize", "REVERB-SIZE", 0, 1, 0, 0.8), ("rmix", "REVERB-MIX", 0, 1, 0, 0.3),
        ("vol", "VOLUME", 0, 1, 0, 0.8)]
GEN_P = [("dens", "DENSITY", 0, 1, 0, 0.5), ("harm", "HARMONY", 0, 1, 0, 0.25),
         ("lyrics", "NEW_LINES", 0, 1, 0, 0.5)]
MACROS = [("mbody", "BODY+", -0.2, 0.2, 0), ("mair", "AIR+", -1, 1, 0),
          ("mvowel", "VOWEL+", -(len(VOWELS) - 1), len(VOWELS) - 1, 0), ("mcast", "CAST+", 0, 1, 0),
          ("mspace", "SPACE+", 0, 1, 0)]
SOUND_KEYS = ([p[0] for p in VOICE_P] + ["text"] + [p[0] for p in EXPR_P + AMP_P + FX_P if p[0] != "vol"])
USER = ["arp", "sing", "hold", "arpm", "arate", "aoct", "agate", "sync", "bpm", "vol",
        "dens", "harm", "lyrics", "scale", "root"]
ALLVALS = SOUND_KEYS + [m[0] for m in MACROS] + USER
DEFAULTS = {p[0]: p[5] for p in VOICE_P + EXPR_P + AMP_P + FX_P}
DEFAULTS["text"] = 0

ARP_MODES = ["UP", "DOWN", "UP+DOWN", "RANDOM", "DRUNK"]
ARP_RATES = ["1/4", "1/8", "1/8T", "1/16", "1/16T", "1/32"]
SCALES = [("MAJ-PENT", [0, 2, 4, 7, 9]), ("MIN-PENT", [0, 3, 5, 7, 10]),
          ("DORIAN", [0, 2, 3, 5, 7, 9, 10]), ("MAJOR", [0, 2, 4, 5, 7, 9, 11]),
          ("MINOR", [0, 2, 3, 5, 7, 8, 10])]
SPQ = "if(vxarate==0, 1, if(vxarate==1, 2, if(vxarate==2, 3, if(vxarate==3, 4, if(vxarate==4, 6, 8)))))"

HOSTP = [
    ("bank", None),
    ("mbody", "param -name Body -min -0.2 -max 0.2 -default 0;"),
    ("mair", "param -name Air -min -1 -max 1 -default 0;"),
    ("mvowel", f"param -name Vowel -min -{len(VOWELS)-1} -max {len(VOWELS)-1} -default 0;"),
    ("mcast", "param -name Cast -min 0 -max 1 -default 0;"),
    ("mspace", "param -name Space -min 0 -max 1 -default 0;"),
    ("text", "param -name Text -list Vowels/Lyrics/Random -default 0;"),
    ("arp", "param -name Arp -list Off/On -default 0;"),
    ("sing", "param -name Sing -list Off/On -default 0;"),
    ("hold", "param -name Hold -list Off/On -default 0;"),
    ("vol", "param -name Volume -min 0 -max 1 -default 0.8;"),
]

B = lambda name, desc, **kw: (name, desc, dict(DEFAULTS, **kw))  # noqa: E731
BANKS = [
    B("Choir_of_Everyone", "every_voice_from_deep_to_very_high_singing_the_lyrics_together", cast=1.0, text=1, line=0, att=20, rel=700, chorus=0.3, rmix=0.45),
    B("Deep_Voice_Ballad", "a_deep_voice_singing_slow_words", speaker=0, tune=-12, text=1, line=1, vibd=0.4, rel=800),
    B("Low_Voice_Ooh", "low_and_round_ooh", speaker=1, tune=-12, text=0, vowel=2, att=60, rel=900),
    B("Warm_Low_Lullaby", "warm_low_voice_singing_come_home_to_me", speaker=2, tune=-12, text=1, line=9, vibd=0.45, rel=900, rmix=0.4),
    B("In_Between_Ah", "an_in-between_voice_singing_ah", speaker=3, text=0, vowel=0, vibd=0.5),
    B("In_Between_Lyrics", "an_in-between_voice:_we_fly_so_high", speaker=4, text=1, line=2),
    B("High_Warm_Oh", "warm_high_voice_singing_oh", speaker=5, text=0, vowel=1, vibd=0.6),
    B("High_Voice_Light", "high_voice:_you_are_my_light", speaker=6, text=1, line=6, vibd=0.6),
    B("Very_High_Ee", "very_high_and_bright_ee", speaker=7, text=0, vowel=3, vibd=0.7, vibr=6.0),
    B("Hummingbird", "closed-mouth_humming", speaker=6, text=0, vowel=4, vibd=0.35, att=80, rel=900),
    B("Random_Talker", "random_words_from_the_song", speaker=3, text=2, speed=1.15, vibd=0.2, scoop=0.4),
    B("Gospel_Scoop", "big_scoops_into_every_word", speaker=5, text=1, line=4, scoop=3, vibd=0.8, vibr=6.0),
    B("Breathy_Secret", "soft_and_airy:_stay_with_me_now", speaker=4, text=1, line=3, air=0.7, vibd=0.3, rmix=0.4),
    B("Robot_Choir", "perfectly_steady_voices", cast=0.6, text=0, vowel=0, vibd=0.0, jitter=0.0, scoop=0.0, att=30, rel=500),
    B("Small_Body_Big_Voice", "a_low_voice_with_a_tiny_throat", speaker=1, tune=-12, body=1.2, text=1, line=5),
    B("Big_Body_Little_Voice", "a_high_voice_with_a_huge_throat", speaker=6, body=0.84, text=1, line=7),
    B("Slow_Words", "words_stretched_out_like_taffy", speaker=2, tune=-12, text=1, line=5, speed=0.6, rel=1300, rmix=0.5),
    B("Fast_Chatter", "a_quick_crowd_saying_song_words", cast=0.8, text=2, speed=1.8, att=5, rel=220, vibd=0.15),
    B("Opera_Hall", "big_vibrato_in_a_huge_hall", speaker=2, tune=-12, text=0, vowel=0, vibd=0.9, vibr=5.6, rsize=0.97, rmix=0.65, att=120, rel=1800),
    B("Night_Choir", "i_feel_you_in_the_night_(everyone)", cast=1.0, text=1, line=0, rsize=0.95, rmix=0.55, rel=1200),
    B("Street_Crowd", "a_mixed_crowd_saying_random_words", cast=1.0, text=2, jitter=0.5, scoop=1.5),
    B("Ooh_Pad", "a_soft_wall_of_ooh", cast=0.7, text=0, vowel=2, att=500, rel=2200, chorus=0.4, rmix=0.5),
    B("Yodel_Goat", "a_very_enthusiastic_mountain_goat", speaker=5, tune=12, text=0, vowel=3, glide=60, scoop=3, vibd=0.7, vibr=7.0),
    B("La_La_Choir", "a_mixed_choir_singing_la", cast=1.0, text=0, vowel=9, att=15, rel=500, chorus=0.3, rmix=0.45),
    B("Hey_Crowd", "a_crowd_shouting_hey_on_the_beat", cast=1.0, text=0, vowel=13, att=3, rel=250, vibd=0.1, scoop=1.2, rmix=0.25),
    B("Stars_Tonight", "the_stars_are_out_tonight_(in-between_voice)", speaker=4, text=1, line=10, vibd=0.55, rmix=0.45),
    B("Sweet_Dreams", "a_low_lullaby:_sweet_dreams_my_love", speaker=2, tune=-12, text=1, line=29, att=40, rel=1500, vibd=0.4, rmix=0.5),
    B("Airport_Angel", "please_proceed_to_gate_heaven", speaker=7, text=0, vowel=1, att=400, rel=2600, chorus=0.5, rsize=0.96, rmix=0.6),
]
HOSTP[0] = ("bank", f"param -name Bank -min 0 -max {len(BANKS)-1} -default 0 -nsteps {len(BANKS)};")

LINEW = []  # lyric line -> word indices (8 slots per line)
for line in LYRICS:
    ids = [WORDS.index(w) for w in line.split()]
    LINEW.append(ids + [0] * (8 - len(ids)))
LINELEN = [len(line.split()) for line in LYRICS]


def write_banks(levels):
    with open(os.path.join(OUT, "banks.txt"), "w") as f:
        for i, (nm, desc, d) in enumerate(BANKS):
            lvl = levels.get(str(i), 1.0)
            pairs = " ".join(f"{k} {d[k]:.4g}" for k in SOUND_KEYS)
            desc = desc.replace(",", "").replace(";", "")  # Pd would split on these
            f.write(f"{nm} {desc} lvl {lvl:.3f} {pairs};\n")


# =========================================================================


# =========================================================================


# =========================================================================
def gen_params():
    p = Patch()
    o = p.obj
    p.text("VOXEL parameter store, voice sample loading, and the lyric / word chooser", 20, 5)
    p.at(20, 40)
    p.max_y = 900
    p.col_w = 200
    lv = o("r vx-lvl-set")
    p.c(lv, o("v vxlvl"))
    for name in ALLVALS:
        r = o(f"r vx-{name}")
        if name == "aoct":
            a = o("+ 1")
            p.c(r, a)
            r = a
        p.c(r, o(f"v vx{name}"))
    # ---- tables + sample loading
    p.at(700, 40)
    tabs = {
        "vxscales": [x for _, sc in SCALES for x in (sc + [0] * 8)[:8]],
        "vxsclen": [len(sc) for _, sc in SCALES],
        "vxlinew": [x for row in LINEW for x in row],
        "vxlinelen": LINELEN,
    }
    for name, vals in tabs.items():
        o(f"array define {name} {len(vals)}")
    for k in range(NSPEAKERS):
        o(f"array define vxs{k} 10")
    o("text define vxwords")
    o("text define vxvoices")
    lb = o("loadbang")
    t = o("t b b b")
    p.c(lb, t)
    fill = "; " + "; ".join(f"{name} 0 " + " ".join(f"{v:g}" for v in vals)
                            for name, vals in tabs.items())
    p.c(t, p.msg(fill), 2)
    sfr = o("soundfiler")
    for k in range(NSPEAKERS):
        m = p.msg(f"read -resize voices/voice{k}.wav vxs{k}")
        p.c(t, m, 1)
        p.c(m, sfr)
    rw = p.msg("read voices/words.txt")
    p.c(t, rw, 1)
    # connect the text reads to their [text define]s
    lines = p.lines
    tw = next(i for i, l in enumerate(lines) if "text define vxwords" in l)
    tv = next(i for i, l in enumerate(lines) if "text define vxvoices" in l)
    p.c(rw, tw)
    rv = p.msg("read voices/voices.txt")
    p.c(t, rv, 1)
    p.c(rv, tv)
    p.c(t, p.msg("; vx-lyrreset bang"), 0)

    # ---- lyric position / line
    p.at(950, 40)
    # use the incoming value itself: reading [v vxline] here could race the store
    rl = o("r vx-line")
    tl = o("t b f")
    p.c(rl, tl)
    cl = o(f"expr min(max(int($f1+0.5), 0), {len(LYRICS)-1})")
    p.c(tl, cl, 1)
    p.c(cl, o("v vxcurline"))
    z0 = p.msg("0")
    p.c(tl, z0, 0)
    p.c(z0, o("v vxlyrpos"))
    rr = o("r vx-lyrreset")
    rre = o(f"expr min(max(int(vxline+0.5), 0), {len(LYRICS)-1})")
    p.c(rr, rre)
    p.c(rre, o("v vxcurline"))
    p.c(rr, z0)
    # SING: at the start of each phrase maybe jump to a new line
    rph = o("r vx-phrase")
    tp = o("t b b")
    p.c(rph, tp)
    p.c(tp, p.msg("0"), 0)
    p.c(p.n - 1, o("v vxlyrpos"))
    nl = o(f"expr if(random(0, 100)<vxlyrics*100, random(0, {len(LYRICS)}), vxcurline)")
    p.c(tp, nl, 1)
    p.c(nl, o("v vxcurline"))
    # ---- word chooser: one new word per chord (notes < 25 ms apart share a word)
    rwt = o("r vx-wordtick")
    tt = o("t b b")
    p.c(rwt, tt)
    tim = o("timer")
    p.c(tt, tim, 1, 1)  # measure time since the last note first
    p.c(tt, tim, 0, 0)  # then reset
    # a new word when >= 25 ms since the last note (or on the very first note)
    mo0 = o("expr $f1>=25 || vxwdone==0")
    p.c(tim, mo0)
    mo = o("sel 0 1")
    p.c(mo0, mo)
    W = (f"if(vxtext<0.5, min(max(int(vxvowel+vxmvowel+0.5), 0), {len(VOWELS)-1}), "
         f"if(vxtext<1.5, vxlinew[vxcurline*8+vxlyrpos%max(vxlinelen[vxcurline], 1)], random({len(VOWELS)}, {NW})))")
    adv = o("t b b")
    p.c(mo, adv, 1)
    we = o(f"expr {W}")
    p.c(adv, we, 1)
    p.c(we, o("v vxwordnow"))
    inc = o("expr vxlyrpos+1")
    p.c(adv, inc, 0)
    p.c(inc, o("v vxlyrpos"))
    p.c(adv, p.msg("1"), 0)
    p.c(p.n - 1, o("v vxwdone"))
    p.save(os.path.join(OUT, "vx-params.pd"))


# =========================================================================
def gen_voice():
    p = Patch(1500, 1100)
    o = p.obj
    p.text("VOXEL voice: real voice samples, formant-preserving PSOLA pitch shift. attack -> held vowel (ping-pong) -> word ending on release", 20, 5)
    inl = o("inlet", 20, 30)
    unp = o("unpack f f", 20, 55)
    p.c(inl, unp)
    p.c(unp, o("v vxxvel", 120, 80), 1)
    tn = o("t b f", 20, 80)
    p.c(unp, tn)
    p.c(tn, o("v vxxnote", 60, 105), 1)
    on = o("expr vxxvel>0", 20, 130)
    p.c(tn, on)
    sel = o("sel 0 1", 20, 155)
    p.c(on, sel)

    # ---------------- signal graph
    p.at(620, 30)
    p.max_y = 1060
    p.col_w = 220
    # pitch: scoop/glide + vibrato + roughness
    F0 = o("vline~")
    vibo = o("osc~ 5.5")
    vibenv = o("vline~")
    vib = o("*~")
    p.c(vibo, vib)
    p.c(vibenv, vib, 0, 1)
    jn = o("noise~")
    jl = o("lop~ 6")
    p.c(jn, jl)
    jg = o("*~ 0")
    p.c(jl, jg)
    mod = o("+~ 1")
    p.c(vib, mod)
    p.c(jg, mod)
    F = o("*~")
    p.c(F0, F)
    p.c(mod, F, 0, 1)
    Fc = o("clip~ 30 2000")
    p.c(F, Fc)
    # read position in the voice sample: attack/release ramp OR sustain ping-pong
    posA = o("vline~")
    susph = o("phasor~ 1")
    posS = o("expr~ $f2+$f3*(1-abs(2*$v1-1))")
    p.c(susph, posS)
    mode = o("vline~")
    pos = o("expr~ if($v3>0.5, $v2, $v1)")
    p.c(posA, pos)
    p.c(posS, pos, 0, 1)
    p.c(mode, pos, 0, 2)
    # PSOLA: grain duration D = min(2 source periods, 4 target periods)
    D = o("expr~ min(2/max($f2, 20), 4/max($v1, 20))")
    p.c(Fc, D)
    master = o("*~ 0.25")
    p.c(Fc, master)
    mph = o("phasor~")
    p.c(master, mph)
    gq = o("expr~ floor($v1/max($f2, 1)+0.5)*max($f2, 1)")  # snap to the pitch-period grid
    p.c(pos, gq)
    gsum = o("*~ 1")
    tabs = []
    for k in range(NG):
        if k:
            sh = o(f"+~ {k/NG}")
            p.c(mph, sh)
            q = o("wrap~")
            p.c(sh, q)
        else:
            q = mph
        gs = o("samphold~")
        p.c(gq, gs)
        p.c(q, gs, 0, 1)
        w = o("expr~ $v1*4/(max($v2, 20)*max($v3, 0.0001))")
        p.c(q, w)
        p.c(Fc, w, 0, 1)
        p.c(D, w, 0, 2)
        rp = o(f"expr~ $v1+$v2*$v3*{SRC_SR}*$f4")
        p.c(gs, rp)
        p.c(w, rp, 0, 1)
        p.c(D, rp, 0, 2)
        tr = o("tabread4~ vxs0")
        p.c(rp, tr)
        tabs.append(tr)
        win = o("expr~ if($v2<1, 0.5-0.5*cos(6.28319*$v2), 0)*$v1")
        p.c(tr, win)
        p.c(w, win, 0, 1)
        p.c(win, gsum)
        tabs.append(rp)
    olan = o("expr~ $v1*2/max($v2*$v3, 1)")  # overlap-add normalisation
    p.c(gsum, olan)
    p.c(D, olan, 0, 1)
    p.c(Fc, olan, 0, 2)
    # air (breath) layer
    an = o("noise~")
    ah = o("hip~ 2500")
    p.c(an, ah)
    ag = o("*~ 0")
    p.c(ah, ag)
    AE = o("vline~")
    amp = o("*~")
    p.c(olan, amp)
    p.c(ag, amp)
    p.c(AE, amp, 0, 1)
    out = o("*~ 1")
    p.c(amp, out)
    p.c(out, o("outlet~", 1300, 1075))
    p.c(out, o("outlet~", 1400, 1075))
    tabreads = tabs[0::2]
    readpos = tabs[1::2]

    # ---------------- note on
    p.at(20, 190)
    p.max_y = 1060
    p.col_w = 300
    NB = 12
    ton = o("t " + "b " * NB)
    p.c(sel, ton, 1)
    nxt = [NB - 1]

    def step():
        k = nxt[0]
        nxt[0] -= 1
        return k

    # 11: which voice sings this note
    who = o(f"expr if(random(0, 1000)<min(vxcast+vxmcast, 1)*1000, random(0, {NSPEAKERS}), min(max(int(vxspeaker+0.5), 0), {NSPEAKERS-1}))")
    p.c(ton, who, step())
    tw = o("t f f f")
    p.c(who, tw)
    p.c(tw, o("v vxxs"), 2)
    # 10: that voice's sample table + sung pitch
    mk = o("makefilename vxs%d")
    p.c(tw, mk, 1)
    ms = p.msg("set $1")
    p.c(mk, ms)
    for tr in tabreads:
        p.c(ms, tr)
    tvg = o("text get vxvoices")
    p.c(tw, tvg, 0)
    p.c(tvg, o("v vxxfref"))
    k10 = step()
    # word boundaries: start susA susB end
    wi = o(f"expr vxxs*{NW}+vxwordnow")
    p.c(ton, wi, k10)
    twg = o("text get vxwords")
    p.c(wi, twg)
    up = o("unpack f f f f")
    p.c(twg, up)
    for i, nm in enumerate(("vxxa", "vxxsa", "vxxsb", "vxxe")):
        p.c(up, o(f"v {nm}"), i)
    # 9: grain params: source period, sung pitch, formant (BODY) read speed
    k9 = step()
    per = o(f"expr {SRC_SR}/max(vxxfref, 20); vxxfref; min(max(vxbody+vxmbody, 0.6), 1.5)")
    p.c(ton, per, k9)
    p.c(per, gq, 0, 1)
    p.c(per, D, 1, 1)
    for rp in readpos:
        p.c(per, rp, 2, 3)
    # 8: position envelopes (attack -> sustain ping-pong)
    k8 = step()
    pe = o(f"expr vxxa; vxxsa; (vxxsa-vxxa)/{SRC_SR/1000}/max(vxspeed, 0.2); "
           f"{SRC_SR}/max(vxxsb-vxxsa, 50)/3.2; vxxsb-vxxsa")
    p.c(ton, pe, k8)
    ppk = o("pack f f f")
    p.c(pe, ppk, 0, 0)
    p.c(pe, ppk, 1, 1)
    p.c(pe, ppk, 2, 2)
    p.c(ppk, p.msg("$1, $2 $3"))
    p.c(p.n - 1, posA)
    sse = o("expr vxxsa; vxxsb-vxxsa")
    p.c(ton, sse, k8)
    p.c(sse, posS, 0, 1)
    p.c(sse, posS, 1, 2)
    p.c(pe, susph, 3, 0)  # ping-pong rate
    mt = o("expr (vxxsa-vxxa)/" + f"{SRC_SR/1000}" + "/max(vxspeed, 0.2)")
    p.c(ton, mt, k8)
    tm = o("t f f")
    p.c(mt, tm)
    p.c(tm, p.msg("0, 1 0 $1"), 0)
    p.c(p.n - 1, mode)
    dl = o("delay")
    p.c(tm, dl, 1, 0)  # float into [delay] = start with that time
    p.c(dl, p.msg("0"))
    p.c(p.n - 1, susph, 0, 1)  # reset the ping-pong to the vowel start
    # 7: vibrato + roughness
    k7 = step()
    vr = o("expr vxvibr*(1+(random(0, 1001)/1000-0.5)*0.1)")
    p.c(ton, vr, k7)
    p.c(vr, vibo)
    jge = o("expr vxjitter*0.01")
    p.c(ton, jge, k7)
    p.c(jge, jg, 0, 1)
    vde = o("expr vxvibd*0.03; vxvibdel")
    p.c(ton, vde, step())
    vpk = o("pack f f")
    p.c(vde, vpk, 0, 0)
    p.c(vde, vpk, 1, 1)
    p.c(vpk, p.msg("0, $1 500 $2"))
    p.c(p.n - 1, vibenv)
    # 5: pitch (glide to a scooped start, slide up to the note)
    pp = o("expr 440*pow(2, (vxxnote+vxtune-69-vxscoop+(random(0, 101)/100-0.5)*0.1)/12); vxglide; "
           "440*pow(2, (vxxnote+vxtune-69+(random(0, 101)/100-0.5)*0.1)/12); 40+vxscoop*25")
    p.c(ton, pp, step())
    fpk = o("pack f f f f")
    for i in range(4):
        p.c(pp, fpk, i, i)
    p.c(fpk, p.msg("$1 $2, $3 $4 $2"))
    p.c(p.n - 1, F0)
    # 4: air + level
    k4 = step()
    air = o("expr min(max(vxair+vxmair, 0), 1)*0.06")
    p.c(ton, air, k4)
    p.c(air, ag, 0, 1)
    lve = o("expr vxlvl*0.9")
    p.c(ton, lve, k4)
    p.c(lve, out, 0, 1)
    # 3: amp envelope
    ae = o("expr pow(vxxvel/127, 0.7); vxatt")
    p.c(ton, ae, step())
    apk = o("pack f f")
    p.c(ae, apk, 0, 0)
    p.c(ae, apk, 1, 1)
    p.c(apk, p.msg("$1 $2"))
    p.c(p.n - 1, AE)

    # ---------------- note off: play the end of the word, then fade
    rl = o(f"expr vxxsb; vxxe; (vxxe-vxxsb)/{SRC_SR/1000}/max(vxspeed, 0.2); "
           f"max(vxrel, (vxxe-vxxsb)/{SRC_SR/1000}/max(vxspeed, 0.2))")
    p.c(sel, rl, 0)
    rpk = o("pack f f f")
    p.c(rl, rpk, 0, 0)
    p.c(rl, rpk, 1, 1)
    p.c(rl, rpk, 2, 2)
    p.c(rpk, p.msg("$1, $2 $3"))
    p.c(p.n - 1, posA)
    p.c(rl, p.msg("0 $1"), 3)
    p.c(p.n - 1, AE)
    p.c(sel, p.msg("0"), 0)
    p.c(p.n - 1, mode)
    p.c(sel, p.msg("stop"), 0)
    p.c(p.n - 1, dl)
    p.save(os.path.join(OUT, "vx-voice.pd"))


# =========================================================================
def gen_clock():
    p = Patch(1000, 700)
    o = p.obj
    p.text("VOXEL arp clock: internal metro (while ARP is on) or the DAW transport (SYNC + playing)", 20, 5)
    p.at(20, 40)
    trig = []
    for name in ("bpm", "arate"):
        r = o(f"r vx-{name}")
        t = o("t b f")
        p.c(r, t)
        p.c(t, o(f"v vx{name}"), 1)
        trig.append(t)
    lb = o("loadbang")
    sm = o(f"expr 60000/(max(vxbpm, 20)*{SPQ})")
    for t in trig + [lb]:
        p.c(t, sm)
    p.c(sm, o("v vxstepms"))
    p.at(280, 40)
    st_in = []
    for name in ("arp", "sing", "sync"):
        r = o(f"r vx-{name}")
        t = o("t b f")
        p.c(r, t)
        p.c(t, o(f"v vx{name}"), 1)
        st_in.append(t)
    rph = o("r playhead")
    route = o("route playing bpm position")
    p.c(rph, route)
    chp = o("change")
    p.c(route, chp)
    thp = o("t b f")
    p.c(chp, thp)
    p.c(thp, o("v vxhostplay"), 1)
    st = o("expr if((vxarp || vxsing) && !(vxsync && vxhostplay), 1, 0)")
    for t in st_in + [thp]:
        p.c(t, st)
    stc = o("change")
    p.c(st, stc)
    met = o("metro 250")
    p.c(stc, met)
    p.c(sm, met, 0, 1)
    cnt = o("f")
    inc = o("+ 1")
    p.c(met, cnt)
    p.c(cnt, inc)
    p.c(inc, cnt, 0, 1)
    outl = o("outlet", 600, 600)
    p.c(cnt, outl)
    # host bpm + position
    p.at(560, 40)
    hb = o("change")
    p.c(route, hb, 1)
    hbe = o("expr if(vxsync, $f1, -1)")
    p.c(hb, hbe)
    hbm = o("moses 1")
    p.c(hbe, hbm)
    hbr = o("expr int($f1*10+0.5)/10")
    p.c(hbm, hbr, 1)
    p.c(hbr, o("s vx-bpm-set"))
    up = o("unpack f f f")
    p.c(route, up, 2)
    hs = o(f"expr if(vxsync && vxhostplay, floor($f1*{SPQ}+0.0001), -1)")
    p.c(up, hs)
    hsm = o("moses 0")
    p.c(hs, hsm)
    hsc = o("change")
    p.c(hsm, hsc, 1)
    p.c(hsc, outl)
    p.save(os.path.join(OUT, "vx-clock.pd"))


# =========================================================================
def gen_brain():
    p = Patch(1500, 1000)
    o = p.obj
    p.text("VOXEL brain: MIDI -> HOLD (latch) -> direct notes, ARP, or SING (generative phrases). outlet goes to [poly].", 20, 5)
    tick = o("inlet", 20, 20)
    mid = o("inlet", 700, 20)
    outl = o("outlet", 700, 960)
    for arr in ("vxheld", "vxphys", "vxsorted"):
        o(f"array define {arr} 128", 1300, 20 + 25 * ("vxheld", "vxphys", "vxsorted").index(arr))

    def scan(arr, sorted_arr, count):
        """returns an object that, when banged, rebuilds count (and sorted list)"""
        t = o("t b b")
        z = p.msg("0")
        p.c(t, z, 1)
        p.c(z, o(f"v {count}"))
        n = p.msg("128")
        p.c(t, n, 0)
        u = o("until")
        p.c(n, u)
        i = o("f")
        i1 = o("+ 1")
        p.c(u, i)
        p.c(i, i1)
        p.c(i1, i, 0, 1)
        p.c(z, i, 0, 1)
        h = o(f"expr if({arr}[$f1]>0, $f1, -1)")
        p.c(i, h)
        m = o("moses 0")
        p.c(h, m)
        tf = o("t f b b")
        p.c(m, tf, 1)
        if sorted_arr:
            ec = o(f"expr {count}")
            p.c(tf, ec, 2)
            tw = o(f"tabwrite {sorted_arr}")
            p.c(ec, tw, 0, 1)
            p.c(tf, tw, 0)
        inc = o(f"expr {count}+1")
        p.c(tf, inc, 1)
        p.c(inc, o(f"v {count}"))
        return t

    def tabset(arr, idx_expr, val_expr, src, outlet=0):
        t = o("t b b")
        p.c(src, t, outlet)
        ie = o(f"expr {idx_expr}")
        p.c(t, ie, 1)
        tw = o(f"tabwrite {arr}")
        p.c(ie, tw, 0, 1)
        ve = o(f"expr {val_expr}")
        p.c(t, ve, 0)
        p.c(ve, tw)

    # ---- resend: stop all voices, then (if ARP off) replay the held set
    p.at(20, 60)
    p.max_y = 950
    p.col_w = 330
    resend = o("t b b")
    stop = p.msg("stop")
    p.c(resend, stop, 1)
    p.c(stop, outl)
    p.c(stop, p.msg("-1"))
    p.c(p.n - 1, o("v vxarpcur"))
    rs_ok = o("expr vxarp==0 && vxsing==0")
    p.c(resend, rs_ok, 0)
    rs_sel = o("sel 1")
    p.c(rs_ok, rs_sel)
    rs_n = o("expr vxcount")
    p.c(rs_sel, rs_n)
    rs_u = o("until")
    p.c(rs_n, rs_u)
    rs_i = o("f")
    rs_i1 = o("+ 1")
    p.c(rs_u, rs_i)
    p.c(rs_i, rs_i1)
    p.c(rs_i1, rs_i, 0, 1)
    rs_z = p.msg("0")
    p.c(rs_sel, rs_z)
    p.conns.pop()
    rs_t = o("t b b")
    p.conns = [c for c in p.conns if c != f"#X connect {rs_sel} 0 {rs_n} 0;"]
    p.c(rs_sel, rs_t)
    p.c(rs_t, rs_z, 1)
    p.c(rs_z, rs_i, 0, 1)
    p.c(rs_t, rs_n, 0)
    rs_note = o("expr vxsorted[$f1]; max(vxlastvel, 60)")
    p.c(rs_i, rs_note)
    rs_pk = o("pack f f")
    p.c(rs_note, rs_pk, 0, 0)
    p.c(rs_note, rs_pk, 1, 1)
    p.c(rs_pk, outl)

    held_scan = scan("vxheld", "vxsorted", "vxcount")
    phys_scan = scan("vxphys", None, "vxphyscount")

    # ---- MIDI in
    p.at(400, 60)
    tm = o("t b b b b b l")
    p.c(mid, tm)
    un = o("unpack f f")
    p.c(tm, un, 5)
    p.c(un, o("v vxmv"), 1)
    p.c(un, o("v vxmn"), 0)
    # (b) new chord while HOLD -> forget the old one
    nc = o("expr vxmv>0 && vxhold && vxphyscount==0")
    p.c(tm, nc, 4)
    ncs = o("sel 1")
    p.c(nc, ncs)
    nct = o("t b b")
    p.c(ncs, nct)
    clr = p.msg("const 0")
    p.c(nct, clr, 1)
    p.c(clr, o("s vxheld"))
    ncr = o("expr vxarp==0 && vxsing==0")
    p.c(nct, ncr, 0)
    ncr2 = o("sel 1")
    p.c(ncr, ncr2)
    p.c(ncr2, stop)
    # (c) physical keys
    tabset("vxphys", "vxmn", "vxmv", tm, 3)
    # (d) held set
    hd = o("expr vxmv>0 || vxhold==0")
    p.c(tm, hd, 2)
    hds = o("sel 1")
    p.c(hd, hds)
    tabset("vxheld", "vxmn", "vxmv", hds)
    lv = o("expr if(vxmv>0, vxmv, vxlastvel)")
    p.c(hds, lv)
    p.c(lv, o("v vxlastvel"))
    # (e) direct play when ARP is off
    dp = o("expr vxarp==0 && vxsing==0 && (vxmv>0 || vxhold==0)")
    p.c(tm, dp, 1)
    dps = o("sel 1")
    p.c(dp, dps)
    dpe = o("expr vxmn; vxmv")
    p.c(dps, dpe)
    dpk = o("pack f f")
    p.c(dpe, dpk, 0, 0)
    p.c(dpe, dpk, 1, 1)
    p.c(dpk, outl)
    # (f) rescans
    rsc = o("t b b")
    p.c(tm, rsc, 0)
    p.c(rsc, held_scan, 1)
    p.c(rsc, phys_scan, 0)

    # ---- ARP / HOLD switches
    p.at(760, 60)
    ra = o("r vx-arp")
    ta = o("t b f")
    p.c(ra, ta)
    p.c(ta, o("v vxarp"), 1)
    p.c(ta, resend, 0)
    rsg = o("r vx-sing")
    tsg = o("t b f")
    p.c(rsg, tsg)
    p.c(tsg, o("v vxsing"), 1)
    p.c(tsg, resend, 0)
    rh = o("r vx-hold")
    th = o("t b f")
    p.c(rh, th)
    p.c(th, o("v vxhold"), 1)
    hoff = o("expr vxhold==0")
    p.c(th, hoff, 0)
    hos = o("sel 1")
    p.c(hoff, hos)
    # held := phys, rescan, resend
    hcp = o("t b b b")
    p.c(hos, hcp)
    cpn = p.msg("128")
    p.c(hcp, cpn, 2)
    cpu = o("until")
    p.c(cpn, cpu)
    cpi = o("f")
    cpi1 = o("+ 1")
    p.c(cpu, cpi)
    p.c(cpi, cpi1)
    p.c(cpi1, cpi, 0, 1)
    cpz = p.msg("0")
    p.c(hcp, cpz, 2)
    p.conns = [c for c in p.conns if c != f"#X connect {hcp} 2 {cpn} 0;"]
    cpt = o("t b b")
    p.conns = [c for c in p.conns if c != f"#X connect {hcp} 2 {cpz} 0;"]
    p.c(hcp, cpt, 2)
    p.c(cpt, cpz, 1)
    p.c(cpz, cpi, 0, 1)
    p.c(cpt, cpn, 0)
    cpv = o("t f f")
    p.c(cpi, cpv)
    cpe = o("expr vxphys[$f1]")
    p.c(cpv, cpe, 1)
    cpw = o("tabwrite vxheld")
    p.c(cpv, cpw, 0, 1)
    p.conns = [c for c in p.conns if c != f"#X connect {cpv} 0 {cpw} 1;"]
    p.conns = [c for c in p.conns if c != f"#X connect {cpv} 1 {cpe} 0;"]
    # index first (right outlet), then value (left outlet)
    p.c(cpv, cpw, 1, 1)
    p.c(cpv, cpe, 0, 0)
    p.c(cpe, cpw)
    p.c(hcp, held_scan, 1)
    p.c(hcp, resend, 0)
    # panic: CC123 or UNSTICK
    cc = o("ctlin 123")
    run = o("r vx-unstick")
    pan = o("t b b b")
    p.c(cc, pan)
    p.c(run, pan)
    c0 = p.msg("const 0")
    p.c(pan, c0, 2)
    p.c(c0, o("s vxheld"))
    p.c(c0, o("s vxphys"))
    p.c(pan, held_scan, 1)
    p.c(pan, resend, 0)
    # sustain pedal -> HOLD
    cc64 = o("ctlin 64")
    ped = o("expr $f1>63")
    p.c(cc64, ped)
    pc = o("change")
    p.c(ped, pc)
    p.c(pc, o("s vx-hold-set"))

    # ---- ARP ticks
    p.at(1100, 60)
    go = o("expr vxarp && !vxsing && vxcount>0")
    p.c(tick, go)
    gs = o("sel 1")
    p.c(go, gs)
    t3 = o("t b b b")
    p.c(gs, t3)
    # off routine (shared with the gate delay)
    off = o("expr vxarpcur")
    p.c(t3, off, 2)
    offm = o("moses 0")
    p.c(off, offm)
    offt = o("t f b")
    p.c(offm, offt, 1)
    m1 = p.msg("-1")
    p.c(offt, m1, 1)
    p.c(m1, o("v vxarpcur"))
    offp = o("pack f 0")
    p.c(offt, offp, 0)
    p.c(offp, outl)
    # next note
    apos = o("f")
    ainc = o("+ 1")
    p.c(t3, apos, 1)
    p.c(apos, ainc)
    p.c(ainc, apos, 0, 1)
    N = "(vxcount*vxaoct)"
    P = f"max(2*{N}-2, 1)"
    ak = o(f"expr if(vxarpm==0, $f1%{N}, if(vxarpm==1, {N}-1-$f1%{N}, if(vxarpm==2, if($f1%{P}<{N}, $f1%{P}, 2*{N}-2-$f1%{P}), if(vxarpm==3, random(0, {N}), min(max(vxprevk+random(-1, 2), 0), {N}-1)))))")
    p.c(apos, ak)
    tk = o("t f f")
    p.c(ak, tk)
    p.c(tk, o("v vxprevk"), 1)
    an = o("expr min(vxsorted[$f1%vxcount]+12*int($f1/vxcount), 127)")
    p.c(tk, an, 0)
    p.c(an, o("v vxarpnext"))
    # play it
    pl = o("t b b b")
    p.c(t3, pl, 0)
    gd = o("expr max(vxagate*vxstepms, 10)")
    p.c(pl, gd, 2)
    dl = o("delay")
    p.c(gd, dl, 0, 1)
    nv = o("expr vxarpnext; max(vxlastvel, 60)")
    p.c(pl, nv, 1)
    npk = o("pack f f")
    p.c(nv, npk, 0, 0)
    p.c(nv, npk, 1, 1)
    ntt = o("t l l")
    p.c(npk, ntt)
    p.c(ntt, outl, 0)
    cur = o("unpack f f")
    p.c(ntt, cur, 1)
    p.c(cur, o("v vxarpcur"))
    p.c(pl, dl, 0)
    p.c(dl, off)
    p.c(pl, o("s vx-arpflash"), 0)

    # ---- SING: generative phrases (notes from held keys, else SCALE + ROOT)
    p.at(1100, 520)
    L = "if(vxcount>0, vxcount, vxsclen[vxscale])"

    def note_of(d):
        w = f"((({d})%{L}+{L})%{L})"
        return (f"min(max(if(vxcount>0, vxsorted[{w}], vxroot+vxscales[vxscale*8+{w}])"
                f"+12*floor(({d})/{L}), 0), 127)")

    def play(expr_note, vel, curvar):
        e = o(f"expr {expr_note}; {vel}")
        pk = o("pack f f")
        p.c(e, pk, 0, 0)
        p.c(e, pk, 1, 1)
        tt = o("t l l")
        p.c(pk, tt)
        p.c(tt, outl, 0)
        u = o("unpack f f")
        p.c(tt, u, 1)
        p.c(u, o(f"v {curvar}"))
        return e

    sg = o("expr vxsing")
    p.c(tick, sg)
    sgs = o("sel 1")
    p.c(sg, sgs)
    cdq = o("expr vxcd>0")
    p.c(sgs, cdq)
    s01 = o("sel 0 1")
    p.c(cdq, s01)
    dec = o("expr vxcd-1")
    p.c(s01, dec, 1)
    p.c(dec, o("v vxcd"))
    ev = o("t b b")
    p.c(s01, ev, 0)
    # release the previous sung note(s)
    p.c(ev, off, 1)
    hof = o("expr vxharmcur")
    p.c(ev, hof, 1)
    hom = o("moses 0")
    p.c(hof, hom)
    hot = o("t f b")
    p.c(hom, hot, 1)
    hm1 = p.msg("-1")
    p.c(hot, hm1, 1)
    p.c(hm1, o("v vxharmcur"))
    hop = o("pack f 0")
    p.c(hot, hop, 0)
    p.c(hop, outl)
    # rest or note?
    rq = o("expr vxphr<=0")
    p.c(ev, rq, 0)
    rsel = o("sel 1 0")
    p.c(rq, rsel)
    rt = o("t b b")
    p.c(rsel, rt, 0)
    re1 = o("expr random(1, 4)+int((1-vxdens)*7)")
    p.c(rt, re1, 1)
    p.c(re1, o("v vxcd"))
    re2 = o("expr random(3, 9)")
    p.c(rt, re2, 0)
    p.c(re2, o("v vxphr"))
    p.c(rt, o("s vx-phrase"), 0)  # new phrase: maybe a new lyric line
    nt = o("t b b b b b")
    p.c(rsel, nt, 1)
    dg = o(f"expr min(max(vxdeg+if(random(0, 10)<7, random(-1, 2), random(-3, 4)), -{L}), 2*{L}-1)")
    p.c(nt, dg, 4)
    p.c(dg, o("v vxdeg"))
    gn = o(f"expr {note_of('vxdeg')}")
    p.c(nt, gn, 3)
    p.c(gn, o("v vxgnote"))
    pl1 = play("vxgnote", "65+random(0, 45)", "vxarpcur")
    p.c(nt, pl1, 1)
    hq = o("expr random(0, 100)<vxharm*100")
    p.c(nt, hq, 1)
    hs = o("sel 1")
    p.c(hq, hs)
    pl2 = play(note_of("vxdeg+2"), "55+random(0, 30)", "vxharmcur")
    p.c(hs, pl2)
    p.c(nt, o("s vx-arpflash"), 1)
    ph = o("expr vxphr-1; if(random(0, 10)<4, 0, if(random(0, 10)<6, 1, if(random(0, 10)<5, 2, 3)))")
    p.c(nt, ph, 0)
    p.c(ph, o("v vxphr"), 0)
    p.c(ph, o("v vxcd"), 1)
    lbh = o("loadbang")
    p.c(lbh, p.msg("-1"))
    p.c(p.n - 1, o("v vxharmcur"))
    p.save(os.path.join(OUT, "vx-brain.pd"))


# =========================================================================
def gen_fx():
    p = Patch(1300, 900)
    o = p.obj
    p.text("VOXEL fx: stereo chorus -> ping-pong echo (16ths) -> big schroeder reverb", 20, 5)
    il = o("inlet~", 300, 10)
    ir = o("inlet~", 400, 10)
    p.at(20, 40)
    lb = o("loadbang")
    met = o("metro 40")
    p.c(lb, met)
    lines = {}
    for key, ex, ms in (("chorus", "vxchorus", 60),
                        ("dtime", "min(max(vxdsync*15000/max(vxbpm, 20), 10), 2900)", 120),
                        ("dfb", "vxdfb", 50), ("dmix", "vxdmix", 50),
                        ("rfb", "0.7+vxrsize*0.27", 80),
                        ("rmix", "min(vxrmix+vxmspace, 1)", 50),
                        ("width", "0.5+vxspread*1.5", 60)):
        e = o(f"expr {ex}")
        p.c(met, e)
        ch = o("change")
        p.c(e, ch)
        m = p.msg(f"$1 {ms}")
        p.c(ch, m)
        ln = o("line~")
        p.c(m, ln)
        lines[key] = ln

    # chorus
    p.at(300, 60)
    outs = []
    lf = o("osc~ 0.31")  # one LFO, opposite phase on L and R = balanced
    for side, src, sign in (("l", il, "+"), ("r", ir, "-")):
        dw = o(f"delwrite~ $0-ch{side} 60")
        p.c(src, dw)
        dt = o(f"expr~ 14{sign}6*$v1")
        p.c(lf, dt)
        vd = o(f"vd~ $0-ch{side}")
        p.c(dt, vd)
        wet = o("*~")
        p.c(vd, wet)
        p.c(lines["chorus"], wet, 0, 1)
        s = o("+~")
        p.c(src, s)
        p.c(wet, s, 0, 1)
        outs.append(s)
    cl, cr = outs

    # echo (ping-pong)
    p.at(560, 60)
    mono = o("*~ 0.5")
    p.c(cl, mono)
    p.c(cr, mono)
    # balanced echo: both sides get the same input and the same time = equal L/R
    dwl = o("delwrite~ $0-dl 4500")
    dwr = o("delwrite~ $0-dr 4500")
    p.c(mono, dwl)
    p.c(mono, dwr)
    vdl = o("vd~ $0-dl")
    vdr = o("vd~ $0-dr")
    p.c(lines["dtime"], vdl)
    p.c(lines["dtime"], vdr)
    for src, dst in ((vdl, dwl), (vdr, dwr)):
        lp = o("lop~ 2800")
        p.c(src, lp)
        hp = o("hip~ 150")
        p.c(lp, hp)
        vx = o("*~")
        p.c(hp, vx)
        p.c(lines["dfb"], vx, 0, 1)
        p.c(vx, dst)
    el = o("*~")
    er = o("*~")
    p.c(vdl, el)
    p.c(vdr, er)
    p.c(lines["dmix"], el, 0, 1)
    p.c(lines["dmix"], er, 0, 1)
    sl = o("+~")
    sr = o("+~")
    p.c(cl, sl)
    p.c(el, sl, 0, 1)
    p.c(cr, sr)
    p.c(er, sr, 0, 1)
    # WIDTH: mid/side, symmetric so it can never lean to one side
    mid = o("*~ 0.5")
    p.c(sl, mid)
    p.c(sr, mid)
    side = o("-~")
    p.c(sl, side)
    p.c(sr, side, 0, 1)
    sideh = o("*~ 0.5")
    p.c(side, sideh)
    sidew = o("*~")
    p.c(sideh, sidew)
    p.c(lines["width"], sidew, 0, 1)
    nl = o("+~")
    p.c(mid, nl)
    p.c(sidew, nl, 0, 1)
    nr = o("-~")
    p.c(mid, nr)
    p.c(sidew, nr, 0, 1)
    sl, sr = nl, nr

    # reverb
    p.at(820, 60)

    def allpass(src, name, ms, g=0.6):
        w = o("+~")
        p.c(src, w)
        dw = o(f"delwrite~ $0-{name} 100")
        p.c(w, dw)
        dr = o(f"delread~ $0-{name} {ms}")
        gd = o(f"*~ {g}")
        p.c(dr, gd)
        p.c(gd, w, 0, 1)
        gw = o(f"*~ {-g}")
        p.c(w, gw)
        y = o("+~")
        p.c(dr, y)
        p.c(gw, y, 0, 1)
        return y

    rin = o("*~ 0.2")
    p.c(sl, rin)
    p.c(sr, rin)
    rhp = o("hip~ 140")  # keep the lows out of the reverb (less mud, equal L/R)
    p.c(rin, rhp)
    pre = o("delwrite~ $0-pre 100")
    p.c(rhp, pre)
    prd = o("delread~ $0-pre 30")
    d1 = allpass(prd, "d1", 4.7)
    d2 = allpass(d1, "d2", 11.3)
    wets = []
    for side, times, ap in (("l", (50.3, 56.9, 61.7, 68.2, 74.9, 81.1, 86.3), 5.3),):
        acc = o("*~ 0.15")
        for k, ms in enumerate(times):
            sm = o("+~")
            p.c(d2, sm)
            dw = o(f"delwrite~ $0-c{side}{k} 120")
            p.c(sm, dw)
            dr = o(f"delread~ $0-c{side}{k} {ms}")
            lp = o("lop~ 4200")
            p.c(dr, lp)
            g = o("*~")
            p.c(lp, g)
            p.c(lines["rfb"], g, 0, 1)
            p.c(g, sm, 0, 1)
            p.c(dr, acc)
        a = allpass(acc, f"o{side}", ap, 0.5)
        w = o("*~")
        p.c(a, w)
        p.c(lines["rmix"], w, 0, 1)
        wets.append(w)
    # right = the same reverb 13 ms later: wide, but exactly equal energy L/R
    rdw = o("delwrite~ $0-rdel 50")
    p.c(wets[0], rdw)
    wets.append(o("delread~ $0-rdel 13"))
    ol = o("outlet~", 900, 870)
    orr = o("outlet~", 1000, 870)
    p.c(sl, ol)
    p.c(wets[0], ol)
    p.c(sr, orr)
    p.c(wets[1], orr)
    p.save(os.path.join(OUT, "vx-fx.pd"))


# =========================================================================
def gen_bank():
    p = Patch(1000, 700)
    o = p.obj
    p.text("VOXEL banks: banks.txt line = Name description lvl x key value ...", 20, 5)
    p.at(20, 40)
    tb = o("text define vxbanks")
    lb = o("loadbang")
    t = o("t b b")
    p.c(lb, t)
    rd = p.msg("read banks.txt")
    p.c(t, rd, 1)
    p.c(rd, tb)
    p.c(t, p.msg("; vx-bank-set 0"), 0)
    p.at(300, 40)
    rb = o("r vx-bank")
    cl = o(f"clip 0 {len(BANKS)-1}")
    p.c(rb, cl)
    tl = o("t f f")
    p.c(cl, tl)
    p.c(tl, o("v vxbank"), 1)
    get = o("text get vxbanks")
    p.c(tl, get, 0)
    sp = o("list split 2")
    p.c(get, sp)
    nm = o("unpack s s")
    p.c(sp, nm)
    p.c(nm, p.msg("; vx-name-lbl label $1"), 0)
    p.c(nm, p.msg("; vx-desc-lbl label $1"), 1)
    d = o("list split 2")
    back = o("list")
    p.c(sp, d, 1)
    p.c(d, back, 1)
    p.c(back, d)
    p.c(d, p.msg("; vx-$1-set $2"))
    p.at(600, 40)
    n = len(BANKS)
    for rcv, ex in (("vx-prev", f"(vxbank-1+{n})%{n}"), ("vx-next", f"(vxbank+1)%{n}"),
                    ("vx-rand", f"random(0, {n})")):
        r = o(f"r {rcv}")
        e = o(f"expr {ex}")
        p.c(r, e)
        p.c(e, o("s vx-bank-set"))
    p.save(os.path.join(OUT, "vx-bank.pd"))


def gen_host():
    p = Patch(1300, 900)
    o = p.obj
    p.text("host bridge for Camomile: [r param] -> GUI, state save/load. idle elsewhere.", 20, 5)
    p.at(20, 40)
    rp = o("r param")
    rt = o("route " + " ".join(str(i + 1) for i in range(len(HOSTP))))
    p.c(rp, rt)
    p.at(20, 100)
    p.col_w = 150
    p.max_y = 300
    for i, (name, _) in enumerate(HOSTP):
        ch = o("change")
        p.c(rt, ch, i)
        tf = o("t f f")
        p.c(ch, tf)
        ne = o(f"expr $f1 != vx{name}")
        p.c(tf, ne, 1)
        sp = o("spigot")
        p.c(ne, sp, 0, 1)
        p.c(tf, sp, 0)
        p.c(sp, o(f"s vx-{name}-set"))
    p.at(20, 360)
    p.col_w = 220
    p.max_y = 880
    rs = o("r save")
    names = [n for n in ALLVALS] + ["lvl", "bank"]
    t = o("t b " + "b " * len(names) + "b")
    p.c(rs, t)
    store = o("list store")
    clear = p.msg("list")
    p.c(t, clear, len(names) + 1)
    p.c(clear, store, 0, 1)
    for k, n in enumerate(names):
        v = o(f"v vx{n}")
        p.c(t, v, len(names) - k)
        if n == "aoct":
            mm = o("- 1")
            p.c(v, mm)
            v = mm
        am = p.msg(f"append {n} $1")
        p.c(v, am)
        p.c(am, store)
    out = p.msg("bang")
    p.c(t, out, 0)
    p.c(out, store)
    pre = o("list prepend save")
    p.c(store, pre)
    tr = o("list trim")
    p.c(pre, tr)
    p.c(tr, o("s camomile"))
    rl = o("r load")
    ll = o("list")
    p.c(rl, ll)
    sp = o("list split 2")
    p.c(ll, sp)
    back = o("list")
    p.c(sp, back, 1)
    p.c(back, sp)
    p.c(sp, p.msg("; vx-$1-set $2"))
    p.save(os.path.join(OUT, "vx-host.pd"))


# =========================================================================


# =========================================================================
PAL = dict(bg="#24192b", panel="#35253d", panel2="#4a3354", top="#1a1120", text="#f5ecf7",
           coral="#ff8c69", gold="#ffd166", mint="#7ee0b8", lilac="#c9a7eb", dim="#a892b3")


def gen_main():
    p = Patch(1500, 900, 10)
    W, H = 780, 480
    P = PAL
    cnv, lab = p.cnv, p.label
    cnv(0, 0, W, H, P["bg"])
    cnv(0, 0, W, 54, P["top"], "VOXEL", 10, 20, 26, P["coral"])
    lab(12, 44, f"real_singing_voices_//_8_voices_//_{len(WORDS)}_words_//_{len(BANKS)}_banks", 9, P["lilac"], P["top"])
    p.bng(250, 12, 18, "vx-prev", "empty", "<", P["bg"], P["coral"], P["bg"], 6, 9, 11)
    p.nbx(272, 12, 3, 18, 0, len(BANKS) - 1, "vx-bank", "vx-bank-set", "BANK", "#000000",
          P["coral"], P["coral"], 0, -6, 9)
    p.bng(318, 12, 18, "vx-next", "empty", ">", P["bg"], P["coral"], P["bg"], 6, 9, 11)
    p.bng(340, 12, 18, "vx-rand", "empty", "?", P["bg"], P["gold"], P["bg"], 6, 9, 11)
    lab(372, 20, "...", 16, P["text"], P["top"], "vx-name-lbl")
    p.bng(732, 8, 38, "vx-poke", "empty", "SING!", P["bg"], P["mint"], P["top"], 4, 19, 9)
    cnv(0, 54, W, 20, P["panel2"])
    lab(10, 64, "...", 10, P["mint"], P["panel2"], "vx-desc-lbl")

    def panel(x, y, w, h, title, col):
        cnv(x, y, w, h, P["panel"], title, 6, 9, 10, col)

    def sliders(x, y0, items, col, step=24, w=120):
        for k, it in enumerate(items):
            name, label, lo, hi, lg = it[:5]
            p.hsl(x, y0 + k * step, w, 13, lo, hi, f"vx-{name}", f"vx-{name}-set", label, lg,
                  col, "#1e1424", P["text"])

    panel(4, 78, 254, 172, "VOICE", P["coral"])
    sliders(10, 94, VOICE_P, P["coral"], 22)
    lab(10, 230, "TEXT", 8, P["text"], P["panel"])
    p.hradio(38, 223, 13, 3, "vx-text", "vx-text-set", "empty", P["coral"], "#1e1424", P["text"])
    lab(82, 230, "VOWELS", 9, P["coral"], P["panel"], "vx-textname")
    lab(150, 230, "...", 8, P["dim"], P["panel"], "vx-voicename")
    lab(10, 243, "...", 8, P["mint"], P["panel"], "vx-linetext")
    panel(262, 78, 254, 172, "EXPRESSION", P["gold"])
    sliders(268, 96, EXPR_P, P["gold"], 22)
    panel(520, 78, 256, 172, "CAST_+_ENVELOPE", P["lilac"])
    sliders(526, 96, AMP_P, P["lilac"], 24)
    lab(526, 196, "CAST-MIX_=_chance_each_note_is_sung", 8, P["dim"], P["panel"])
    lab(526, 208, "by_another_of_the_8_voices_(deep->", 8, P["dim"], P["panel"])
    lab(526, 220, "in-between->very_high)", 8, P["dim"], P["panel"])
    lab(526, 238, "BODY_moves_the_formants:_<1_bigger_throat", 8, P["dim"], P["panel"])

    panel(4, 254, 254, 222, "SPACE", P["mint"])
    sliders(10, 272, FX_P, P["mint"], 28)

    panel(262, 254, 254, 222, "PERFORM", P["gold"])
    y = 270
    p.tgl(268, y, 18, "vx-arp", "vx-arp-set", "ARP", P["gold"], "#1e1424", P["text"], 21, 9, 9)
    p.tgl(318, y, 18, "vx-sing", "vx-sing-set", "SING", P["mint"], "#1e1424", P["text"], 21, 9, 9)
    p.tgl(372, y, 18, "vx-hold", "vx-hold-set", "HOLD", P["gold"], "#1e1424", P["text"], 21, 9, 9)
    p.tgl(426, y, 18, "vx-sync", "vx-sync-set", "DAW-SYNC", P["gold"], "#1e1424", P["text"], 21, 9, 9)
    p.bng(498, y + 2, 12, "empty", "vx-arpflash", "empty", P["mint"], "#1e1424", P["text"])
    y = 296
    lab(268, y + 6, "MODE", 8, P["text"], P["panel"])
    p.hradio(300, y, 13, 5, "vx-arpm", "vx-arpm-set", "empty", P["gold"], "#1e1424", P["text"])
    lab(370, y + 6, "UP", 9, P["gold"], P["panel"], "vx-arpmname")
    lab(430, y + 6, "OCT", 8, P["text"], P["panel"])
    p.hradio(452, y, 13, 4, "vx-aoct", "vx-aoct-set", "empty", P["gold"], "#1e1424", P["text"])
    y = 314
    lab(268, y + 6, "RATE", 8, P["text"], P["panel"])
    p.hradio(300, y, 13, 6, "vx-arate", "vx-arate-set", "empty", P["gold"], "#1e1424", P["text"])
    lab(382, y + 6, "1/8", 9, P["gold"], P["panel"], "vx-aratename")
    p.nbx(430, y, 3, 13, 20, 300, "vx-bpm", "vx-bpm-set", "BPM", "#000000", P["gold"], P["text"], 34, 6, 8)
    p.hsl(268, 334, 90, 12, 0.05, 1, "vx-agate", "vx-agate-set", "GATE", 0, P["gold"], "#1e1424", P["text"])
    p.bng(400, 334, 12, "vx-unstick", "empty", "ALL-NOTES-OFF", P["bg"], P["coral"], P["text"], 15, 6, 8)
    lab(268, 358, "SING_(generative)", 9, P["mint"], P["panel"])
    for k, (name, label, lo, hi, lg, _) in enumerate(GEN_P):
        p.hsl(268, 368 + k * 19, 110, 12, lo, hi, f"vx-{name}", f"vx-{name}-set", label, lg,
              P["mint"], "#1e1424", P["text"])
    y = 428
    lab(268, y + 6, "SCALE", 8, P["text"], P["panel"])
    p.hradio(302, y, 13, len(SCALES), "vx-scale", "vx-scale-set", "empty", P["mint"], "#1e1424", P["text"])
    lab(372, y + 6, "MIN-PENT", 9, P["mint"], P["panel"], "vx-scalename")
    p.nbx(450, y, 3, 13, 24, 96, "vx-root", "vx-root-set", "ROOT", "#000000", P["mint"], P["text"], 34, 6, 8)
    lab(268, 454, "SING_uses_your_held_keys_as_its_notes", 8, P["dim"], P["panel"])
    lab(268, 466, "or_SCALE+ROOT_when_no_keys_are_held.", 8, P["dim"], P["panel"])

    panel(520, 254, 256, 222, "BIG_KNOBS_(DAW)", P["coral"])
    sliders(526, 272, MACROS, P["coral"], 24)
    lab(526, 400, "these_ride_on_top_of_the_bank", 8, P["dim"], P["panel"])
    lab(526, 414, "-_automate_them_in_your_DAW", 8, P["dim"], P["panel"])
    lab(526, 436, "try:_bank_0_+_SING_on_+_play", 9, P["gold"], P["panel"])
    lab(526, 452, "or_hold_a_chord_+_ARP+HOLD", 9, P["gold"], P["panel"])
    p.gop(W, H)

    # ---------------- engine wiring
    o = p.obj
    X = 820
    p.text("VOXEL - the plugin face is left of here. engine below.", X, 10)
    o("vx-params", X, 40)
    o("vx-bank", X, 64)
    o("vx-host", X, 88)
    clock = o("vx-clock", X, 130)
    brain = o("vx-brain", X, 180)
    p.c(clock, brain)
    ni = o("notein", X + 160, 120)
    npk = o("pack f f", X + 160, 145)
    p.c(ni, npk, 0, 0)
    p.c(ni, npk, 1, 1)
    p.c(npk, brain, 0, 1)
    rn = o("r vx-note", X + 260, 145)
    p.c(rn, brain, 0, 1)
    # SING! button: a short audition phrase note
    rp = o("r vx-poke", X + 360, 120)
    pe = o("expr vxroot+12; 100", X + 360, 145)
    p.c(rp, pe)
    ppk = o("pack f f", X + 360, 170)
    p.c(pe, ppk, 0, 0)
    p.c(pe, ppk, 1, 1)
    pt = o("t l b", X + 360, 195)
    p.c(ppk, pt)
    # every note-on asks for a word first (one new word per chord), then goes to [poly]
    nsplit = o("t a a", X, 205)
    p.c(brain, nsplit)
    p.c(pt, nsplit, 0)
    nrl = o("route list", X + 120, 185)
    p.c(nsplit, nrl, 1)
    nvu = o("unpack f f", X + 120, 205)
    p.c(nrl, nvu, 0)
    nvm = o("moses 1", X + 120, 230)
    p.c(nvu, nvm, 1)
    p.c(nvm, o("s vx-wordtick", X + 120, 255), 1)
    poly = o(f"poly {NVOICES} 1", X, 230)
    p.c(nsplit, poly, 0)
    pd_ = o("delay 700", X + 460, 220)
    p.c(pt, pd_, 1)
    poff = o("expr vxroot+12; 0", X + 460, 245)
    p.c(pd_, poff)
    pof = o("pack f f", X + 460, 270)
    p.c(poff, pof, 0, 0)
    p.c(poff, pof, 1, 1)
    p.c(pof, nsplit)
    pk = o("pack f f f", X, 250)
    p.c(poly, pk, 0, 0)
    p.c(poly, pk, 1, 1)
    p.c(poly, pk, 2, 2)
    cl = o(f"clone -s 1 vx-voice {NVOICES}", X, 280)
    p.c(pk, cl)
    p.c(cl, o("s~ vx-dry", X + 300, 310), 0)  # tap for offline tests
    fx = o("vx-fx", X, 310)
    p.c(cl, fx, 0, 0)
    p.c(cl, fx, 1, 1)
    rv = o("r vx-vol", X + 200, 310)
    vm = p.msg("$1 30", X + 200, 335)
    p.c(rv, vm)
    vl = o("line~", X + 200, 360)
    p.c(vm, vl)
    gl = o("*~", X, 360)
    gr = o("*~", X + 80, 360)
    p.c(fx, gl, 0)
    p.c(fx, gr, 1)
    p.c(vl, gl, 0, 1)
    p.c(vl, gr, 0, 1)
    hl = o("hip~ 10", X, 385)
    hr = o("hip~ 10", X + 80, 385)
    p.c(gl, hl)
    p.c(gr, hr)
    c1 = o("expr~ tanh($v1)", X, 410)
    c2 = o("expr~ tanh($v1)", X + 160, 410)
    p.c(hl, c1)
    p.c(hr, c2)
    dac = o("dac~ 1 2", X, 440)
    p.c(c1, dac, 0, 0)
    p.c(c2, dac, 0, 1)
    p.c(c1, o("s~ vx-master-l", X + 100, 465))
    p.c(c2, o("s~ vx-master-r", X + 220, 465))

    def namer(rcv, dests, names, y):
        r = o(f"r {rcv}", X + 400, y)
        s = o("sel " + " ".join(str(i) for i in range(len(names))), X + 400, y + 25)
        p.c(r, s)
        for i, nm in enumerate(names):
            txt = "; " + "; ".join(f"{d} label {nm}" for d in dests)
            m = p.msg(txt, X + 400 + i * 150, y + 50)
            p.c(s, m, i)

    namer("vx-arpm", ["vx-arpmname"], ARP_MODES, 320)
    namer("vx-arate", ["vx-aratename"], ARP_RATES, 420)
    namer("vx-scale", ["vx-scalename"], [s[0] for s in SCALES], 520)
    namer("vx-text", ["vx-textname"], TEXT_MODES, 620)
    # voice name + lyric line text labels
    rsp = o("r vx-speaker", X + 400, 720)
    spi = o(f"expr min(max(int($f1+0.5), 0), {NSPEAKERS-1})", X + 400, 745)
    p.c(rsp, spi)
    sps = o("sel " + " ".join(str(i) for i in range(NSPEAKERS)), X + 400, 770)
    p.c(spi, sps)
    for i, nm in enumerate(VOICE_NAMES):
        p.c(sps, p.msg(f"; vx-voicename label v{i+1}:{nm}", X + 400 + i * 160, 795), i)
    rvo = o("r vx-vowel", X + 400, 960)
    voi = o(f"expr min(max(int($f1+0.5), 0), {len(VOWELS)-1})", X + 400, 985)
    p.c(rvo, voi)
    vos = o("sel " + " ".join(str(i) for i in range(len(VOWELS))), X + 400, 1010)
    p.c(voi, vos)
    for i, (key, _) in enumerate(VOWELS):
        p.c(vos, p.msg(f"; vx-vowel-set label VOWEL:_{key}", X + 400 + i * 130, 1035), i)
    rli = o("r vx-line", X + 400, 830)
    lii = o(f"expr min(max(int($f1+0.5), 0), {len(LYRICS)-1})", X + 400, 855)
    p.c(rli, lii)
    lis = o("sel " + " ".join(str(i) for i in range(len(LYRICS))), X + 400, 880)
    p.c(lii, lis)
    for i, line in enumerate(LYRICS):
        p.c(lis, p.msg(f'; vx-linetext label "{line.replace(" ", "_")}"'.replace('"', ''), X + 400 + i * 160, 905), i)

    lb = o("loadbang", X, 520)
    init = ("; vx-bpm-set 92; vx-arp-set 0; vx-sing-set 0; vx-hold-set 0; vx-arpm-set 0; "
            "vx-arate-set 1; vx-aoct-set 0; vx-agate-set 0.8; vx-sync-set 1; vx-vol-set 0.8; "
            "vx-dens-set 0.5; vx-harm-set 0.25; vx-lyrics-set 0.5; vx-scale-set 1; vx-root-set 57; "
            "vx-mbody-set 0; vx-mair-set 0; vx-mvowel-set 0; vx-mcast-set 0; vx-mspace-set 0")
    p.c(lb, p.msg(init, X, 545))
    p.save(os.path.join(OUT, "Voxel.pd"))


def gen_txt():
    lines = ["type instrument;", "code VxVc;", "midiin true;", "midiout false;",
             "playhead true;", "bus 0 2;", "taillength 8;", "compatibility v1.0.7;"]
    lines += [h[1] for h in HOSTP]
    with open(os.path.join(OUT, "Voxel.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    gen_params()
    gen_voice()
    gen_clock()
    gen_brain()
    gen_fx()
    gen_bank()
    gen_host()
    gen_main()
    gen_txt()
    lv = os.path.join(ROOT, "tools", "voxel_levels.json")
    write_banks(json.load(open(lv)) if os.path.exists(lv) else {})
    print("wrote", OUT)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generates FOGBANK, an ambient pad synth (Pure Data -> Camomile VST3).

    python3 tools/fogbank.py         -> writes Fogbank/ plugin folder
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pdgen import Patch  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "Fogbank")
NVOICES = 8

ENGINES = ["CLOUD", "GLASS", "CHOIR", "WIND", "TAPE"]

# name, label, lo, hi, log, default
ENG_P = [("tune", "TUNE", -24, 24, 0, 0), ("color", "COLOR", 0, 1, 0, 0.5),
         ("motion", "MOTION", 0, 1, 0, 0.3), ("detune", "DETUNE", 0, 1, 0, 0.3),
         ("glide", "GLIDE", 0, 800, 0, 0)]
FIL_P = [("cut", "CUTOFF", 20, 135, 0, 80), ("res", "RESONANCE", 0.5, 8, 1, 1),
         ("fenv", "ENV>CUT", 0, 48, 0, 12), ("lfor", "LFO-RATE", 0.02, 8, 1, 0.15),
         ("lfof", "LFO>CUT", 0, 36, 0, 6), ("lfop", "LFO>PITCH", 0, 1, 0, 0.1)]
AMP_P = [("att", "ATTACK", 1, 8000, 1, 1500), ("dec", "DECAY", 10, 8000, 1, 3000),
         ("sus", "SUSTAIN", 0, 1, 0, 0.8), ("rel", "RELEASE", 10, 15000, 1, 4000),
         ("warm", "WARMTH", 0, 1, 0, 0.2), ("spread", "WIDTH", 0, 1, 0, 0.6)]
FX_P = [("chorus", "CHORUS", 0, 1, 0, 0.4), ("dsync", "ECHO-16THS", 1, 16, 0, 6),
        ("dfb", "ECHO-FB", 0, 0.9, 0, 0.4), ("dmix", "ECHO-MIX", 0, 1, 0, 0.15),
        ("rsize", "REVERB-SIZE", 0, 1, 0, 0.85), ("rmix", "REVERB-MIX", 0, 1, 0, 0.4),
        ("vol", "VOLUME", 0, 1, 0, 0.8)]
MACROS = [("mbright", "BRIGHT", -36, 36, 0), ("mcolor", "COLOR+", -1, 1, 0),
          ("mmotion", "MOTION+", -1, 1, 0), ("matt", "ATTACK-x", -2, 2, 0),
          ("mrel", "RELEASE-x", -2, 2, 0), ("mspace", "SPACE+", 0, 1, 0)]
SOUND_KEYS = ["engine"] + [p[0] for p in ENG_P + FIL_P + AMP_P + FX_P if p[0] != "vol"]
USER = ["arp", "hold", "arpm", "arate", "aoct", "agate", "sync", "bpm", "vol"]
ALLVALS = SOUND_KEYS + [m[0] for m in MACROS] + USER
DEFAULTS = {p[0]: p[5] for p in ENG_P + FIL_P + AMP_P + FX_P}
DEFAULTS["engine"] = 0

ARP_MODES = ["UP", "DOWN", "UP+DOWN", "RANDOM", "DRUNK"]
ARP_RATES = ["1/4", "1/8", "1/8T", "1/16", "1/16T", "1/32"]
SPQ = "if(fbarate==0, 1, if(fbarate==1, 2, if(fbarate==2, 3, if(fbarate==3, 4, if(fbarate==4, 6, 8)))))"

HOSTP = [
    ("bank", "param -name Bank -min 0 -max 37 -default 0 -nsteps 38;"),
    ("mbright", "param -name Bright -label st -min -36 -max 36 -default 0;"),
    ("mcolor", "param -name Color -min -1 -max 1 -default 0;"),
    ("mmotion", "param -name Motion -min -1 -max 1 -default 0;"),
    ("matt", "param -name Attack -min -2 -max 2 -default 0;"),
    ("mrel", "param -name Release -min -2 -max 2 -default 0;"),
    ("mspace", "param -name Space -min 0 -max 1 -default 0;"),
    ("arp", "param -name Arp -list Off/On -default 0;"),
    ("hold", "param -name Hold -list Off/On -default 0;"),
    ("vol", "param -name Volume -min 0 -max 1 -default 0.8;"),
]

# ------------------------------------------------------------------ banks
B = lambda name, desc, engine, **kw: (name, desc, dict(DEFAULTS, engine=engine, **kw))  # noqa: E731
BANKS = [
    # CLOUD (supersaw)
    B("Morning_Fog", "like_a_duvet_made_of_sine_waves", 0, color=0.4, detune=0.35, cut=72, fenv=10, att=2500, rel=5000, chorus=0.5, rmix=0.45),
    B("Cathedral_Lint", "dust_floating_in_a_very_big_room", 0, color=0.2, detune=0.6, cut=84, res=1.6, lfof=10, lfor=0.08, rsize=0.95, rmix=0.6, att=3500, rel=8000),
    B("Warm_Static_Blanket", "cozy._fuzzy._slightly_electric.", 0, color=0.7, detune=0.45, cut=66, warm=0.7, att=1200, rel=4000, chorus=0.6),
    B("Slow_Sunrise", "opens_up_like_a_sleepy_eyelid", 0, color=0.3, detune=0.3, cut=48, fenv=40, att=6000, dec=7000, sus=0.6, rel=6000, rmix=0.5),
    B("Big_Soft_Nothing", "the_sound_of_a_cloud_thinking", 0, tune=-12, color=0.9, detune=0.8, cut=60, motion=0.7, att=4000, rel=9000, rsize=0.97, rmix=0.55),
    B("Velvet_Pluck_Rain", "arp-friendly._pitter-patter.", 0, color=0.3, detune=0.25, cut=58, fenv=36, att=5, dec=700, sus=0.2, rel=1800, dmix=0.35, dfb=0.55, dsync=3),
    # GLASS (FM)
    B("Ice_Choir_of_Spoons", "frozen_cutlery_singing_softly", 1, color=0.07, motion=0.25, cut=100, att=1800, rel=6000, rmix=0.5),
    B("Frozen_Lake_Bells", "bells_heard_through_ice", 1, color=0.4, motion=0.5, cut=110, att=20, dec=4000, sus=0.25, rel=6000, rmix=0.55, rsize=0.93),
    B("Glass_Harmonium", "wet_finger_on_a_wine_glass", 1, color=0.0, motion=0.15, cut=96, lfop=0.3, att=900, rel=3500, chorus=0.3),
    B("Distant_Satellite", "beep_boop_from_very_far_away", 1, color=0.27, motion=0.8, lfor=0.4, cut=105, att=600, rel=5000, dmix=0.3, dsync=6, dfb=0.6),
    B("Crystal_Drip_Pad", "arp-friendly._tiny_glass_drops.", 1, color=0.2, motion=0.35, cut=118, att=3, dec=900, sus=0.1, rel=2500, dmix=0.3, dsync=3, rmix=0.5),
    B("Prism_Breath", "rainbows_exhaling", 1, color=0.53, motion=0.6, lfor=0.07, cut=92, res=2, lfof=14, att=3000, rel=7000, chorus=0.6),
    # CHOIR (additive formants)
    B("Sleepy_Monks", "ooooh_(but_drowsy)", 2, tune=-12, color=0.12, motion=0.25, cut=95, att=2500, rel=6000, rmix=0.55),
    B("Ghost_Vowels", "aaaa-eeee-oooo_from_the_attic", 2, color=0.5, motion=0.9, lfor=0.12, cut=110, att=1500, rel=6000, chorus=0.5),
    B("Aaah_in_a_Tunnel", "one_long_aaah_in_a_long_tunnel", 2, color=0.35, motion=0.2, cut=100, rsize=0.97, rmix=0.65, att=2000, rel=8000),
    B("Breathing_Organ", "a_church_organ_taking_a_nap", 2, color=0.75, motion=0.4, lfor=0.2, cut=105, att=800, rel=3000, warm=0.3),
    B("Moth_Choir", "tiny_fuzzy_singers_near_a_lamp", 2, tune=12, color=0.85, motion=0.6, cut=115, detune=0.6, att=1200, rel=4500, chorus=0.7),
    B("Hum_of_the_Fridge", "2am_kitchen_meditation", 2, tune=-24, color=0.05, motion=0.1, cut=85, lfor=0.05, lfof=4, att=3000, rel=6000, warm=0.5, rmix=0.35),
    # WIND (resonant noise)
    B("Wind_Through_Pipes", "drafty_but_in_tune", 3, color=0.45, motion=0.4, cut=110, att=2000, rel=5000, rmix=0.5),
    B("Whistling_Canyon", "a_canyon_that_learned_to_whistle", 3, tune=12, color=0.85, motion=0.3, cut=125, att=1500, rel=6000, rsize=0.95, rmix=0.6),
    B("Seashell_Ear", "hold_it_up_to_your_ear", 3, color=0.2, motion=0.7, lfor=0.1, cut=100, lfof=14, att=3000, rel=7000),
    B("Bowed_Fog", "a_violin_bow_dragged_across_mist", 3, color=0.65, motion=0.5, cut=105, res=1.5, att=1200, rel=4000, chorus=0.5),
    B("Night_Air_Drone", "crickets_went_home._this_stayed.", 3, tune=-12, color=0.55, motion=0.8, lfor=0.05, cut=95, att=5000, rel=9000, rmix=0.55),
    B("Steam_Kettle_Lullaby", "arp-friendly._polite_little_whistles.", 3, tune=12, color=0.95, motion=0.2, cut=128, att=10, dec=600, sus=0.3, rel=1500, dmix=0.35, dsync=4, dfb=0.5),
    # TAPE (PWM + wobble)
    B("Worn_VHS_Strings", "rewound_too_many_times", 4, color=0.3, motion=0.5, lfop=0.35, cut=78, warm=0.4, att=1500, rel=4000, chorus=0.6),
    B("Wobbly_Cassette_Pad", "left_in_a_hot_car_all_summer", 4, color=0.55, motion=0.9, lfop=0.6, lfor=0.4, cut=72, warm=0.5, att=1000, rel=4000),
    B("Grandmas_Synth", "found_in_the_attic._still_works.", 4, color=0.15, motion=0.3, cut=85, detune=0.5, att=500, rel=2500, chorus=0.7, warm=0.3),
    B("Dusty_Memory", "arp-friendly._faded_photograph.", 4, color=0.4, motion=0.4, cut=70, fenv=30, att=5, dec=800, sus=0.25, rel=2000, dmix=0.4, dsync=3, dfb=0.6),
    B("LoFi_Aurora", "northern_lights_on_a_tiny_tv", 4, tune=12, color=0.7, motion=0.6, lfor=0.25, cut=90, lfof=12, att=2500, rel=6000, rmix=0.55),
    B("Melted_Polaroid", "a_warm_blurry_goodbye", 4, tune=-12, color=0.85, motion=0.7, lfop=0.5, cut=64, warm=0.6, att=3000, rel=8000, rsize=0.93, rmix=0.5),
]
# ---- opposite pairs: same engine, opposite feeling (dreamy <-> harsh)
BANKS += [
    B("Dream_Cloud_Bath", "PAIR_1_DREAMY:_warm_bath_in_a_cloud", 0, color=0.45, detune=0.3, cut=64, res=0.8, fenv=8, lfor=0.06, lfof=5, att=4000, rel=9000, warm=0.1, chorus=0.6, rsize=0.96, rmix=0.6),
    B("Harsh_Cloud_Grinder", "PAIR_1_HARSH:_the_same_cloud_in_a_blender", 0, color=0.9, detune=1.0, cut=126, res=4, fenv=20, lfor=6.5, lfof=20, lfop=0.35, att=150, rel=1500, warm=1.0, spread=1.0, chorus=0.0, dmix=0.25, dfb=0.7, dsync=3, rsize=0.6, rmix=0.2),
    B("Dream_Snow_Globe", "PAIR_2_DREAMY:_shake_gently._watch_it_settle", 1, color=0.07, motion=0.18, cut=96, res=0.8, lfor=0.08, att=2500, rel=8000, warm=0.05, chorus=0.5, rmix=0.6, rsize=0.95),
    B("Harsh_Broken_Window", "PAIR_2_HARSH:_the_snow_globe_hit_the_floor", 1, color=0.63, motion=1.0, cut=132, res=3.5, lfor=7.3, lfof=24, lfop=0.5, att=40, dec=1200, sus=0.7, rel=1200, warm=0.95, spread=1.0, chorus=0.0, rmix=0.2, rsize=0.5),
    B("Dream_Lullaby_Choir", "PAIR_3_DREAMY:_humming_you_to_sleep", 2, color=0.1, motion=0.2, lfor=0.07, cut=92, res=0.8, att=3500, rel=8000, warm=0.05, chorus=0.5, rmix=0.6, rsize=0.95),
    B("Harsh_Screaming_Vowels", "PAIR_3_HARSH:_the_choir_found_out_about_taxes", 2, tune=12, color=0.95, motion=1.0, lfor=5.5, lfof=18, lfop=0.4, cut=128, res=5, fenv=24, att=60, rel=1500, warm=1.0, detune=0.9, spread=1.0, chorus=0.0, rmix=0.25, rsize=0.6),
    B("Dream_Faded_Tape", "PAIR_4_DREAMY:_a_cassette_of_a_summer_long_ago", 4, color=0.2, motion=0.35, lfop=0.3, lfor=0.25, cut=66, res=0.8, att=3000, rel=8000, warm=0.25, chorus=0.6, rmix=0.55, rsize=0.93),
    B("Harsh_Chewed_Tape", "PAIR_4_HARSH:_the_tape_deck_ate_it._angrily.", 4, color=0.95, motion=1.0, lfop=1.0, lfor=6.0, lfof=24, cut=130, res=4, fenv=30, att=30, dec=900, sus=0.6, rel=1000, warm=1.0, detune=0.8, spread=1.0, chorus=0.2, dmix=0.3, dfb=0.75, dsync=2, rmix=0.2, rsize=0.5),
]
assert len(BANKS) == 38


def write_banks(levels):
    with open(os.path.join(OUT, "banks.txt"), "w") as f:
        for i, (nm, desc, d) in enumerate(BANKS):
            lvl = levels.get(str(i), 1.0)
            pairs = " ".join(f"{k} {d[k]:.4g}" for k in SOUND_KEYS)
            f.write(f"{nm} {desc} lvl {lvl:.3f} {pairs};\n")


# =========================================================================
def gen_params():
    p = Patch()
    o = p.obj
    p.text("FOGBANK parameter store + smoothed global signals (fb-s-*)", 20, 5)
    p.at(20, 40)
    p.max_y = 900
    p.col_w = 200
    lv = o("r fb-lvl-set")
    p.c(lv, o("v fblvl"))
    for name in ALLVALS:
        r = o(f"r fb-{name}")
        if name == "aoct":
            a = o("+ 1")
            p.c(r, a)
            r = a
        p.c(r, o(f"v fb{name}"))
    # smoothed signals
    p.at(700, 40)
    lb = o("loadbang")
    met = o("metro 25")
    p.c(lb, met)
    sig = [
        ("min(max(fbcolor+fbmcolor, 0), 1)", "fb-s-color", 60),
        ("min(max(fbmotion+fbmmotion, 0), 1)", "fb-s-motion", 60),
        ("fbdetune", "fb-s-detune", 60),
        ("min(max(fbcut+fbmbright, 0), 140)", "fb-s-cut", 40),
    ]
    for ex, name, ms in sig:
        e = o(f"expr {ex}")
        p.c(met, e)
        ch = o("change")
        p.c(e, ch)
        m = p.msg(f"$1 {ms}")
        p.c(ch, m)
        ln = o("line~")
        p.c(m, ln)
        p.c(ln, o(f"s~ {name}"))
    # float version of colour (WIND engine resonance)
    ec = o("expr min(max(fbcolor+fbmcolor, 0), 1)")
    p.c(met, ec)
    ecc = o("change")
    p.c(ec, ecc)
    p.c(ecc, o("s fb-e-color"))
    # LFO
    lr = o("expr max(fblfor, 0.01)")
    p.c(met, lr)
    lrc = o("change")
    p.c(lr, lrc)
    lfo = o("osc~ 0.15")
    p.c(lrc, lfo)
    p.c(lfo, o("s~ fb-lfo"))
    for ex, name in (("fblfof", "fb-lfocut"), ("fblfop*0.0578", "fb-vibamt")):
        e = o(f"expr {ex}")
        p.c(met, e)
        ch = o("change")
        p.c(e, ch)
        m = p.msg("$1 60")
        p.c(ch, m)
        ln = o("line~")
        p.c(m, ln)
        mul = o("*~")
        p.c(lfo, mul)
        p.c(ln, mul, 0, 1)
        if name == "fb-vibamt":
            one = o("+~ 1")
            p.c(mul, one)
            p.c(one, o("s~ fb-vib"))
        else:
            p.c(mul, o(f"s~ {name}"))
    p.save(os.path.join(OUT, "fb-params.pd"))


# =========================================================================
#  engines: inlet~ = frequency, outlet~ = raw tone. switch~ keeps CPU low.
# =========================================================================
def engine_shell(k, title):
    p = Patch(900, 700)
    p.text(f"FOGBANK engine {k}: {title}", 20, 5)
    inl = p.obj("inlet~", 20, 30)
    out = p.obj("outlet~", 20, 660)
    r = p.obj("r fb-engine", 700, 30)
    eq = p.obj(f"== {k}", 700, 55)
    sw = p.obj("switch~", 700, 80)
    p.c(r, eq)
    p.c(eq, sw)
    p.at(20, 60)
    p.max_y = 640
    p.col_w = 220
    return p, inl, out


def gen_engines():
    # 0 CLOUD: 5 detuned saws + sub sine
    p, F, out = engine_shell(0, "CLOUD - 5 detuned saws + sub (COLOR = sub, MOTION = breathing detune)")
    o = p.obj
    det = o("r~ fb-s-detune")
    d1 = o("*~ 0.016")
    p.c(det, d1)
    lfo = o("r~ fb-lfo")
    mot = o("r~ fb-s-motion")
    lm = o("*~")
    p.c(lfo, lm)
    p.c(mot, lm, 0, 1)
    lm2 = o("*~ 0.9")
    p.c(lm, lm2)
    lm3 = o("+~ 1")
    p.c(lm2, lm3)
    d = o("*~")
    p.c(d1, d)
    p.c(lm3, d, 0, 1)
    gain = o("*~ 0.22")
    for k in (-2, -1, 0, 1, 2):
        if k == 0:
            ph = o("phasor~")
            p.c(F, ph)
        else:
            m = o(f"*~ {k}")
            p.c(d, m)
            r1 = o("+~ 1")
            p.c(m, r1)
            fr = o("*~")
            p.c(F, fr)
            p.c(r1, fr, 0, 1)
            ph = o("phasor~")
            p.c(fr, ph)
        c = o("-~ 0.5")
        p.c(ph, c)
        p.c(c, gain)
    sub = o("*~ 0.5")
    p.c(F, sub)
    so = o("osc~")
    p.c(sub, so)
    col = o("r~ fb-s-color")
    sg = o("*~")
    p.c(so, sg)
    p.c(col, sg, 0, 1)
    sg2 = o("*~ 0.5")
    p.c(sg, sg2)
    p.c(gain, out)
    p.c(sg2, out)
    p.save(os.path.join(OUT, "fb-e0.pd"))

    # 1 GLASS: FM, COLOR = ratio, MOTION = index breathing
    p, F, out = engine_shell(1, "GLASS - FM (COLOR = mod ratio 0.5..8, MOTION = index + breathing)")
    o = p.obj
    col = o("r~ fb-s-color")
    ratio = o("expr~ 0.5+$v1*7.5")
    p.c(col, ratio)
    mf = o("*~")
    p.c(F, mf)
    p.c(ratio, mf, 0, 1)
    mod = o("osc~")
    p.c(mf, mod)
    mot = o("r~ fb-s-motion")
    lfo = o("r~ fb-lfo")
    idx = o("expr~ 0.25+$v1*2.5*(1+0.6*$v2)")
    p.c(mot, idx)
    p.c(lfo, idx, 0, 1)
    dev = o("*~")
    p.c(F, dev)
    p.c(idx, dev, 0, 1)
    dm = o("*~")
    p.c(mod, dm)
    p.c(dev, dm, 0, 1)
    cf = o("+~")
    p.c(F, cf)
    p.c(dm, cf, 0, 1)
    car = o("osc~")
    p.c(cf, car)
    g1 = o("*~ 0.42")
    p.c(car, g1)
    f2 = o("*~ 2.003")
    p.c(F, f2)
    o2 = o("osc~")
    p.c(f2, o2)
    g2 = o("*~ 0.12")
    p.c(o2, g2)
    f3 = o("*~ 0.5")
    p.c(F, f3)
    o3 = o("osc~")
    p.c(f3, o3)
    g3 = o("*~ 0.15")
    p.c(o3, g3)
    for g in (g1, g2, g3):
        p.c(g, out)
    p.save(os.path.join(OUT, "fb-e1.pd"))

    # 2 CHOIR: 10 partials shaped by a moving formant
    p, F, out = engine_shell(2, "CHOIR - 10 additive partials through a moving formant (COLOR = vowel, MOTION = vowel drift)")
    o = p.obj
    col = o("r~ fb-s-color")
    mot = o("r~ fb-s-motion")
    lfo = o("r~ fb-lfo")
    fc = o("expr~ 300+$v1*2200+$v2*$v3*700")
    p.c(col, fc)
    p.c(mot, fc, 0, 1)
    p.c(lfo, fc, 0, 2)
    gain = o("*~ 0.3")
    for k in range(1, 11):
        fk = o(f"*~ {k*(1+k*0.0004):.5f}")
        p.c(F, fk)
        ok = o("osc~")
        p.c(fk, ok)
        amp = o(f"expr~ exp(-pow(($v1*{k}-$v2)/($v2*0.3+90), 2))+0.12/{k}")
        p.c(F, amp)
        p.c(fc, amp, 0, 1)
        m = o("*~")
        p.c(ok, m)
        p.c(amp, m, 0, 1)
        p.c(m, gain)
    p.c(gain, out)
    p.save(os.path.join(OUT, "fb-e2.pd"))

    # 3 WIND: noise through pitched resonators
    p, F, out = engine_shell(3, "WIND - noise through 3 pitched resonators (COLOR = resonance, MOTION = airy breath)")
    o = p.obj
    nz = o("noise~")
    rc = o("r fb-e-color")
    q = o("expr 6+$f1*$f1*220")
    p.c(rc, q)
    lb = o("loadbang")
    p.c(lb, q)
    gq = o("expr sqrt(6+$f1*$f1*220)*3.5")
    p.c(rc, gq)
    p.c(lb, gq)
    gm = o("*~ 1")
    p.c(gq, gm, 0, 1)
    for k, w in ((1, 1.0), (2.002, 0.5), (2.997, 0.3)):
        fk = o(f"*~ {k}")
        p.c(F, fk)
        fkc = o("clip~ 20 18000")
        p.c(fk, fkc)
        v = o("vcf~ 10")
        p.c(nz, v)
        p.c(fkc, v, 0, 1)
        p.c(q, v, 0, 2)
        g = o(f"*~ {w}")
        p.c(v, g)
        p.c(g, gm)
    p.c(gm, out)
    hp = o("hip~ 2500")
    p.c(nz, hp)
    mot = o("r~ fb-s-motion")
    lfo = o("r~ fb-lfo")
    br = o("expr~ $v1*0.05*(0.6+0.4*$v2)")
    p.c(mot, br)
    p.c(lfo, br, 0, 1)
    air = o("*~")
    p.c(hp, air)
    p.c(br, air, 0, 1)
    p.c(air, out)
    p.save(os.path.join(OUT, "fb-e3.pd"))

    # 4 TAPE: 2 PWM pulses + flutter
    p, F, out = engine_shell(4, "TAPE - 2 PWM pulses + flutter, soft lowpass (COLOR = pulse width, MOTION = PWM + flutter)")
    o = p.obj
    mot = o("r~ fb-s-motion")
    fl = o("osc~ 5.3")
    fl2 = o("osc~ 0.71")
    flm = o("expr~ 1+$v3*(0.0025*$v1+0.004*$v2)")
    p.c(fl, flm)
    p.c(fl2, flm, 0, 1)
    p.c(mot, flm, 0, 2)
    Ff = o("*~")
    p.c(F, Ff)
    p.c(flm, Ff, 0, 1)
    col = o("r~ fb-s-color")
    lfo = o("r~ fb-lfo")
    pw = o("expr~ min(max(0.5-$v1*0.42+$v2*$v3*0.25, 0.04), 0.96)")
    p.c(col, pw)
    p.c(lfo, pw, 0, 1)
    p.c(mot, pw, 0, 2)
    gain = o("*~ 0.3")
    for det in (1.0, 1.0042):
        if det == 1.0:
            ph = o("phasor~")
            p.c(Ff, ph)
        else:
            m = o(f"*~ {det}")
            p.c(Ff, m)
            ph = o("phasor~")
            p.c(m, ph)
        pu = o("expr~ ($v1<$v2)*2-1")
        p.c(ph, pu)
        p.c(pw, pu, 0, 1)
        p.c(pu, gain)
    lp = o("lop~ 3000")
    p.c(gain, lp)
    lp2 = o("lop~ 5000")
    p.c(lp, lp2)
    p.c(lp2, out)
    p.save(os.path.join(OUT, "fb-e4.pd"))


# =========================================================================
def gen_voice():
    p = Patch(1300, 900)
    o = p.obj
    p.text("FOGBANK voice: glide pitch * vibrato -> engine (one of 5) -> lowpass w/ env + LFO -> ADSR -> warmth -> pan", 20, 5)
    inl = o("inlet", 20, 30)
    unp = o("unpack f f", 20, 55)
    p.c(inl, unp)
    p.c(unp, o("v fbxvel", 120, 80), 1)
    tn = o("t b f", 20, 80)
    p.c(unp, tn)
    p.c(tn, o("v fbxnote", 60, 105), 1)
    on = o("expr fbxvel>0", 20, 130)
    p.c(tn, on)
    sel = o("sel 0 1", 20, 155)
    p.c(on, sel)

    # --- signal graph
    p.at(560, 30)
    p.max_y = 860
    p.col_w = 240
    F = o("vline~")
    vib = o("r~ fb-vib")
    Fv = o("*~")
    p.c(F, Fv)
    p.c(vib, Fv, 0, 1)
    Fc = o("clip~ 10 15000")
    p.c(Fv, Fc)
    eng = o("*~ 1")
    for k in range(5):
        e = o(f"fb-e{k}")
        p.c(Fc, e)
        p.c(e, eng)
    FE = o("vline~")
    fen = o("*~ 0")
    p.c(FE, fen)
    cut = o("r~ fb-s-cut")
    lc = o("r~ fb-lfocut")
    cs = o("+~")
    p.c(cut, cs)
    p.c(fen, cs, 0, 1)
    cs2 = o("+~")
    p.c(cs, cs2)
    p.c(lc, cs2, 0, 1)
    kt = o("+~ 0")
    p.c(cs2, kt)
    mt = o("mtof~")
    p.c(kt, mt)
    # vcf~ blows up when centre > sr*q/(2*pi): clamp it there, and above that
    # point crossfade to the unfiltered engine so bright settings stay bright.
    mtc = o("clip~ 20 6000")
    p.c(mt, mtc)
    vcf = o("vcf~ 1")
    p.c(eng, vcf)
    p.c(mtc, vcf, 0, 1)
    ov = o("-~ 100")
    p.c(kt, ov)
    ov2 = o("*~ 0.0833")
    p.c(ov, ov2)
    ovc = o("clip~ 0 1")
    p.c(ov2, ovc)
    inv = o("expr~ 1-$v1")
    p.c(ovc, inv)
    lpw = o("*~")
    p.c(vcf, lpw, 1)  # lowpass outlet
    p.c(inv, lpw, 0, 1)
    dw = o("*~")
    p.c(eng, dw)
    p.c(ovc, dw, 0, 1)
    AE = o("vline~")
    amp = o("*~")
    p.c(lpw, amp)
    p.c(dw, amp)
    p.c(AE, amp, 0, 1)
    dr = o("*~ 1")
    p.c(amp, dr)
    th = o("expr~ tanh($v1*$f2)/max($f2, 1)")
    p.c(dr, th)
    gll = o("line~")
    grl = o("line~")
    gl = o("*~")
    gr = o("*~")
    p.c(th, gl)
    p.c(th, gr)
    p.c(gll, gl, 0, 1)
    p.c(grl, gr, 0, 1)
    p.c(gl, o("outlet~", 1100, 870))
    p.c(gr, o("outlet~", 1200, 870))

    # --- note on
    p.at(20, 190)
    p.max_y = 860
    p.col_w = 260
    ton = o("t b b b b b b b")
    p.c(sel, ton, 1)
    # 6: pitch with glide (+ random drift from DETUNE)
    fr = o("expr 440*pow(2, (fbxnote+fbtune-69+(random(-100, 101)/100)*fbdetune*0.06)/12); fbglide")
    p.c(ton, fr, 6)
    fpk = o("pack f f")
    p.c(fr, fpk, 0, 0)
    p.c(fr, fpk, 1, 1)
    fm = p.msg("$1 $2")
    p.c(fpk, fm)
    p.c(fm, F)
    # 5: filter settings
    p.c(ton, o("expr fbfenv"), 5)
    p.c(p.n - 1, fen, 0, 1)
    kte = o("expr (fbxnote-60)*0.5")
    p.c(ton, kte, 4)
    p.c(kte, kt, 0, 1)
    rq = o("expr fbres")
    p.c(ton, rq, 4)
    p.c(rq, vcf, 0, 2)
    srb = o("samplerate~")
    p.c(ton, srb, 5)
    p.c(srb, o("v fbsr"))
    lim = o("expr 0.85*max(fbsr, 22050)*max(fbres, 0.5)/6.2832; 69+12*log(0.85*max(fbsr, 22050)*max(fbres, 0.5)/6.2832/440)/log(2)")
    p.c(ton, lim, 4)
    p.c(lim, mtc, 0, 2)
    p.c(lim, ov, 1, 1)
    # 3: warmth
    w1 = o("expr 1+fbwarm*fbwarm*14")
    p.c(ton, w1, 3)
    p.c(w1, dr, 0, 1)
    p.c(w1, th, 0, 1)
    # 2: pan
    pan = o("expr 0.5")  # voices dead centre; width comes from the balanced M/S stage in fb-fx
    p.c(ton, pan, 2)
    tp = o("t f f")
    p.c(pan, tp)
    el = o("expr sqrt(1-$f1)*fblvl")
    er = o("expr sqrt($f1)*fblvl")
    p.c(tp, er, 1)
    p.c(tp, el, 0)
    for e, g in ((el, gll), (er, grl)):
        m = p.msg("$1 20")
        p.c(e, m)
        p.c(m, g)
    # 1/0: envelopes
    env = o("expr pow(fbxvel/127, 0.7)*0.5; max(fbatt*pow(2, fbmatt), 1); pow(fbxvel/127, 0.7)*0.5*fbsus; fbdec; fbsus")
    p.c(ton, env, 0)
    pk = o("pack f f f f f")
    for i in range(5):
        p.c(env, pk, i, i)
    p.c(pk, p.msg("$1 $2, $3 $4 $2"))
    p.c(p.n - 1, AE)
    p.c(pk, p.msg("1 $2, $5 $4 $2"))
    p.c(p.n - 1, FE)
    # --- note off
    rl = o("expr max(fbrel*pow(2, fbmrel), 5)")
    p.c(sel, rl, 0)
    mr = p.msg("0 $1")
    p.c(rl, mr)
    p.c(mr, AE)
    p.c(mr, FE)
    p.save(os.path.join(OUT, "fb-voice.pd"))


# =========================================================================
def gen_clock():
    p = Patch(1000, 700)
    o = p.obj
    p.text("FOGBANK arp clock: internal metro (while ARP is on) or the DAW transport (SYNC + playing)", 20, 5)
    p.at(20, 40)
    trig = []
    for name in ("bpm", "arate"):
        r = o(f"r fb-{name}")
        t = o("t b f")
        p.c(r, t)
        p.c(t, o(f"v fb{name}"), 1)
        trig.append(t)
    lb = o("loadbang")
    sm = o(f"expr 60000/(max(fbbpm, 20)*{SPQ})")
    for t in trig + [lb]:
        p.c(t, sm)
    p.c(sm, o("v fbstepms"))
    p.at(280, 40)
    st_in = []
    for name in ("arp", "sync"):
        r = o(f"r fb-{name}")
        t = o("t b f")
        p.c(r, t)
        p.c(t, o(f"v fb{name}"), 1)
        st_in.append(t)
    rph = o("r playhead")
    route = o("route playing bpm position")
    p.c(rph, route)
    chp = o("change")
    p.c(route, chp)
    thp = o("t b f")
    p.c(chp, thp)
    p.c(thp, o("v fbhostplay"), 1)
    st = o("expr if(fbarp && !(fbsync && fbhostplay), 1, 0)")
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
    hbe = o("expr if(fbsync, $f1, -1)")
    p.c(hb, hbe)
    hbm = o("moses 1")
    p.c(hbe, hbm)
    hbr = o("expr int($f1*10+0.5)/10")
    p.c(hbm, hbr, 1)
    p.c(hbr, o("s fb-bpm-set"))
    up = o("unpack f f f")
    p.c(route, up, 2)
    hs = o(f"expr if(fbsync && fbhostplay, floor($f1*{SPQ}+0.0001), -1)")
    p.c(up, hs)
    hsm = o("moses 0")
    p.c(hs, hsm)
    hsc = o("change")
    p.c(hsm, hsc, 1)
    p.c(hsc, outl)
    p.save(os.path.join(OUT, "fb-clock.pd"))


# =========================================================================
def gen_brain():
    p = Patch(1500, 1000)
    o = p.obj
    p.text("FOGBANK brain: MIDI -> HOLD (latch) -> direct notes or ARP. outlet goes to [poly].", 20, 5)
    tick = o("inlet", 20, 20)
    mid = o("inlet", 700, 20)
    outl = o("outlet", 700, 960)
    for arr in ("fbheld", "fbphys", "fbsorted"):
        o(f"array define {arr} 128", 1300, 20 + 25 * ("fbheld", "fbphys", "fbsorted").index(arr))

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
    p.c(p.n - 1, o("v fbarpcur"))
    rs_ok = o("expr fbarp==0")
    p.c(resend, rs_ok, 0)
    rs_sel = o("sel 1")
    p.c(rs_ok, rs_sel)
    rs_n = o("expr fbcount")
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
    rs_note = o("expr fbsorted[$f1]; max(fblastvel, 60)")
    p.c(rs_i, rs_note)
    rs_pk = o("pack f f")
    p.c(rs_note, rs_pk, 0, 0)
    p.c(rs_note, rs_pk, 1, 1)
    p.c(rs_pk, outl)

    held_scan = scan("fbheld", "fbsorted", "fbcount")
    phys_scan = scan("fbphys", None, "fbphyscount")

    # ---- MIDI in
    p.at(400, 60)
    tm = o("t b b b b b l")
    p.c(mid, tm)
    un = o("unpack f f")
    p.c(tm, un, 5)
    p.c(un, o("v fbmv"), 1)
    p.c(un, o("v fbmn"), 0)
    # (b) new chord while HOLD -> forget the old one
    nc = o("expr fbmv>0 && fbhold && fbphyscount==0")
    p.c(tm, nc, 4)
    ncs = o("sel 1")
    p.c(nc, ncs)
    nct = o("t b b")
    p.c(ncs, nct)
    clr = p.msg("const 0")
    p.c(nct, clr, 1)
    p.c(clr, o("s fbheld"))
    ncr = o("expr fbarp==0")
    p.c(nct, ncr, 0)
    ncr2 = o("sel 1")
    p.c(ncr, ncr2)
    p.c(ncr2, stop)
    # (c) physical keys
    tabset("fbphys", "fbmn", "fbmv", tm, 3)
    # (d) held set
    hd = o("expr fbmv>0 || fbhold==0")
    p.c(tm, hd, 2)
    hds = o("sel 1")
    p.c(hd, hds)
    tabset("fbheld", "fbmn", "fbmv", hds)
    lv = o("expr if(fbmv>0, fbmv, fblastvel)")
    p.c(hds, lv)
    p.c(lv, o("v fblastvel"))
    # (e) direct play when ARP is off
    dp = o("expr fbarp==0 && (fbmv>0 || fbhold==0)")
    p.c(tm, dp, 1)
    dps = o("sel 1")
    p.c(dp, dps)
    dpe = o("expr fbmn; fbmv")
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
    ra = o("r fb-arp")
    ta = o("t b f")
    p.c(ra, ta)
    p.c(ta, o("v fbarp"), 1)
    p.c(ta, resend, 0)
    rh = o("r fb-hold")
    th = o("t b f")
    p.c(rh, th)
    p.c(th, o("v fbhold"), 1)
    hoff = o("expr fbhold==0")
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
    cpe = o("expr fbphys[$f1]")
    p.c(cpv, cpe, 1)
    cpw = o("tabwrite fbheld")
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
    run = o("r fb-unstick")
    pan = o("t b b b")
    p.c(cc, pan)
    p.c(run, pan)
    c0 = p.msg("const 0")
    p.c(pan, c0, 2)
    p.c(c0, o("s fbheld"))
    p.c(c0, o("s fbphys"))
    p.c(pan, held_scan, 1)
    p.c(pan, resend, 0)
    # sustain pedal -> HOLD
    cc64 = o("ctlin 64")
    ped = o("expr $f1>63")
    p.c(cc64, ped)
    pc = o("change")
    p.c(ped, pc)
    p.c(pc, o("s fb-hold-set"))

    # ---- ARP ticks
    p.at(1100, 60)
    go = o("expr fbarp && fbcount>0")
    p.c(tick, go)
    gs = o("sel 1")
    p.c(go, gs)
    t3 = o("t b b b")
    p.c(gs, t3)
    # off routine (shared with the gate delay)
    off = o("expr fbarpcur")
    p.c(t3, off, 2)
    offm = o("moses 0")
    p.c(off, offm)
    offt = o("t f b")
    p.c(offm, offt, 1)
    m1 = p.msg("-1")
    p.c(offt, m1, 1)
    p.c(m1, o("v fbarpcur"))
    offp = o("pack f 0")
    p.c(offt, offp, 0)
    p.c(offp, outl)
    # next note
    apos = o("f")
    ainc = o("+ 1")
    p.c(t3, apos, 1)
    p.c(apos, ainc)
    p.c(ainc, apos, 0, 1)
    N = "(fbcount*fbaoct)"
    P = f"max(2*{N}-2, 1)"
    ak = o(f"expr if(fbarpm==0, $f1%{N}, if(fbarpm==1, {N}-1-$f1%{N}, if(fbarpm==2, if($f1%{P}<{N}, $f1%{P}, 2*{N}-2-$f1%{P}), if(fbarpm==3, random(0, {N}), min(max(fbprevk+random(-1, 2), 0), {N}-1)))))")
    p.c(apos, ak)
    tk = o("t f f")
    p.c(ak, tk)
    p.c(tk, o("v fbprevk"), 1)
    an = o("expr min(fbsorted[$f1%fbcount]+12*int($f1/fbcount), 127)")
    p.c(tk, an, 0)
    p.c(an, o("v fbarpnext"))
    # play it
    pl = o("t b b b")
    p.c(t3, pl, 0)
    gd = o("expr max(fbagate*fbstepms, 10)")
    p.c(pl, gd, 2)
    dl = o("delay")
    p.c(gd, dl, 0, 1)
    nv = o("expr fbarpnext; max(fblastvel, 60)")
    p.c(pl, nv, 1)
    npk = o("pack f f")
    p.c(nv, npk, 0, 0)
    p.c(nv, npk, 1, 1)
    ntt = o("t l l")
    p.c(npk, ntt)
    p.c(ntt, outl, 0)
    cur = o("unpack f f")
    p.c(ntt, cur, 1)
    p.c(cur, o("v fbarpcur"))
    p.c(pl, dl, 0)
    p.c(dl, off)
    p.c(pl, o("s fb-arpflash"), 0)
    p.save(os.path.join(OUT, "fb-brain.pd"))


# =========================================================================
def gen_fx():
    p = Patch(1300, 900)
    o = p.obj
    p.text("FOGBANK fx: stereo chorus -> ping-pong echo (16ths) -> big schroeder reverb", 20, 5)
    il = o("inlet~", 300, 10)
    ir = o("inlet~", 400, 10)
    p.at(20, 40)
    lb = o("loadbang")
    met = o("metro 40")
    p.c(lb, met)
    lines = {}
    for key, ex, ms in (("chorus", "fbchorus", 60),
                        ("dtime", "min(max(fbdsync*15000/max(fbbpm, 20), 10), 2900)", 120),
                        ("dfb", "fbdfb", 50), ("dmix", "fbdmix", 50),
                        ("rfb", "0.7+fbrsize*0.27", 80),
                        ("rmix", "min(fbrmix+fbmspace, 1)", 50),
                        ("width", "0.5+fbspread*1.5", 60)):
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
        fb = o("*~")
        p.c(hp, fb)
        p.c(lines["dfb"], fb, 0, 1)
        p.c(fb, dst)
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
    p.save(os.path.join(OUT, "fb-fx.pd"))


# =========================================================================
def gen_bank():
    p = Patch(1000, 700)
    o = p.obj
    p.text("FOGBANK banks: banks.txt line = Name description lvl x key value ...", 20, 5)
    p.at(20, 40)
    tb = o("text define fbbanks")
    lb = o("loadbang")
    t = o("t b b")
    p.c(lb, t)
    rd = p.msg("read banks.txt")
    p.c(t, rd, 1)
    p.c(rd, tb)
    p.c(t, p.msg("; fb-bank-set 0"), 0)
    p.at(300, 40)
    rb = o("r fb-bank")
    cl = o(f"clip 0 {len(BANKS)-1}")
    p.c(rb, cl)
    tl = o("t f f")
    p.c(cl, tl)
    p.c(tl, o("v fbbank"), 1)
    get = o("text get fbbanks")
    p.c(tl, get, 0)
    sp = o("list split 2")
    p.c(get, sp)
    nm = o("unpack s s")
    p.c(sp, nm)
    p.c(nm, p.msg("; fb-name-lbl label $1"), 0)
    p.c(nm, p.msg("; fb-desc-lbl label $1"), 1)
    d = o("list split 2")
    back = o("list")
    p.c(sp, d, 1)
    p.c(d, back, 1)
    p.c(back, d)
    p.c(d, p.msg("; fb-$1-set $2"))
    p.at(600, 40)
    n = len(BANKS)
    for rcv, ex in (("fb-prev", f"(fbbank-1+{n})%{n}"), ("fb-next", f"(fbbank+1)%{n}"),
                    ("fb-rand", f"random(0, {n})")):
        r = o(f"r {rcv}")
        e = o(f"expr {ex}")
        p.c(r, e)
        p.c(e, o("s fb-bank-set"))
    p.save(os.path.join(OUT, "fb-bank.pd"))


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
        ne = o(f"expr $f1 != fb{name}")
        p.c(tf, ne, 1)
        sp = o("spigot")
        p.c(ne, sp, 0, 1)
        p.c(tf, sp, 0)
        p.c(sp, o(f"s fb-{name}-set"))
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
        v = o(f"v fb{n}")
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
    p.c(sp, p.msg("; fb-$1-set $2"))
    p.save(os.path.join(OUT, "fb-host.pd"))


# =========================================================================
PAL = dict(bg="#0b132b", panel="#1c2541", panel2="#25305a", text="#e9ecf5", cyan="#9be7ff",
           peach="#ffb4a2", lav="#cdb4db", mint="#b9fbc0", dim="#8892b0", yellow="#ffe66d")


def gen_main():
    p = Patch(1500, 900, 10)
    W, H = 780, 470
    P = PAL
    cnv, lab = p.cnv, p.label
    cnv(0, 0, W, H, P["bg"])
    cnv(0, 0, W, 54, "#070d1f", "FOGBANK", 10, 20, 26, P["cyan"])
    lab(12, 44, "ambient_pad_machine_//_5_engines_//_38_banks", 9, P["lav"], "#070d1f")
    p.bng(250, 12, 18, "fb-prev", "empty", "<", P["bg"], P["cyan"], P["bg"], 6, 9, 11)
    p.nbx(272, 12, 3, 18, 0, len(BANKS) - 1, "fb-bank", "fb-bank-set", "BANK", "#000000",
          P["cyan"], P["cyan"], 0, -6, 9)
    p.bng(318, 12, 18, "fb-next", "empty", ">", P["bg"], P["cyan"], P["bg"], 6, 9, 11)
    p.bng(340, 12, 18, "fb-rand", "empty", "?", P["bg"], P["peach"], P["bg"], 6, 9, 11)
    lab(372, 20, "...", 16, P["text"], "#070d1f", "fb-name-lbl")
    lab(372, 41, "...", 9, P["peach"], "#070d1f", "fb-engname-big")
    cnv(0, 54, W, 20, P["panel2"])
    lab(10, 64, "...", 10, P["mint"], P["panel2"], "fb-desc-lbl")

    def panel(x, y, w, h, title, col):
        cnv(x, y, w, h, P["panel"], title, 6, 9, 10, col)

    def sliders(x, y0, items, col, step=24, w=120):
        for k, it in enumerate(items):
            name, label, lo, hi, lg = it[:5]
            p.hsl(x, y0 + k * step, w, 13, lo, hi, f"fb-{name}", f"fb-{name}-set", label, lg,
                  col, "#0f1730", P["text"])

    panel(4, 78, 254, 172, "ENGINE", P["peach"])
    p.hradio(10, 96, 18, 5, "fb-engine", "fb-engine-set", "empty", P["peach"], "#0f1730", P["text"])
    lab(104, 105, "CLOUD", 11, P["peach"], P["panel"], "fb-engname")
    sliders(10, 124, ENG_P, P["peach"])
    panel(262, 78, 254, 172, "FILTER_+_LFO", P["cyan"])
    sliders(268, 96, FIL_P, P["cyan"])
    panel(520, 78, 256, 172, "AMP", P["lav"])
    sliders(526, 96, AMP_P, P["lav"])

    panel(4, 254, 254, 212, "SPACE", P["mint"])
    sliders(10, 272, FX_P, P["mint"], 27)
    panel(262, 254, 254, 212, "ARPEGGIATOR", P["yellow"])
    p.tgl(268, 272, 22, "fb-arp", "fb-arp-set", "ARP_ON", P["yellow"], "#0f1730", P["text"], 26, 11, 10)
    p.tgl(350, 272, 22, "fb-hold", "fb-hold-set", "HOLD", P["yellow"], "#0f1730", P["text"], 26, 11, 10)
    p.tgl(420, 272, 22, "fb-sync", "fb-sync-set", "DAW-SYNC", P["yellow"], "#0f1730", P["text"], 26, 11, 10)
    p.bng(494, 276, 14, "empty", "fb-arpflash", "empty", P["yellow"], "#0f1730", P["text"])
    lab(268, 312, "MODE", 9, P["text"], P["panel"])
    p.hradio(304, 305, 15, 5, "fb-arpm", "fb-arpm-set", "empty", P["yellow"], "#0f1730", P["text"])
    lab(386, 312, "UP", 10, P["yellow"], P["panel"], "fb-arpmname")
    lab(268, 336, "RATE", 9, P["text"], P["panel"])
    p.hradio(304, 329, 15, 6, "fb-arate", "fb-arate-set", "empty", P["yellow"], "#0f1730", P["text"])
    lab(400, 336, "1/8", 10, P["yellow"], P["panel"], "fb-aratename")
    lab(268, 360, "OCT", 9, P["text"], P["panel"])
    p.hradio(304, 353, 15, 4, "fb-aoct", "fb-aoct-set", "empty", P["yellow"], "#0f1730", P["text"])
    p.hsl(268, 380, 120, 13, 0.05, 1, "fb-agate", "fb-agate-set", "GATE", 0, P["yellow"], "#0f1730", P["text"])
    p.nbx(268, 404, 4, 16, 20, 300, "fb-bpm", "fb-bpm-set", "BPM", "#000000", P["yellow"], P["text"])
    p.bng(350, 404, 16, "fb-unstick", "empty", "ALL-NOTES-OFF", P["bg"], P["peach"], P["text"], 20, 8, 9)
    lab(268, 436, "ARP_ON:_hold_keys_->_arpeggio", 9, P["dim"], P["panel"])
    lab(268, 452, "HOLD:_chords_ring_until_the_next_one", 9, P["dim"], P["panel"])
    panel(520, 254, 256, 212, "BIG_KNOBS_(DAW)", P["peach"])
    sliders(526, 272, MACROS, P["peach"], 24)
    lab(526, 426, "these_ride_on_top_of_the_bank", 9, P["dim"], P["panel"])
    lab(526, 442, "-_automate_them_in_your_DAW", 9, P["dim"], P["panel"])
    p.gop(W, H)

    # ---------------- engine wiring
    o = p.obj
    X = 820
    p.text("FOGBANK - the plugin face is left of here. engine below.", X, 10)
    o("fb-params", X, 40)
    o("fb-bank", X, 64)
    o("fb-host", X, 88)
    clock = o("fb-clock", X, 130)
    brain = o("fb-brain", X, 180)
    p.c(clock, brain)
    ni = o("notein", X + 160, 120)
    npk = o("pack f f", X + 160, 145)
    p.c(ni, npk, 0, 0)
    p.c(ni, npk, 1, 1)
    p.c(npk, brain, 0, 1)
    rn = o("r fb-note", X + 260, 145)
    p.c(rn, brain, 0, 1)
    poly = o(f"poly {NVOICES} 1", X, 220)
    p.c(brain, poly)
    pk = o("pack f f f", X, 250)
    p.c(poly, pk, 0, 0)
    p.c(poly, pk, 1, 1)
    p.c(poly, pk, 2, 2)
    cl = o(f"clone -s 1 fb-voice {NVOICES}", X, 280)
    p.c(pk, cl)
    fx = o("fb-fx", X, 310)
    p.c(cl, fx, 0, 0)
    p.c(cl, fx, 1, 1)
    rv = o("r fb-vol", X + 200, 310)
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
    p.c(c1, o("s~ fb-master-l", X + 100, 465))
    p.c(c2, o("s~ fb-master-r", X + 220, 465))

    def namer(rcv, dests, names, y):
        r = o(f"r {rcv}", X + 400, y)
        s = o("sel " + " ".join(str(i) for i in range(len(names))), X + 400, y + 25)
        p.c(r, s)
        for i, nm in enumerate(names):
            txt = "; " + "; ".join(f"{d} label {nm}" for d in dests)
            m = p.msg(txt, X + 400 + i * 150, y + 50)
            p.c(s, m, i)

    namer("fb-engine", ["fb-engname", "fb-engname-big"], ENGINES, 40)
    namer("fb-arpm", ["fb-arpmname"], ARP_MODES, 140)
    namer("fb-arate", ["fb-aratename"], ARP_RATES, 240)

    lb = o("loadbang", X, 520)
    init = ("; fb-bpm-set 100; fb-arp-set 0; fb-hold-set 0; fb-arpm-set 0; fb-arate-set 1; "
            "fb-aoct-set 0; fb-agate-set 0.6; fb-sync-set 1; fb-vol-set 0.8; "
            "fb-mbright-set 0; fb-mcolor-set 0; fb-mmotion-set 0; fb-matt-set 0; "
            "fb-mrel-set 0; fb-mspace-set 0")
    p.c(lb, p.msg(init, X, 545))
    p.save(os.path.join(OUT, "Fogbank.pd"))


def gen_txt():
    lines = ["type instrument;", "code FgBk;", "midiin true;", "midiout false;",
             "playhead true;", "bus 0 2;", "taillength 15;", "compatibility v1.0.7;"]
    lines += [h[1] for h in HOSTP]
    with open(os.path.join(OUT, "Fogbank.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    gen_params()
    gen_engines()
    gen_voice()
    gen_clock()
    gen_brain()
    gen_fx()
    gen_bank()
    gen_host()
    gen_main()
    gen_txt()
    lv = os.path.join(ROOT, "tools", "fogbank_levels.json")
    write_banks(json.load(open(lv)) if os.path.exists(lv) else {})
    print("wrote", OUT)


if __name__ == "__main__":
    main()
